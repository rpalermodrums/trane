"""Module for asynchronous DSP tasks."""
from celery import shared_task
import librosa
import numpy as np
import os
import time
import logging
import json
from redis import Redis
from celery.utils.log import get_task_logger
from typing import Dict, Any, Optional, List
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ObjectDoesNotExist

from .feature_extraction import FeatureExtractor, AudioFeatures, MIDIFeatures
from .models import ProcessingTask, ProcessingResult, PerformanceMetrics
from .performance import PerformanceMonitor

logger = get_task_logger(__name__)

# Initialize performance monitor
performance_monitor = PerformanceMonitor()

def default_converter(o):
    """Convert numpy arrays to lists for JSON serialization."""
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

# Configure Redis connection with retry logic
def get_redis_client(max_retries=5, retry_delay=1):
    for attempt in range(max_retries):
        try:
            client = Redis(host='redis', port=6379, db=0)
            client.ping()
            logger.info(f"Redis connection status: {client.ping()}")
            return client
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to connect to Redis after {max_retries} attempts: {e}")
                raise
            logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
            time.sleep(retry_delay)

# Initialize Redis client
try:
    redis_client = get_redis_client()
    CACHE_EXPIRY = 3600  # Cache results for 1 hour
except Exception as e:
    logger.error(f"Failed to initialize Redis client: {e}")
    redis_client = None

# Initialize feature extractor
feature_extractor = FeatureExtractor()

@shared_task(bind=True, queue='audio', autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_audio_file(self, audio_path: str, chunk_size: Optional[int] = None) -> Dict[str, Any]:
    """
    Process audio file asynchronously with optional chunking.
    If a ProcessingTask record exists (from the view), reuse it.
    """
    logger.info(f"Task {self.request.id} received for file: {audio_path}")
    task_obj, created = ProcessingTask.objects.get_or_create(
        task_id=self.request.id,
        defaults={
            'task_type': 'audio',
            'status': 'pending'
        }
    )
    # Log whether we created a new record or reused an existing one
    if created:
        logger.info(f"Created new ProcessingTask: {task_obj.task_id}")
    else:
        logger.info(f"Found existing ProcessingTask: {task_obj.task_id}")
    
    logger.info(f"Starting audio processing for {audio_path}")
    start_time = time.time()
    
    try:
        # Verify file exists
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        cache_key = f"audio_features:{audio_path}"

        # Try to get from cache if Redis is available
        if redis_client:
            try:
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for {audio_path}")
                    return eval(cached_result)
            except Exception as e:
                logger.warning(f"Cache retrieval failed: {e}")

        # Process the audio
        try:
            if chunk_size:
                logger.info(f"Processing {audio_path} in chunks of size {chunk_size}")
                features = process_audio_chunks(audio_path, chunk_size)
            else:
                logger.info(f"Processing {audio_path} as complete file")
                features = process_complete_audio(audio_path)

            # Add processing metadata
            features['processing_time'] = time.time() - start_time
            features['processed_at'] = time.time()

            # Convert features to JSON-serializable format
            features_serializable = json.loads(json.dumps(features, default=default_converter))

            # Cache the results if Redis is available
            if redis_client:
                try:
                    redis_client.setex(cache_key, CACHE_EXPIRY, str(features_serializable))
                    logger.info(f"Cached results for {audio_path}")
                except Exception as e:
                    logger.warning(f"Failed to cache results: {e}")

            logger.info(f"Successfully processed {audio_path}")

            # Store results
            ProcessingResult.objects.create(
                task=task_obj,
                features=features_serializable,
                source_file=audio_path,
                processing_time=time.time() - start_time,
                metadata={
                    'chunk_size': chunk_size,
                    'sample_rate': 22050,
                    'file_size': os.path.getsize(audio_path)
                }
            )

            return features_serializable

        except Exception as e:
            logger.error(f"Processing failed for {audio_path}: {e}")
            raise

    except Exception as e:
        logger.error(f"Task failed for {audio_path}: {e}")
        task_obj.status = 'failed'
        task_obj.error_message = str(e)
        task_obj.save()

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task for {audio_path}")
            raise self.retry(exc=e, countdown=2 ** self.request.retries)
        raise

def process_complete_audio(audio_path: str) -> Dict[str, Any]:
    """Process the entire audio file at once."""
    # Load audio file
    y, sr = librosa.load(audio_path, sr=22050)
    
    # Extract features
    features = feature_extractor.extract_audio_features(y, time.time())
    
    # Convert to dictionary format
    return {
        'pitch_mean': features.pitch_mean,
        'pitch_std': features.pitch_std,
        'pitch_confidence': features.pitch_confidence,
        'tempo': features.tempo,
        'beat_positions': features.beat_positions,
        'onset_positions': features.onset_positions,
        'spectral_features': {
            'centroid': features.spectral_centroid_mean,
            'bandwidth': features.spectral_bandwidth_mean,
            'rolloff': features.spectral_rolloff_mean
        },
        'dynamics': {
            'rms_energy': features.rms_energy,
            'zero_crossing_rate': features.zero_crossing_rate
        },
        'timbre': {
            'mfcc': features.mfcc.tolist() if features.mfcc is not None else None,
            'chroma': features.chroma.tolist() if features.chroma is not None else None
        },
        'is_speech': features.is_speech,
        'processing_type': 'complete'
    }

def process_audio_chunks(audio_path: str, chunk_size: int) -> Dict[str, Any]:
    """Process audio file in chunks."""
    features = {
        'chunks': [],
        'processing_type': 'chunked'
    }
    
    # Aggregate features across chunks
    all_pitches = []
    all_pitch_confidences = []
    all_onsets = []
    all_beats = []
    all_rms = []
    
    # Stream the audio in chunks
    for i, y_chunk in enumerate(librosa.stream(
        audio_path,
        block_length=chunk_size,
        frame_length=2048,
        hop_length=512
    )):
        # Extract features for this chunk
        chunk_features = feature_extractor.extract_audio_features(y_chunk, time.time())
        
        # Collect features for aggregation
        if chunk_features.pitch_mean is not None:
            all_pitches.append(chunk_features.pitch_mean)
            all_pitch_confidences.append(chunk_features.pitch_confidence)
        if chunk_features.onset_positions:
            all_onsets.extend(chunk_features.onset_positions)
        if chunk_features.beat_positions:
            all_beats.extend(chunk_features.beat_positions)
        if chunk_features.rms_energy is not None:
            all_rms.append(chunk_features.rms_energy)
        
        # Store chunk-specific features
        features['chunks'].append({
            'chunk_index': i,
            'pitch': chunk_features.pitch_mean,
            'pitch_mean': chunk_features.pitch_mean,
            'pitch_std': chunk_features.pitch_std,
            'pitch_confidence': chunk_features.pitch_confidence,
            'tempo': chunk_features.tempo,
            'beat_positions': chunk_features.beat_positions,
            'onset_positions': chunk_features.onset_positions,
            'rms_energy': chunk_features.rms_energy,
            'is_speech': chunk_features.is_speech,
            'duration': len(y_chunk) / 22050  # assuming sr=22050
        })
    
    # Safely aggregate features
    def safe_mean(arr):
        """Calculate mean safely for empty arrays."""
        if not arr:
            return None
        return float(np.mean(arr))
    
    # Aggregate features with safe calculations
    features.update({
        'average_pitch': safe_mean(all_pitches),
        'pitch_confidence': safe_mean(all_pitch_confidences),
        'onset_positions': sorted(all_onsets) if all_onsets else [],
        'beat_positions': sorted(all_beats) if all_beats else [],
        'average_rms': safe_mean(all_rms),
        'total_duration': sum(chunk['duration'] for chunk in features['chunks'])
    })
    
    return features

@shared_task(bind=True)
def process_midi_events(self, events: List[Dict[str, Any]], timestamp: float) -> Dict[str, Any]:
    """Process a batch of MIDI events."""
    # Create task record
    task = ProcessingTask.objects.create(
        task_id=self.request.id,
        task_type='midi',
        status='pending'
    )

    start_time = time.time()

    try:
        # Extract active notes and velocities
        active_notes = []
        active_velocities = []
        
        for event in events:
            if event.get('event_type') == 'note_on' and event.get('velocity', 0) > 0:
                active_notes.append(event.get('note'))
                active_velocities.append(event.get('velocity'))
            elif event.get('event_type') == 'note_off' or (
                event.get('event_type') == 'note_on' and event.get('velocity', 0) == 0
            ):
                try:
                    idx = active_notes.index(event.get('note'))
                    active_notes.pop(idx)
                    active_velocities.pop(idx)
                except ValueError:
                    pass
        
        # Extract MIDI features
        features = feature_extractor.extract_midi_features(
            active_notes=active_notes,
            active_velocities=active_velocities,
            recent_events=events,
            timestamp=timestamp
        )
        
        # Convert to dictionary format and ensure JSON serializable
        features_dict = {
            'active_notes': features.active_notes,
            'note_density': features.note_density,
            'average_velocity': features.average_velocity,
            'pitch_range': {
                'min': features.pitch_range[0],
                'max': features.pitch_range[1]
            },
            'recent_onsets': features.recent_onsets,
            'chord_estimate': features.chord_estimate,
            'timestamp': features.timestamp
        }
        
        features_serializable = json.loads(json.dumps(features_dict, default=default_converter))
        return features_serializable
        
    except Exception as e:
        logger.error(f"Error processing MIDI events: {e}")
        task.status = 'failed'
        task.error_message = str(e)
        task.save()

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=2 ** self.request.retries)
        raise

@shared_task
def cleanup_old_results():
    """Clean up old processing results and metrics."""
    try:
        # Delete old completed tasks and their results
        cutoff_date = timezone.now() - timedelta(days=7)
        old_tasks = ProcessingTask.objects.filter(
            created_at__lt=cutoff_date,
            status='completed'
        )
        deleted_count = old_tasks.count()
        old_tasks.delete()

        # Delete old performance metrics
        metrics_cutoff = timezone.now() - timedelta(days=1)
        old_metrics = PerformanceMetrics.objects.filter(
            timestamp__lt=metrics_cutoff
        )
        metrics_count = old_metrics.count()
        old_metrics.delete()

        logger.info(f"Cleaned up {deleted_count} old tasks and {metrics_count} metrics")

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise

@shared_task
def log_performance_metrics():
    """Log current performance metrics."""
    try:
        metrics = performance_monitor.get_current_metrics()

        PerformanceMetrics.objects.create(
            cpu_usage=metrics.cpu_usage,
            memory_usage=metrics.memory_usage,
            processing_time=metrics.processing_time,
            queue_length=metrics.queue_length,
            gpu_memory_used=metrics.gpu_memory_used,
            gpu_utilization=metrics.gpu_utilization
        )

        logger.info("Performance metrics logged successfully")

    except Exception as e:
        logger.error(f"Error logging performance metrics: {e}")
        raise

@shared_task
def test_task():
    logger.info("=== TEST TASK EXECUTED SUCCESSFULLY ===")
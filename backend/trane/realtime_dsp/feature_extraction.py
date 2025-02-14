"""Module for extracting musical features from audio and MIDI data."""
import os
# Configure Numba to disable caching when running as non-root
os.environ['NUMBA_CACHE_DIR'] = '/tmp/numba_cache'
# os.environ['NUMBA_DISABLE_JIT'] = '1'  # Disable JIT compilation for now

import numpy as np
import librosa
import torch
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading
import time

from .interfaces import (
    FeatureExtractorBase,
    ProcessingContext,
    FeatureSet,
    AudioProcessorInterface,
    MIDIProcessorInterface,
    ProcessingError
)
from .performance import (
    PerformanceMonitor,
    ResourceManager,
    OptimizedThreadPool,
    PerformanceMetrics
)

logger = logging.getLogger(__name__)

@dataclass
class AudioFeatures(FeatureSet):
    """Container for extracted audio features."""
    timestamp: float
    # Remove the standalone 'pitch' field
    pitch_mean: float
    pitch_std: float
    pitch_confidence: float
    pitch_yin_mean: float
    pitch_range: float
    spectral_centroid_mean: float
    spectral_centroid_std: float
    spectral_bandwidth_mean: float
    spectral_contrast_mean: float
    spectral_flatness_mean: float
    spectral_rolloff_mean: float
    spectral_variance: float
    tempo: float
    beat_positions: List[float]
    onset_positions: List[float]
    rms_energy: Optional[float] = None
    zero_crossing_rate: Optional[float] = None
    mfcc: Optional[np.ndarray] = None
    chroma: Optional[np.ndarray] = None
    is_speech: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert features to dictionary format."""
        return {
            'timestamp': self.timestamp,
            'pitch_mean': self.pitch_mean,
            'pitch_std': self.pitch_std,
            'pitch_confidence': self.pitch_confidence,
            'pitch_yin_mean': self.pitch_yin_mean,
            'pitch_range': self.pitch_range,
            'tempo': self.tempo,
            'beat_positions': self.beat_positions,
            'onset_positions': self.onset_positions,
            'spectral_features': {
                'centroid_mean': self.spectral_centroid_mean,
                'centroid_std': self.spectral_centroid_std,
                'bandwidth_mean': self.spectral_bandwidth_mean,
                'contrast_mean': self.spectral_contrast_mean,
                'flatness_mean': self.spectral_flatness_mean,
                'rolloff_mean': self.spectral_rolloff_mean,
                'variance': self.spectral_variance
            },
            'dynamics': {
                'rms_energy': self.rms_energy,
                'zero_crossing_rate': self.zero_crossing_rate
            },
            'timbre': {
                'mfcc': self.mfcc.tolist() if self.mfcc is not None else None,
                'chroma': self.chroma.tolist() if self.chroma is not None else None
            },
            'is_speech': self.is_speech,
        }
    
    def merge(self, other: 'AudioFeatures') -> 'AudioFeatures':
        """Merge with another AudioFeatures object."""
        # Take the most recent features
        if other.timestamp > self.timestamp:
            return other
        return self
    
    def get_timestamp(self) -> float:
        """Get the timestamp of this feature set."""
        return self.timestamp

@dataclass
class MIDIFeatures(FeatureSet):
    """Container for extracted MIDI features."""
    timestamp: float
    active_notes: List[int]
    active_velocities: List[int]
    note_density: float  # Notes per second
    average_velocity: float
    pitch_range: Tuple[int, int]  # (min, max)
    recent_onsets: List[float]  # Timestamps of recent note onsets
    chord_estimate: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert features to dictionary format."""
        return {
            'timestamp': self.timestamp,
            'active_notes': self.active_notes,
            'note_density': self.note_density,
            'average_velocity': self.average_velocity,
            'pitch_range': {
                'min': self.pitch_range[0],
                'max': self.pitch_range[1]
            },
            'recent_onsets': self.recent_onsets,
            'chord_estimate': self.chord_estimate
        }
    
    def merge(self, other: 'MIDIFeatures') -> 'MIDIFeatures':
        """Merge with another MIDIFeatures object."""
        # Take the most recent features
        if other.timestamp > self.timestamp:
            return other
        return self
    
    def get_timestamp(self) -> float:
        """Get the timestamp of this feature set."""
        return self.timestamp

class FeatureExtractor(FeatureExtractorBase, AudioProcessorInterface, MIDIProcessorInterface):
    """Extract musical features from audio and MIDI data."""
    def __init__(self, 
                 sample_rate: int = 22050,
                 hop_length: int = 512,
                 n_mels: int = 128,
                 n_mfcc: int = 13,
                 use_torch: bool = True,
                 enable_performance_monitoring: bool = True):
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.n_mels = n_mels
        self.n_mfcc = n_mfcc
        
        # Performance monitoring and optimization
        if enable_performance_monitoring:
            self.performance_monitor = PerformanceMonitor()
            self.resource_manager = ResourceManager(
                monitor=self.performance_monitor,
                target_cpu_usage=80.0,
                target_memory_usage=80.0,
                target_gpu_memory=80.0
            )
            self.thread_pool = OptimizedThreadPool(
                resource_manager=self.resource_manager,
                initial_workers=4
            )
            self.performance_monitor.start_monitoring()
        else:
            self.performance_monitor = None
            self.resource_manager = None
            self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # GPU setup
        self.use_torch = use_torch
        if self.use_torch and torch.cuda.is_available():
            logger.info("Using GPU acceleration for feature extraction")
            self.device = torch.device('cuda')
            # Pre-allocate GPU tensors for common operations
            self.setup_gpu_resources()
        else:
            logger.info("Using CPU for feature extraction")
            self.device = torch.device('cpu')
        
        # Feature extraction optimization
        self.batch_size = 1024
        self._cached_stft_window = None
        self._cached_mel_basis = None
        self._setup_caches()
    
    def setup_gpu_resources(self):
        """Pre-allocate GPU resources for common operations."""
        if self.use_torch and self.device.type == 'cuda':
            # Pre-allocate common tensors
            self._window = torch.hann_window(self.hop_length * 4).to(self.device)
            self._mel_basis = torch.from_numpy(
                librosa.filters.mel(
                    sr=self.sample_rate,
                    n_fft=self.hop_length * 4,
                    n_mels=self.n_mels
                )
            ).to(self.device).float()
    
    def _setup_caches(self):
        """Setup cached resources for CPU processing."""
        self._cached_stft_window = np.hanning(self.hop_length * 4)
        self._cached_mel_basis = librosa.filters.mel(
            sr=self.sample_rate,
            n_fft=self.hop_length * 4,
            n_mels=self.n_mels
        )
    
    def optimize_batch_size(self):
        """Optimize batch size based on performance metrics."""
        if self.resource_manager:
            self.batch_size = self.resource_manager.optimize_batch_size(self.batch_size)
    
    def supports_realtime(self) -> bool:
        """Whether this extractor supports real-time processing."""
        return True
    
    def get_required_sample_rate(self) -> int:
        """Get the required sample rate for this processor."""
        return self.sample_rate
    
    def get_supported_channels(self) -> List[int]:
        """Get supported number of channels."""
        return [1, 2]  # Mono and stereo
    
    def get_active_notes(self) -> List[int]:
        """Get currently active notes."""
        return []  # Implemented in MIDI-specific subclass
    
    def extract_features(self, data: Any, context: ProcessingContext) -> Dict[str, Any]:
        """Extract features from input data."""
        if isinstance(data, np.ndarray):
            features = self.process_chunk(data, context)
            return features.to_dict()
        elif isinstance(data, dict) and 'event_type' in data:
            features = self.process_event(data, context)
            return features.to_dict()
        else:
            raise ProcessingError(f"Unsupported data type: {type(data)}")
    
    def process_chunk(self, audio_data: np.ndarray, context: ProcessingContext) -> AudioFeatures:
        """Process an audio chunk."""
        return self.extract_audio_features(audio_data, context.timestamp)
    
    def process_event(self, event: Dict[str, Any], context: ProcessingContext) -> MIDIFeatures:
        """Process a MIDI event."""
        # This is a simplified version - in practice, you'd maintain state
        return self.extract_midi_features([], [], [event], context.timestamp)
    
    def extract_audio_features(self, audio_data: np.ndarray, timestamp: float) -> AudioFeatures:
        """Extract comprehensive features from audio data."""
        try:
            start_time = time.time()
            
            # Convert to mono if needed
            if len(audio_data.shape) > 1:
                audio_data = librosa.to_mono(audio_data)
            
            # Use GPU if available and beneficial
            if self.use_torch and self.device.type == 'cuda' and (
                self.resource_manager is None or self.resource_manager.should_use_gpu()
            ):
                features = self._extract_features_gpu(audio_data)
            else:
                features = self._extract_features_cpu(audio_data)
            
            # Update performance metrics
            if self.performance_monitor:
                processing_time = time.time() - start_time
                metrics = self.performance_monitor.get_current_metrics()
                metrics.processing_time = processing_time
                
                # Optimize batch size periodically
                if processing_time > 0.1:  # If processing is slow
                    self.optimize_batch_size()
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting audio features: {e}")
            raise ProcessingError(f"Failed to extract audio features: {e}")
    
    def _extract_features_gpu(self, audio_data: np.ndarray) -> AudioFeatures:
        """Extract features using GPU acceleration."""
        # Convert to torch tensor
        audio_tensor = torch.from_numpy(audio_data).float().to(self.device)
        
        # Compute STFT using pre-allocated window
        D = torch.stft(
            audio_tensor,
            n_fft=self.hop_length * 4,
            hop_length=self.hop_length,
            window=self._window,
            return_complex=True
        )
        
        # Compute magnitude spectrogram
        S = torch.abs(D)
        
        # Compute mel spectrogram using pre-allocated mel basis
        mel_spec = torch.matmul(self._mel_basis, S)
        
        # Move other computations to separate thread to maximize GPU utilization
        spectral_future = self.thread_pool.submit(
            self._compute_spectral_features_gpu,
            S
        )
        
        # Compute other features in parallel
        pitch_future = self.thread_pool.submit(
            self._compute_pitch_gpu,
            audio_tensor
        )
        
        # Get results
        spectral_features = spectral_future.result()
        pitch_data = pitch_future.result()
        tempo, beat_frames = librosa.beat.beat_track(y=audio_data, sr=self.sample_rate)
        onset_frames = librosa.onset.onset_detect(y=audio_data, sr=self.sample_rate)
        
        return AudioFeatures(
            timestamp=time.time(),
            tempo=tempo,
            beat_positions=librosa.frames_to_time(beat_frames, sr=self.sample_rate).tolist(),
            onset_positions=librosa.frames_to_time(onset_frames, sr=self.sample_rate).tolist(),
            **spectral_features,
            **pitch_data
        )
    
    def _extract_features_cpu(self, audio_data: np.ndarray) -> AudioFeatures:
        """Extract features using CPU."""
        # Use cached resources
        D = librosa.stft(
            audio_data,
            n_fft=self.hop_length * 4,
            hop_length=self.hop_length,
            window=self._cached_stft_window
        )
        
        # Process in parallel
        spectral_future = self.thread_pool.submit(
            self._compute_spectral_features_cpu,
            audio_data,
            self.sample_rate
        )
        
        pitch_future = self.thread_pool.submit(
            self._compute_pitch_cpu,
            audio_data,
            self.sample_rate
        )
        
        # Get results
        spectral_features = spectral_future.result()
        pitch_data = pitch_future.result()
        
        # Add beat tracking
        tempo, beat_frames = librosa.beat.beat_track(y=audio_data, sr=self.sample_rate)
        onset_frames = librosa.onset.onset_detect(y=audio_data, sr=self.sample_rate)
        
        return AudioFeatures(
            timestamp=time.time(),
            tempo=tempo,
            beat_positions=librosa.frames_to_time(beat_frames, sr=self.sample_rate).tolist(),
            onset_positions=librosa.frames_to_time(onset_frames, sr=self.sample_rate).tolist(),
            **spectral_features,
            **pitch_data,
        )
    
    def extract_midi_features(self, 
                            active_notes: List[int],
                            active_velocities: List[int],
                            recent_events: List[Dict[str, Any]],
                            timestamp: float) -> MIDIFeatures:
        """Extract musical features from MIDI data."""
        try:
            if not active_notes:
                return MIDIFeatures(
                    timestamp=timestamp,
                    active_notes=[],
                    active_velocities=[],
                    note_density=0.0,
                    average_velocity=0.0,
                    pitch_range=(0, 0),
                    recent_onsets=[],
                )
            
            # Calculate note density (notes per second)
            recent_onsets = [
                event['timestamp'] for event in recent_events
                if event.get('event_type') == 'note_on'
                and timestamp - event['timestamp'] <= 1.0  # Look at last second
            ]
            note_density = len(recent_onsets)
            
            # Calculate pitch range
            pitch_range = (min(active_notes), max(active_notes))
            
            # Calculate average velocity
            average_velocity = np.mean(active_velocities) if active_velocities else 0.0
            
            # Estimate chord (simple algorithm - can be enhanced)
            active_notes_set = set(active_notes)
            chord_estimate = None
            if len(active_notes_set) >= 3:
                # Convert MIDI notes to pitch classes
                pitch_classes = set(note % 12 for note in active_notes)
                # TODO: Implement more sophisticated chord recognition
                
            return MIDIFeatures(
                timestamp=timestamp,
                active_notes=active_notes,
                active_velocities=active_velocities,
                note_density=note_density,
                average_velocity=float(average_velocity),
                pitch_range=pitch_range,
                recent_onsets=recent_onsets,
                chord_estimate=chord_estimate
            )
            
        except Exception as e:
            logger.error(f"Error extracting MIDI features: {e}")
            raise ProcessingError(f"Failed to extract MIDI features: {e}")
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'thread_pool'):
            if isinstance(self.thread_pool, OptimizedThreadPool):
                self.thread_pool.shutdown()
            else:
                self.thread_pool.shutdown(wait=False)
        
        if hasattr(self, 'performance_monitor') and self.performance_monitor:
            self.performance_monitor.stop_monitoring()
        
        # Clear GPU memory
        if hasattr(self, 'device') and self.device.type == 'cuda':
            torch.cuda.empty_cache()

    def _compute_spectral_features_cpu(self, y: np.ndarray, sr: int) -> Dict[str, float]:
        """Compute spectral features using Numba-optimized calculations."""
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)[0]
        spectral_flatness = librosa.feature.spectral_flatness(y=y)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]

        return {
            'spectral_centroid_mean': float(np.mean(spectral_centroid)),
            'spectral_centroid_std': float(np.std(spectral_centroid)),
            'spectral_bandwidth_mean': float(np.mean(spectral_bandwidth)),
            'spectral_contrast_mean': float(np.mean(spectral_contrast)),
            'spectral_flatness_mean': float(np.mean(spectral_flatness)),
            'spectral_rolloff_mean': float(np.mean(spectral_rolloff)),
            'spectral_variance': float(np.var(y))
        }

    def _compute_pitch_cpu(self, y: np.ndarray, sr: int) -> Dict[str, float]:
        """Compute pitch-related features using optimized CPU calculations."""
        try:
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_mean = np.mean(pitches[pitches > 0])
            pitch_std = np.std(pitches[pitches > 0])
            
            # Additional pitch detection using YIN algorithm
            pitch_yin = librosa.yin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
            pitch_yin = pitch_yin[~np.isnan(pitch_yin)]
            
            return {
                'pitch_mean': float(pitch_mean),
                'pitch_std': float(pitch_std),
                'pitch_confidence': float(np.mean(magnitudes)),
                'pitch_yin_mean': float(np.mean(pitch_yin)) if len(pitch_yin) > 0 else 0.0,
                'pitch_range': float(np.ptp(pitches[pitches > 0])) if len(pitches[pitches > 0]) > 0 else 0.0
            }
        except Exception as e:
            logger.error(f"Pitch computation failed: {str(e)}")
            return {
                'pitch_mean': 0.0,
                'pitch_std': 0.0,
                'pitch_confidence': 0.0,
                'pitch_yin_mean': 0.0,
                'pitch_range': 0.0
            } 
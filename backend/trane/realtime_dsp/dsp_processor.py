"""Module implementing the DSP service interface."""
import asyncio
import logging
from typing import Dict, Any, Optional, List
import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from .interfaces import (
    DSPServiceInterface,
    ProcessingContext,
    FeatureSet,
    ProcessingError,
    ConfigurationError
)
from .feature_extraction import FeatureExtractor, AudioFeatures, MIDIFeatures
from .buffer_manager import SyncManager

logger = logging.getLogger(__name__)

class DSPProcessor(DSPServiceInterface):
    """Main DSP processor implementing the service interface."""
    def __init__(self, 
                 sync_manager: Optional[SyncManager] = None,
                 sample_rate: int = 22050,
                 max_workers: int = 4):
        self.sync_manager = sync_manager or SyncManager()
        self.sample_rate = sample_rate
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.feature_extractor = FeatureExtractor(sample_rate=sample_rate)
        self.processing_contexts: Dict[str, ProcessingContext] = {}
        self.feature_cache: Dict[str, FeatureSet] = {}
        self._lock = asyncio.Lock()
    
    async def process_stream(self, stream_id: str, data: Any) -> Dict[str, Any]:
        """Process streaming data asynchronously."""
        try:
            # Get or create processing context
            context = self._get_or_create_context(stream_id)
            
            # Process in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            features = await loop.run_in_executor(
                self.executor,
                self.feature_extractor.extract_features,
                data,
                context
            )
            
            # Cache the features
            async with self._lock:
                self.feature_cache[stream_id] = features
            
            return features
            
        except Exception as e:
            logger.error(f"Error processing stream {stream_id}: {e}")
            raise ProcessingError(f"Stream processing failed: {e}")
    
    async def process_file(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Process a file asynchronously."""
        try:
            # Create a unique context for this file
            context = ProcessingContext(
                timestamp=time.time(),
                sample_rate=self.sample_rate,
                source_id=file_path,
                metadata=options
            )
            
            # Process in chunks if specified
            chunk_size = options.get('chunk_size')
            if chunk_size:
                return await self._process_file_chunked(file_path, chunk_size, context)
            else:
                return await self._process_file_complete(file_path, context)
                
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise ProcessingError(f"File processing failed: {e}")
    
    def get_features(self, source_id: str) -> Dict[str, Any]:
        """Get latest features for a source."""
        try:
            # Try to get from sync manager first
            if self.sync_manager:
                sync_data = self.sync_manager.get_synchronized_data(duration=0.1)
                if source_id in sync_data.get('audio', {}):
                    return sync_data['audio'][source_id]
                elif source_id in sync_data.get('midi', {}):
                    return sync_data['midi'][source_id]
            
            # Fall back to cached features
            if source_id in self.feature_cache:
                return self.feature_cache[source_id].to_dict()
            
            raise KeyError(f"No features found for source {source_id}")
            
        except Exception as e:
            logger.error(f"Error getting features for {source_id}: {e}")
            raise ProcessingError(f"Failed to get features: {e}")
    
    async def _process_file_chunked(self, 
                                  file_path: str, 
                                  chunk_size: int,
                                  context: ProcessingContext) -> Dict[str, Any]:
        """Process a file in chunks."""
        try:
            import librosa
            
            features_list = []
            
            # Stream the file in chunks
            for i, chunk in enumerate(librosa.stream(
                file_path,
                block_length=chunk_size,
                frame_length=2048,
                hop_length=512
            )):
                # Update context for this chunk
                chunk_context = ProcessingContext(
                    timestamp=time.time(),
                    sample_rate=context.sample_rate,
                    source_id=f"{context.source_id}_chunk_{i}",
                    metadata={'chunk_index': i, **context.metadata} if context.metadata else {'chunk_index': i}
                )
                
                # Process chunk
                chunk_features = await self.process_stream(chunk_context.source_id, chunk)
                features_list.append(chunk_features)
            
            # Aggregate features
            return self._aggregate_features(features_list)
            
        except Exception as e:
            logger.error(f"Error in chunked processing of {file_path}: {e}")
            raise ProcessingError(f"Chunked processing failed: {e}")
    
    async def _process_file_complete(self, 
                                   file_path: str,
                                   context: ProcessingContext) -> Dict[str, Any]:
        """Process a complete file."""
        try:
            import librosa
            
            # Load the entire file
            y, sr = librosa.load(file_path, sr=self.sample_rate)
            
            # Process the complete file
            return await self.process_stream(context.source_id, y)
            
        except Exception as e:
            logger.error(f"Error in complete processing of {file_path}: {e}")
            raise ProcessingError(f"Complete processing failed: {e}")
    
    def _get_or_create_context(self, source_id: str) -> ProcessingContext:
        """Get existing context or create a new one."""
        if source_id not in self.processing_contexts:
            self.processing_contexts[source_id] = ProcessingContext(
                timestamp=time.time(),
                sample_rate=self.sample_rate,
                source_id=source_id
            )
        return self.processing_contexts[source_id]
    
    def _aggregate_features(self, features_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate features from multiple chunks."""
        if not features_list:
            return {}
        
        # Initialize with first feature set
        aggregated = features_list[0].copy()
        aggregated['chunks'] = features_list
        
        # Calculate averages for numerical features
        numerical_features = [
            'pitch', 'pitch_confidence', 'tempo', 'rms_energy',
            'spectral_centroid', 'spectral_bandwidth', 'spectral_rolloff'
        ]
        
        for feature in numerical_features:
            values = [
                f.get(feature) for f in features_list
                if f.get(feature) is not None
            ]
            if values:
                aggregated[f'average_{feature}'] = float(np.mean(values))
        
        return aggregated
    
    async def close(self):
        """Clean up resources."""
        self.executor.shutdown(wait=False)
        if self.sync_manager:
            # Clean up sync manager resources
            pass 
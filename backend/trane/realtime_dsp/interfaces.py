"""Abstract interfaces for DSP modules."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Protocol, TypeVar, Generic
from dataclasses import dataclass
import numpy as np
import time

T = TypeVar('T')
InputDataType = TypeVar('InputDataType')
OutputDataType = TypeVar('OutputDataType')

@dataclass
class ProcessingContext:
    """Context information for processing operations."""
    timestamp: float
    sample_rate: int
    source_id: str
    metadata: Optional[Dict[str, Any]] = None

class DataSource(Protocol[T]):
    """Protocol for data sources (audio or MIDI)."""
    def start(self) -> None:
        """Start the data source."""
        ...
    
    def stop(self) -> None:
        """Stop the data source."""
        ...
    
    def is_active(self) -> bool:
        """Check if the source is active."""
        ...

class DataProcessor(Protocol[InputDataType, OutputDataType]):
    """Protocol for data processors."""
    def process(self, data: InputDataType, context: ProcessingContext) -> OutputDataType:
        """Process input data and return results."""
        ...

class FeatureExtractorBase(ABC):
    """Base class for feature extractors."""
    @abstractmethod
    def extract_features(self, data: Any, context: ProcessingContext) -> Dict[str, Any]:
        """Extract features from input data."""
        pass
    
    @abstractmethod
    def supports_realtime(self) -> bool:
        """Whether this extractor supports real-time processing."""
        pass

class DataBuffer(Generic[T]):
    """Interface for data buffers."""
    @abstractmethod
    def add(self, data: T, timestamp: float) -> None:
        """Add data to the buffer."""
        pass
    
    @abstractmethod
    def get_recent(self, duration: float) -> List[T]:
        """Get data from the last duration seconds."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear the buffer."""
        pass

class DSPServiceInterface(ABC):
    """Interface for DSP services."""
    @abstractmethod
    async def process_stream(self, stream_id: str, data: Any) -> Dict[str, Any]:
        """Process streaming data."""
        pass
    
    @abstractmethod
    async def process_file(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Process a file."""
        pass
    
    @abstractmethod
    def get_features(self, source_id: str) -> Dict[str, Any]:
        """Get latest features for a source."""
        pass

class AudioProcessorInterface(ABC):
    """Interface for audio processors."""
    @abstractmethod
    def process_chunk(self, audio_data: np.ndarray, context: ProcessingContext) -> Dict[str, Any]:
        """Process an audio chunk."""
        pass
    
    @abstractmethod
    def get_required_sample_rate(self) -> int:
        """Get the required sample rate for this processor."""
        pass
    
    @abstractmethod
    def get_supported_channels(self) -> List[int]:
        """Get supported number of channels."""
        pass

class MIDIProcessorInterface(ABC):
    """Interface for MIDI processors."""
    @abstractmethod
    def process_event(self, event: Dict[str, Any], context: ProcessingContext) -> Dict[str, Any]:
        """Process a MIDI event."""
        pass
    
    @abstractmethod
    def get_active_notes(self) -> List[int]:
        """Get currently active notes."""
        pass

class StreamProcessor(Generic[InputDataType, OutputDataType]):
    """Base class for stream processors."""
    def __init__(self):
        self.is_running = False
        self._start_time = 0.0
    
    @abstractmethod
    async def process(self, data: InputDataType) -> OutputDataType:
        """Process a single piece of data."""
        pass
    
    def start(self) -> None:
        """Start the processor."""
        self.is_running = True
        self._start_time = time.time()
    
    def stop(self) -> None:
        """Stop the processor."""
        self.is_running = False
    
    def get_uptime(self) -> float:
        """Get processor uptime in seconds."""
        if not self.is_running:
            return 0.0
        return time.time() - self._start_time

class FeatureSet(ABC):
    """Base class for feature sets."""
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert features to dictionary format."""
        pass
    
    @abstractmethod
    def merge(self, other: 'FeatureSet') -> 'FeatureSet':
        """Merge with another feature set."""
        pass
    
    @abstractmethod
    def get_timestamp(self) -> float:
        """Get the timestamp of this feature set."""
        pass

class DSPError(Exception):
    """Base class for DSP-related errors."""
    pass

class ProcessingError(DSPError):
    """Error during data processing."""
    pass

class ConfigurationError(DSPError):
    """Error in DSP configuration."""
    pass 
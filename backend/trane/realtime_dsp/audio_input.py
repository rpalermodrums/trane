"""Module for handling real-time audio input from various sources."""
import numpy as np
import soundfile as sf
import webrtcvad
import logging
from typing import Generator, Optional, Dict, Any
from dataclasses import dataclass
from queue import Queue
import threading
import time

logger = logging.getLogger(__name__)

@dataclass
class AudioChunk:
    """Container for audio data and metadata."""
    data: np.ndarray
    sample_rate: int
    timestamp: float
    is_speech: bool = False
    metadata: Optional[Dict[str, Any]] = None

class AudioInputBase:
    """Base class for audio input sources."""
    def __init__(self, sample_rate: int = 22050, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.is_running = False
        self._buffer = Queue(maxsize=100)  # Buffer 100 chunks max
        
    def start(self):
        """Start audio capture."""
        self.is_running = True
        
    def stop(self):
        """Stop audio capture."""
        self.is_running = False
        
    def get_chunk(self) -> Optional[AudioChunk]:
        """Get the next audio chunk from the buffer."""
        try:
            return self._buffer.get_nowait()
        except:
            return None

class FileAudioInput(AudioInputBase):
    """Handle audio input from files."""
    def __init__(self, file_path: str, **kwargs):
        super().__init__(**kwargs)
        self.file_path = file_path
        self._thread = None
        
    def start(self):
        """Start reading from file in a separate thread."""
        super().start()
        self._thread = threading.Thread(target=self._read_file)
        self._thread.daemon = True
        self._thread.start()
        
    def _read_file(self):
        """Read file in chunks."""
        try:
            with sf.SoundFile(self.file_path) as f:
                while self.is_running:
                    data = f.read(self.chunk_size)
                    if len(data) == 0:
                        break
                        
                    chunk = AudioChunk(
                        data=data,
                        sample_rate=f.samplerate,
                        timestamp=time.time()
                    )
                    self._buffer.put(chunk)
                    
        except Exception as e:
            logger.error(f"Error reading audio file: {e}")

class WebRTCAudioInput(AudioInputBase):
    """Handle audio input from WebRTC streams."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.vad = webrtcvad.Vad(3)  # Aggressiveness level 3
        self._thread = None
        
    def handle_stream_data(self, data: bytes):
        """Handle incoming WebRTC audio data."""
        try:
            # Convert bytes to numpy array (assuming 16-bit PCM)
            audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Check for speech
            is_speech = self.vad.is_speech(data, self.sample_rate)
            
            chunk = AudioChunk(
                data=audio_data,
                sample_rate=self.sample_rate,
                timestamp=time.time(),
                is_speech=is_speech
            )
            self._buffer.put(chunk)
            
        except Exception as e:
            logger.error(f"Error processing WebRTC data: {e}")

class AudioInputManager:
    """Manage multiple audio input sources."""
    def __init__(self):
        self.sources: Dict[str, AudioInputBase] = {}
        
    def add_source(self, source_id: str, source: AudioInputBase):
        """Add a new audio source."""
        self.sources[source_id] = source
        
    def remove_source(self, source_id: str):
        """Remove an audio source."""
        if source_id in self.sources:
            self.sources[source_id].stop()
            del self.sources[source_id]
            
    def get_chunks(self) -> Generator[AudioChunk, None, None]:
        """Get chunks from all active sources."""
        for source_id, source in self.sources.items():
            chunk = source.get_chunk()
            if chunk is not None:
                yield chunk 
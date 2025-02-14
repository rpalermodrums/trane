"""Module for managing synchronized buffers and timing in real-time DSP."""
import numpy as np
import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import deque
import logging
from .audio_input import AudioChunk
from .midi_input import MIDIEvent

logger = logging.getLogger(__name__)

@dataclass
class TimedBuffer:
    """Base class for timed circular buffers."""
    max_size: int
    window_size: float  # Size of the window in seconds
    
    def __post_init__(self):
        self.buffer = deque(maxlen=self.max_size)
        self.lock = threading.Lock()
        self.last_timestamp = 0.0
    
    def cleanup_old_data(self, current_time: float):
        """Remove data older than window_size seconds."""
        with self.lock:
            while self.buffer and (current_time - self.buffer[0].timestamp) > self.window_size:
                self.buffer.popleft()

class AudioBuffer(TimedBuffer):
    """Circular buffer for audio chunks with timing information."""
    def add_chunk(self, chunk: AudioChunk):
        """Add an audio chunk to the buffer."""
        with self.lock:
            self.buffer.append(chunk)
            self.last_timestamp = max(self.last_timestamp, chunk.timestamp)
            
    def get_recent_chunks(self, duration: float) -> List[AudioChunk]:
        """Get audio chunks from the last 'duration' seconds."""
        current_time = time.time()
        self.cleanup_old_data(current_time)
        
        with self.lock:
            return [
                chunk for chunk in self.buffer
                if (current_time - chunk.timestamp) <= duration
            ]

class MIDIBuffer(TimedBuffer):
    """Circular buffer for MIDI events with timing information."""
    def __post_init__(self):
        super().__post_init__()
        self.active_notes: Dict[int, MIDIEvent] = {}
    
    def add_event(self, event: MIDIEvent):
        """Add a MIDI event to the buffer and update active notes."""
        with self.lock:
            self.buffer.append(event)
            self.last_timestamp = max(self.last_timestamp, event.timestamp)
            
            # Update active notes
            if event.event_type == 'note_on' and event.note is not None:
                self.active_notes[event.note] = event
            elif event.event_type == 'note_off' and event.note is not None:
                self.active_notes.pop(event.note, None)
    
    def get_recent_events(self, duration: float) -> List[MIDIEvent]:
        """Get MIDI events from the last 'duration' seconds."""
        current_time = time.time()
        self.cleanup_old_data(current_time)
        
        with self.lock:
            return [
                event for event in self.buffer
                if (current_time - event.timestamp) <= duration
            ]
    
    def get_active_notes(self) -> List[MIDIEvent]:
        """Get currently active notes."""
        with self.lock:
            return list(self.active_notes.values())

class SyncManager:
    """Manager for synchronizing multiple audio and MIDI streams."""
    def __init__(self, window_size: float = 1.0):
        self.window_size = window_size
        self.audio_buffers: Dict[str, AudioBuffer] = {}
        self.midi_buffers: Dict[str, MIDIBuffer] = {}
        self.source_latencies: Dict[str, float] = {}
        self._lock = threading.Lock()
        
    def register_audio_source(self, source_id: str, max_size: int = 1000):
        """Register a new audio source."""
        with self._lock:
            if source_id not in self.audio_buffers:
                self.audio_buffers[source_id] = AudioBuffer(
                    max_size=max_size,
                    window_size=self.window_size
                )
                
    def register_midi_source(self, source_id: str, max_size: int = 1000):
        """Register a new MIDI source."""
        with self._lock:
            if source_id not in self.midi_buffers:
                self.midi_buffers[source_id] = MIDIBuffer(
                    max_size=max_size,
                    window_size=self.window_size
                )
    
    def remove_source(self, source_id: str):
        """Remove an audio or MIDI source."""
        with self._lock:
            self.audio_buffers.pop(source_id, None)
            self.midi_buffers.pop(source_id, None)
            self.source_latencies.pop(source_id, None)
    
    def update_source_latency(self, source_id: str, latency: float):
        """Update the measured latency for a source."""
        with self._lock:
            self.source_latencies[source_id] = latency
    
    def add_audio_chunk(self, source_id: str, chunk: AudioChunk):
        """Add an audio chunk to the appropriate buffer."""
        with self._lock:
            if source_id in self.audio_buffers:
                # Adjust timestamp by source latency if known
                if source_id in self.source_latencies:
                    chunk.timestamp -= self.source_latencies[source_id]
                self.audio_buffers[source_id].add_chunk(chunk)
    
    def add_midi_event(self, source_id: str, event: MIDIEvent):
        """Add a MIDI event to the appropriate buffer."""
        with self._lock:
            if source_id in self.midi_buffers:
                # Adjust timestamp by source latency if known
                if source_id in self.source_latencies:
                    event.timestamp -= self.source_latencies[source_id]
                self.midi_buffers[source_id].add_event(event)
    
    def get_synchronized_data(self, duration: float) -> Dict[str, Dict[str, Any]]:
        """Get synchronized data from all sources for the specified duration."""
        result = {'audio': {}, 'midi': {}}
        current_time = time.time()
        
        with self._lock:
            # Get audio data
            for source_id, buffer in self.audio_buffers.items():
                chunks = buffer.get_recent_chunks(duration)
                if chunks:
                    result['audio'][source_id] = {
                        'chunks': chunks,
                        'latest_timestamp': buffer.last_timestamp
                    }
            
            # Get MIDI data
            for source_id, buffer in self.midi_buffers.items():
                events = buffer.get_recent_events(duration)
                active_notes = buffer.get_active_notes()
                if events or active_notes:
                    result['midi'][source_id] = {
                        'events': events,
                        'active_notes': active_notes,
                        'latest_timestamp': buffer.last_timestamp
                    }
            
            result['timestamp'] = current_time
            
        return result
    
    def estimate_sync_offset(self, source_id: str, reference_time: float) -> float:
        """Estimate the synchronization offset for a source."""
        with self._lock:
            if source_id in self.audio_buffers:
                buffer = self.audio_buffers[source_id]
            elif source_id in self.midi_buffers:
                buffer = self.midi_buffers[source_id]
            else:
                return 0.0
            
            if not buffer.buffer:
                return 0.0
                
            # Calculate offset between source timestamps and reference time
            source_time = buffer.last_timestamp
            return reference_time - source_time 
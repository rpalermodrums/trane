"""Module for handling MIDI input from various sources."""
import logging
from typing import Optional, Dict, List, Generator, Any
from dataclasses import dataclass
from queue import Queue
import threading
import time

logger = logging.getLogger(__name__)

@dataclass
class MIDIEvent:
    """Container for MIDI event data."""
    event_type: str  # 'note_on', 'note_off', 'control_change', etc.
    note: Optional[int] = None
    velocity: Optional[int] = None
    channel: int = 0
    timestamp: float = 0.0
    controller: Optional[int] = None
    value: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class MIDIInputBase:
    """Base class for MIDI input sources."""
    def __init__(self):
        self.is_running = False
        self._buffer = Queue(maxsize=1000)  # Buffer for MIDI events
        self._active_notes: Dict[int, MIDIEvent] = {}  # Currently active notes
        
    def start(self):
        """Start MIDI capture."""
        self.is_running = True
        
    def stop(self):
        """Stop MIDI capture."""
        self.is_running = False
        
    def get_event(self) -> Optional[MIDIEvent]:
        """Get the next MIDI event from the buffer."""
        try:
            return self._buffer.get_nowait()
        except:
            return None
        
    def get_active_notes(self) -> List[MIDIEvent]:
        """Get list of currently active notes."""
        return list(self._active_notes.values())

class FileMIDIInput(MIDIInputBase):
    """Handle MIDI input from files."""
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self._thread = None
        
    def start(self):
        """Start reading from MIDI file in a separate thread."""
        super().start()
        self._thread = threading.Thread(target=self._read_file)
        self._thread.daemon = True
        self._thread.start()
        
    def _read_file(self):
        """Read MIDI file events."""
        try:
            # Note: This is a placeholder. In a real implementation,
            # you would use a library like mido to read MIDI files
            logger.info(f"Reading MIDI file: {self.file_path}")
            # Simulate reading MIDI file
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error reading MIDI file: {e}")

class WebMIDIInput(MIDIInputBase):
    """Handle Web MIDI API input."""
    def handle_midi_message(self, data: bytes):
        """Handle incoming Web MIDI message."""
        try:
            # Parse MIDI message (basic MIDI message format)
            status_byte = data[0]
            channel = status_byte & 0x0F
            message_type = status_byte & 0xF0
            
            event = None
            
            # Note On
            if message_type == 0x90 and len(data) >= 3:
                note = data[1]
                velocity = data[2]
                if velocity > 0:
                    event = MIDIEvent(
                        event_type='note_on',
                        note=note,
                        velocity=velocity,
                        channel=channel,
                        timestamp=time.time()
                    )
                    self._active_notes[note] = event
                else:
                    # Note On with velocity 0 is equivalent to Note Off
                    event = MIDIEvent(
                        event_type='note_off',
                        note=note,
                        velocity=0,
                        channel=channel,
                        timestamp=time.time()
                    )
                    self._active_notes.pop(note, None)
                    
            # Note Off
            elif message_type == 0x80 and len(data) >= 3:
                note = data[1]
                velocity = data[2]
                event = MIDIEvent(
                    event_type='note_off',
                    note=note,
                    velocity=velocity,
                    channel=channel,
                    timestamp=time.time()
                )
                self._active_notes.pop(note, None)
                
            # Control Change
            elif message_type == 0xB0 and len(data) >= 3:
                controller = data[1]
                value = data[2]
                event = MIDIEvent(
                    event_type='control_change',
                    controller=controller,
                    value=value,
                    channel=channel,
                    timestamp=time.time()
                )
            
            if event:
                self._buffer.put(event)
                
        except Exception as e:
            logger.error(f"Error processing MIDI message: {e}")

class MIDIInputManager:
    """Manage multiple MIDI input sources."""
    def __init__(self):
        self.sources: Dict[str, MIDIInputBase] = {}
        
    def add_source(self, source_id: str, source: MIDIInputBase):
        """Add a new MIDI source."""
        self.sources[source_id] = source
        
    def remove_source(self, source_id: str):
        """Remove a MIDI source."""
        if source_id in self.sources:
            self.sources[source_id].stop()
            del self.sources[source_id]
            
    def get_events(self) -> Generator[MIDIEvent, None, None]:
        """Get events from all active sources."""
        for source_id, source in self.sources.items():
            event = source.get_event()
            if event is not None:
                yield event
                
    def get_all_active_notes(self) -> Dict[str, List[MIDIEvent]]:
        """Get active notes from all sources."""
        return {
            source_id: source.get_active_notes()
            for source_id, source in self.sources.items()
        } 
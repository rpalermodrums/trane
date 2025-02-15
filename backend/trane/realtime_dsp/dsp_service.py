# backend/trane/realtime_dsp/dsp_service.py
import os
import time
import logging
import django
from flask import Flask, jsonify, request
from celery.result import AsyncResult
import redis
from celery import Celery
import socketio
from typing import Dict, Any

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trane.settings')
django.setup()

# Now we can import Django models
from trane.realtime_dsp.tasks import process_audio_file
from .audio_input import AudioInputManager, FileAudioInput, WebRTCAudioInput, AudioChunk
from .midi_input import MIDIInputManager, WebMIDIInput, MIDIEvent
from .buffer_manager import SyncManager

# Configure logging to display info-level messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Socket.IO server for WebSocket support
sio = socketio.Server(async_mode='threading', cors_allowed_origins='*')

def create_app():
    app = Flask(__name__)
    
    # Configure Flask app
    app.config.update(
        PROPAGATE_EXCEPTIONS=True,
        JSONIFY_PRETTYPRINT_REGULAR=True
    )
    
    # Initialize managers
    app.audio_manager = AudioInputManager()
    app.midi_manager = MIDIInputManager()
    app.sync_manager = SyncManager(window_size=1.0)  # 1-second window for sync
    
    # Test Redis connection
    try:
        redis_client = redis.Redis(host='redis', port=6379, db=0)
        redis_client.ping()
        logger.info("Successfully connected to Redis")
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
    
    # Test Celery connection
    try:
        celery_app = Celery('trane')
        celery_app.config_from_object('django.conf:settings', namespace='CELERY')
        celery_app.connection().ensure_connection(timeout=5)
        logger.info("Successfully connected to Celery broker")
    except Exception as e:
        logger.error(f"Failed to connect to Celery broker: {e}")
    
    # IMPORTANT:
    # Do not wrap the Flask app with Socket.IO here.
    # We'll wrap it when starting the server.
    
    return app

# Create the Flask app (without wrapping)
app = create_app()

# Path to a sample audio file; ensure this file is present in the same folder
AUDIO_SAMPLE = os.path.join(os.path.dirname(__file__), "audio_sample.wav")

@app.route('/process_audio', methods=['POST'])
def process_audio():
    """Start asynchronous processing of an audio file."""
    try:
        data = request.get_json()
        audio_path = data.get('audio_path', AUDIO_SAMPLE)
        chunk_size = data.get('chunk_size')
        source_id = data.get('source_id', 'default')
        
        if not os.path.exists(audio_path):
            return jsonify({'error': 'Audio file not found'}), 404
        
        logger.info(f"Starting async processing for file: {audio_path}")
        
        # Create and register file audio source
        audio_source = FileAudioInput(audio_path, chunk_size=chunk_size)
        app.audio_manager.add_source(source_id, audio_source)
        app.sync_manager.register_audio_source(source_id)
        audio_source.start()
        
        # Start async processing task
        try:
            task = process_audio_file.delay(audio_path, chunk_size)
            logger.info(f"Successfully created task with ID: {task.id}")
            return jsonify({
                'task_id': task.id,
                'source_id': source_id,
                'status': 'processing',
                'message': 'Audio processing started'
            }), 202
        except Exception as e:
            logger.error(f"Failed to create Celery task: {e}")
            return jsonify({'error': f'Failed to start processing: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Error in process_audio endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/task_status/<task_id>')
def get_task_status(task_id):
    """Check the status of an audio processing task."""
    try:
        task_result = AsyncResult(task_id)
        
        if task_result.ready():
            if task_result.successful():
                return jsonify({
                    'status': 'completed',
                    'result': task_result.get()
                })
            else:
                return jsonify({
                    'status': 'failed',
                    'error': str(task_result.result)
                }), 500
        
        return jsonify({
            'status': 'processing',
            'message': 'Task is still processing'
        }), 202
        
    except Exception as e:
        logging.error(f"Error checking task status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/latest_features')
def latest_features():
    """Get latest synchronized features from all active sources."""
    try:
        # Get synchronized data from the last 100ms
        sync_data = app.sync_manager.get_synchronized_data(duration=0.1)
        
        # Format the response
        response = {
            'audio': {},
            'midi': {},
            'timestamp': sync_data['timestamp']
        }
        
        # Process audio data
        for source_id, audio_data in sync_data['audio'].items():
            chunks = audio_data['chunks']
            if chunks:
                response['audio'][source_id] = {
                    'timestamp': audio_data['latest_timestamp'],
                    'is_speech': any(chunk.is_speech for chunk in chunks),
                    'sample_rate': chunks[0].sample_rate if chunks else None
                }
        
        # Process MIDI data
        for source_id, midi_data in sync_data['midi'].items():
            active_notes = midi_data['active_notes']
            if active_notes:
                response['midi'][source_id] = {
                    'timestamp': midi_data['latest_timestamp'],
                    'active_notes': [
                        {
                            'note': note.note,
                            'velocity': note.velocity,
                            'timestamp': note.timestamp
                        }
                        for note in active_notes
                    ]
                }
        
        return jsonify(response)
        
    except Exception as e:
        logging.error(f"Error getting latest features: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Socket.IO event handlers
@sio.on('connect')
def handle_connect(sid, environ):
    """Handle new WebSocket connection."""
    logger.info(f"Client connected: {sid}")

@sio.on('disconnect')
def handle_disconnect(sid):
    """Handle WebSocket disconnection."""
    logger.info(f"Client disconnected: {sid}")
    # Clean up any sources associated with this session
    app.audio_manager.remove_source(sid)
    app.midi_manager.remove_source(sid)
    app.sync_manager.remove_source(sid)

@sio.on('audio_stream')
def handle_audio_stream(sid, data):
    """Handle incoming audio stream data."""
    try:
        # Get or create WebRTC audio source for this session
        if sid not in app.audio_manager.sources:
            source = WebRTCAudioInput()
            app.audio_manager.add_source(sid, source)
            app.sync_manager.register_audio_source(sid)
            source.start()
        
        # Process the audio data
        source = app.audio_manager.sources[sid]
        source.handle_stream_data(data)
        
        # Get the latest chunk and add it to sync manager
        chunk = source.get_chunk()
        if chunk:
            app.sync_manager.add_audio_chunk(sid, chunk)
        
    except Exception as e:
        logger.error(f"Error processing audio stream: {e}")

@sio.on('midi_message')
def handle_midi_message(sid, data):
    """Handle incoming MIDI message."""
    try:
        # Get or create Web MIDI source for this session
        if sid not in app.midi_manager.sources:
            source = WebMIDIInput()
            app.midi_manager.add_source(sid, source)
            app.sync_manager.register_midi_source(sid)
            source.start()
        
        # Process the MIDI message
        source = app.midi_manager.sources[sid]
        source.handle_midi_message(data)
        
        # Get the latest event and add it to sync manager
        event = source.get_event()
        if event:
            app.sync_manager.add_midi_event(sid, event)
        
    except Exception as e:
        logger.error(f"Error processing MIDI message: {e}")

@sio.on('latency_report')
def handle_latency_report(sid, data):
    """Handle client latency report for better synchronization."""
    try:
        latency = float(data.get('latency', 0))
        app.sync_manager.update_source_latency(sid, latency)
        logger.info(f"Updated latency for {sid}: {latency}ms")
    except Exception as e:
        logger.error(f"Error processing latency report: {e}")

if __name__ == '__main__':
    # Instead of calling app.run() on the Socket.IO wrapped app (which doesn't have .route),
    # we now wrap the Flask app here and serve it using an appropriate WSGI server.
    try:
        import eventlet
        import eventlet.wsgi
        # Wrap the Flask app with Socket.IO's WSGIApp for websocket support
        application = socketio.WSGIApp(sio, app)
        eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 9000)), application)
    except ImportError:
        # Fallback to Flask's built-in server (note: this may not support websockets well)
        app.run(host='0.0.0.0', port=9000)

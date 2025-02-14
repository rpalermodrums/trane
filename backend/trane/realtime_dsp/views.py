from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
import os
import json
from .tasks import process_audio_file, process_midi_events
from .models import ProcessingTask, ProcessingResult

def upload_page(request):
    """Render the upload page."""
    return render(request, 'realtime_dsp/upload.html')

@csrf_exempt
def upload_file(request):
    """Handle file upload and start processing."""
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        file_path = fs.path(filename)
        
        # Determine file type and process accordingly
        if filename.lower().endswith(('.wav', '.mp3', '.ogg')):
            task = process_audio_file.delay(file_path)
            file_type = 'audio'
        elif filename.lower().endswith('.mid'):
            task = process_midi_events.delay([], 0)  # Simplified for now
            file_type = 'midi'
        else:
            return JsonResponse({
                'error': 'Unsupported file type'
            }, status=400)
        
        return JsonResponse({
            'task_id': task.id,
            'file_type': file_type,
            'message': 'Processing started'
        })
    
    return JsonResponse({
        'error': 'No file provided'
    }, status=400)

def get_result(request, task_id):
    """Get the processing result for a task."""
    try:
        task = ProcessingTask.objects.get(task_id=task_id)
        
        if task.status == 'completed':
            result = ProcessingResult.objects.get(task=task)
            return JsonResponse({
                'status': 'completed',
                'result': result.features
            })
        elif task.status == 'failed':
            return JsonResponse({
                'status': 'failed',
                'error': task.error_message
            }, status=500)
        else:
            return JsonResponse({
                'status': task.status,
                'message': 'Task is still processing'
            })
            
    except ProcessingTask.DoesNotExist:
        return JsonResponse({
            'error': 'Task not found'
        }, status=404) 
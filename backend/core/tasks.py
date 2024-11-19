from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Entry
import os
import subprocess
import re

@shared_task(bind=True)
def process_audio(self, entry_id):
    channel_layer = get_channel_layer()
    entry = Entry.objects.get(id=entry_id)
    entry.processing_status = 'processing'
    entry.save()

    def update_progress(progress, status='processing'):
        async_to_sync(channel_layer.group_send)(
            f'task_{entry_id}',
            {
                'type': 'progress_update',
                'progress': progress,
                'status': status
            }
        )

    try:
        audio_path = entry.audio_file.path
        output_dir = os.path.join(os.path.dirname(audio_path), f"entry_{entry_id}_stems")
        os.makedirs(output_dir, exist_ok=True)

        command = ['demucs', '-o', output_dir, '--verbose']
        
        if entry.model_version:
            command.extend(['--model', entry.model_version])
            
        if entry.processing_options.get('instruments'):
            command.extend(['--two-stems'] + list(entry.processing_options['instruments']))
            
        command.append(audio_path)

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Monitor progress
        for line in process.stderr:
            if 'Progress:' in line:
                progress = re.search(r'(\d+)%', line)
                if progress:
                    update_progress(int(progress.group(1)))

        process.wait()
        
        if process.returncode == 0:
            entry.processing_status = 'completed'
            entry.save()
            update_progress(100, 'completed')
            return {
                'status': 'success',
                'output_dir': output_dir
            }
        else:
            raise Exception(f"Process failed with return code {process.returncode}")
            
    except Exception as e:
        entry.processing_status = 'failed'
        entry.error_message = str(e)
        entry.save()
        update_progress(0, 'failed')
        raise e

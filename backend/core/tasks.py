from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import os
import subprocess
import re

from core.models import Entry

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
            command.extend(['-n', entry.model_version])
            
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
        stderr_output = []
        for line in process.stderr:
            stderr_output.append(line)
            if 'Progress:' in line:
                progress = re.search(r'(\d+)%', line)
                if progress:
                    update_progress(int(progress.group(1)))

        process.wait()

        if process.returncode != 0:
            error_msg = '\n'.join(stderr_output)
            raise Exception(f"Process failed with return code {process.returncode}. Error: {error_msg}")
        
        entry.processing_status = 'completed'
        entry.save()
        update_progress(100, 'completed')
        return {
            'status': 'success',
            'output_dir': output_dir
        }
            
    except Exception as e:
        entry.processing_status = 'failed'
        entry.error_message = str(e)
        entry.save()
        update_progress(0, 'failed')
        raise e

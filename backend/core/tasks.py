from celery import shared_task
from .models import Entry
import os
import subprocess

@shared_task
def process_audio(entry_id):
    entry = Entry.objects.get(id=entry_id)
    audio_path = entry.audio_file.path
    output_dir = os.path.join(os.path.dirname(audio_path), f"entry_{entry_id}_stems")
    os.makedirs(output_dir, exist_ok=True)

    # Use Demucs to separate audio
    command = [
        'demucs',
        '-o', output_dir,
        audio_path
    ]

    subprocess.run(command, check=True)

    # Update entry with processing status (you may need to add fields to your model)
    entry.processing_status = 'completed'
    entry.save()

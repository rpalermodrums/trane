from django.db import models
from django.contrib.auth.models import User
import os

class Entry(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    audio_file = models.FileField(upload_to='audio_files/')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entries')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_entries')
    notes = models.ManyToManyField('Note', related_name='entries', blank=True)
    documents = models.ManyToManyField('Document', related_name='entries', blank=True)
    processing_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    model_version = models.CharField(max_length=50, default='htdemucs')
    processing_options = models.JSONField(default=dict)
    error_message = models.TextField(null=True, blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(default=0)
    duration = models.FloatField(null=True, blank=True)
    output_directory = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['processing_status', 'priority']),
            models.Index(fields=['user', '-created_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.original_filename and self.audio_file:
            self.original_filename = os.path.basename(self.audio_file.name)
        
        if self.audio_file and not self.file_size:
            self.file_size = self.audio_file.size
            
        if self.audio_file and not self.duration:
            try:
                import librosa
                y, sr = librosa.load(self.audio_file.path)
                self.duration = librosa.get_duration(y=y, sr=sr)
            except Exception:
                self.duration = 0
                
        super().save(*args, **kwargs)


class Note(models.Model):
    entry = models.ForeignKey(Entry, related_name='notes_set', on_delete=models.CASCADE)
    content = models.TextField()
    title = models.CharField(max_length=255)
    description = models.TextField()
    tags = models.ManyToManyField('Tag', related_name='notes')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_notes')

class Document(models.Model):
    entry = models.ForeignKey(Entry, related_name='documents_set', on_delete=models.CASCADE)
    file = models.FileField(upload_to='documents/')
    title = models.CharField(max_length=255)
    description = models.TextField()
    type = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_documents')

class Tag(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_tags')
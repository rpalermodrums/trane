from django.db import models
from django.contrib.auth.models import User

class Entry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    audio_file = models.FileField(upload_to='audio_files/')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entries')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_entries')
    notes = models.ManyToManyField('Note', related_name='entries')
    documents = models.ManyToManyField('Document', related_name='entries')
    processing_status = models.CharField(max_length=20, default='pending')


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
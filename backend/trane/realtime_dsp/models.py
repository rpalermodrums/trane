"""Models for storing DSP processing results and task information."""
from django.db import models
from django.utils import timezone
import uuid

class ProcessingTask(models.Model):
    """Model for tracking DSP processing tasks."""
    TASK_TYPES = [
        ('audio', 'Audio Processing'),
        ('midi', 'MIDI Processing'),
        ('feature', 'Feature Extraction'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_id = models.CharField(max_length=255, unique=True)
    task_type = models.CharField(max_length=10, choices=TASK_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['task_type', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.task_type} - {self.status} ({self.task_id})"

class ProcessingResult(models.Model):
    """Model for storing processing results."""
    task = models.OneToOneField(ProcessingTask, on_delete=models.CASCADE, related_name='result')
    features = models.JSONField()  # Stores extracted features
    metadata = models.JSONField(default=dict)  # Additional metadata
    source_file = models.CharField(max_length=255, null=True, blank=True)
    processing_time = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Result for {self.task.task_id}"

class PerformanceMetrics(models.Model):
    """Model for storing performance metrics."""
    timestamp = models.DateTimeField(default=timezone.now)
    cpu_usage = models.FloatField()
    memory_usage = models.FloatField()
    processing_time = models.FloatField()
    queue_length = models.IntegerField()
    gpu_memory_used = models.FloatField(null=True, blank=True)
    gpu_utilization = models.FloatField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
        ]
        
    def __str__(self):
        return f"Metrics at {self.timestamp}" 
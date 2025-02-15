import os
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from django.utils import timezone
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trane.settings')

# Create the Celery app
app = Celery('trane')

# Configure Celery using Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Explicit Redis configuration
app.conf.broker_transport_options = {
    'visibility_timeout': 3600,
    'fanout_prefix': True,
    'fanout_patterns': True,
    'queue_order_strategy': 'priority',
}

# Force all tasks to use direct routing
app.conf.task_default_exchange = 'direct'
app.conf.task_default_exchange_type = 'direct'
app.conf.task_default_routing_key = 'audio'
app.conf.task_default_queue = 'audio'

# Update task routes to use direct binding
app.conf.task_routes = {
    'trane.realtime_dsp.tasks.process_audio_file': {
        'queue': 'audio',
        'exchange': 'direct',
        'routing_key': 'audio'
    },
    'trane.realtime_dsp.tasks.process_midi_events': {
        'queue': 'midi',
        'exchange': 'direct',
        'routing_key': 'midi'
    },
    'trane.realtime_dsp.tasks.cleanup_old_results': {
        'queue': 'maintenance',
        'exchange': 'direct',
        'routing_key': 'maintenance'
    },
}

# Disable automatic queue creation
app.conf.task_create_missing_queues = False

# Configure task queues
app.conf.task_queues = {
    'audio': {
        'exchange': 'audio',
        'routing_key': 'audio',
    },
    'midi': {
        'exchange': 'midi',
        'routing_key': 'midi',
    },
    'maintenance': {
        'exchange': 'maintenance',
        'routing_key': 'maintenance',
    },
}

# Configure periodic tasks
app.conf.beat_schedule = {
    'cleanup-old-results': {
        'task': 'trane.realtime_dsp.tasks.cleanup_old_results',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
    'log-performance-metrics': {
        'task': 'trane.realtime_dsp.tasks.log_performance_metrics',
        'schedule': 300.0,  # Every 5 minutes
    },
}

# Auto-discover tasks in all registered Django app configs
app.autodiscover_tasks()

@task_prerun.connect
def task_prerun_handler(task_id=None, task=None, *args, **kwargs):
    """Handle task pre-run events."""
    from trane.realtime_dsp.models import ProcessingTask
    try:
        task_obj = ProcessingTask.objects.get(task_id=task_id)
        task_obj.status = 'processing'
        task_obj.started_at = timezone.now()
        task_obj.save()
    except ProcessingTask.DoesNotExist:
        pass

@task_postrun.connect
def task_postrun_handler(task_id=None, task=None, state=None, *args, **kwargs):
    """Handle task completion events."""
    from trane.realtime_dsp.models import ProcessingTask
    try:
        task_obj = ProcessingTask.objects.get(task_id=task_id)
        task_obj.status = 'completed' if state == 'SUCCESS' else 'failed'
        task_obj.completed_at = timezone.now()
        task_obj.save()
    except ProcessingTask.DoesNotExist:
        pass

@task_failure.connect
def task_failure_handler(task_id=None, exception=None, *args, **kwargs):
    """Handle task failure events."""
    from trane.realtime_dsp.models import ProcessingTask
    try:
        task_obj = ProcessingTask.objects.get(task_id=task_id)
        task_obj.status = 'failed'
        task_obj.error_message = str(exception)
        task_obj.completed_at = timezone.now()
        task_obj.save()
    except ProcessingTask.DoesNotExist:
        pass

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}') 
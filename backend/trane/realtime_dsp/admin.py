from django.contrib import admin
from .models import ProcessingTask, ProcessingResult, PerformanceMetrics

@admin.register(ProcessingTask)
class ProcessingTaskAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'task_type', 'status', 'created_at', 'completed_at')
    list_filter = ('task_type', 'status', 'created_at')
    search_fields = ('task_id', 'error_message')
    readonly_fields = ('id', 'task_id', 'created_at', 'updated_at')
    ordering = ('-created_at',)

@admin.register(ProcessingResult)
class ProcessingResultAdmin(admin.ModelAdmin):
    list_display = ('task', 'source_file', 'processing_time', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('source_file',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

@admin.register(PerformanceMetrics)
class PerformanceMetricsAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'cpu_usage', 'memory_usage', 'processing_time', 'queue_length')
    list_filter = ('timestamp',)
    ordering = ('-timestamp',) 
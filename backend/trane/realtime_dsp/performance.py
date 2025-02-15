"""Module for performance monitoring and optimization."""
import time
import logging
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from collections import deque
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import torch

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    cpu_usage: float
    memory_usage: float
    processing_time: float
    queue_length: int
    gpu_memory_used: Optional[float] = None
    gpu_utilization: Optional[float] = None

class PerformanceMonitor:
    """Monitor system performance and resource usage."""
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics_history = deque(maxlen=window_size)
        self.process = psutil.Process()
        self._lock = threading.Lock()
        self.is_monitoring = False
        self._monitor_thread = None
        
        # GPU monitoring
        self.has_gpu = torch.cuda.is_available()
        if self.has_gpu:
            logger.info(f"GPU available: {torch.cuda.get_device_name(0)}")
    
    def start_monitoring(self, interval: float = 1.0):
        """Start periodic performance monitoring."""
        self.is_monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.is_monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join()
    
    def _monitor_loop(self, interval: float):
        """Continuous monitoring loop."""
        while self.is_monitoring:
            try:
                metrics = self.get_current_metrics()
                with self._lock:
                    self.metrics_history.append(metrics)
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
            time.sleep(interval)
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_info = self.process.memory_info()
        memory_percent = memory_info.rss / psutil.virtual_memory().total * 100
        
        metrics = PerformanceMetrics(
            cpu_usage=cpu_percent,
            memory_usage=memory_percent,
            processing_time=0.0,  # Will be updated by processors
            queue_length=0  # Will be updated by processors
        )
        
        if self.has_gpu:
            try:
                gpu_memory = torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated() * 100
                metrics.gpu_memory_used = gpu_memory
                # Note: GPU utilization would require nvidia-smi which might not be available
            except Exception as e:
                logger.warning(f"Error getting GPU metrics: {e}")
        
        return metrics
    
    def get_average_metrics(self, window: Optional[int] = None) -> PerformanceMetrics:
        """Get average metrics over the specified window."""
        with self._lock:
            if not self.metrics_history:
                return self.get_current_metrics()
            
            window = window or len(self.metrics_history)
            recent_metrics = list(self.metrics_history)[-window:]
            
            # Gather lists for GPU metrics only if available
            gpu_memory_list = [m.gpu_memory_used for m in recent_metrics if m.gpu_memory_used is not None]
            gpu_utilization_list = [m.gpu_utilization for m in recent_metrics if m.gpu_utilization is not None]
            
            return PerformanceMetrics(
                cpu_usage=np.mean([m.cpu_usage for m in recent_metrics]),
                memory_usage=np.mean([m.memory_usage for m in recent_metrics]),
                processing_time=np.mean([m.processing_time for m in recent_metrics]),
                queue_length=np.mean([m.queue_length for m in recent_metrics]),
                gpu_memory_used=np.mean(gpu_memory_list) if gpu_memory_list else None,
                gpu_utilization=np.mean(gpu_utilization_list) if gpu_utilization_list else None
            )

class ResourceManager:
    """Manage and optimize resource allocation."""
    def __init__(self, 
                 monitor: PerformanceMonitor,
                 target_cpu_usage: float = 80.0,
                 target_memory_usage: float = 80.0,
                 target_gpu_memory: float = 80.0):
        self.monitor = monitor
        self.target_cpu_usage = target_cpu_usage
        self.target_memory_usage = target_memory_usage
        self.target_gpu_memory = target_gpu_memory
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self._lock = threading.Lock()
    
    def optimize_thread_pool(self, current_workers: int) -> int:
        """Optimize number of worker threads based on performance metrics."""
        metrics = self.monitor.get_average_metrics(window=10)
        
        # Start conservative
        new_workers = current_workers
        
        # Adjust based on CPU usage
        if metrics.cpu_usage > self.target_cpu_usage:
            new_workers = max(1, current_workers - 1)
        elif metrics.cpu_usage < self.target_cpu_usage * 0.7:  # Some headroom
            new_workers = min(psutil.cpu_count(), current_workers + 1)
        
        return new_workers
    
    def should_use_gpu(self) -> bool:
        """Determine if GPU should be used based on current metrics."""
        if not torch.cuda.is_available():
            return False
        
        metrics = self.monitor.get_current_metrics()
        if metrics.gpu_memory_used and metrics.gpu_memory_used > self.target_gpu_memory:
            return False
        
        return True
    
    def optimize_batch_size(self, current_batch_size: int) -> int:
        """Optimize batch size based on performance metrics."""
        metrics = self.monitor.get_average_metrics(window=10)
        
        # Start conservative
        new_batch_size = current_batch_size
        
        # Adjust based on memory usage and processing time
        if metrics.memory_usage > self.target_memory_usage:
            new_batch_size = max(1, current_batch_size // 2)
        elif metrics.memory_usage < self.target_memory_usage * 0.7:
            new_batch_size = min(1024, current_batch_size * 2)
        
        return new_batch_size

class OptimizedThreadPool:
    """Thread pool that automatically adjusts its size based on performance."""
    def __init__(self, 
                 resource_manager: ResourceManager,
                 initial_workers: int = 4,
                 min_workers: int = 1,
                 max_workers: Optional[int] = None):
        self.resource_manager = resource_manager
        self.min_workers = min_workers
        self.max_workers = max_workers or psutil.cpu_count()
        self.current_workers = initial_workers
        self.executor = ThreadPoolExecutor(max_workers=initial_workers)
        self._lock = threading.Lock()
        
        # Start optimization loop
        self.is_optimizing = True
        self._optimize_thread = threading.Thread(
            target=self._optimization_loop,
            daemon=True
        )
        self._optimize_thread.start()
    
    def submit(self, fn: Callable, *args, **kwargs):
        """Submit a task to the thread pool."""
        return self.executor.submit(fn, *args, **kwargs)
    
    def _optimization_loop(self):
        """Continuously optimize thread pool size."""
        while self.is_optimizing:
            try:
                new_workers = self.resource_manager.optimize_thread_pool(self.current_workers)
                new_workers = max(self.min_workers, min(self.max_workers, new_workers))
                
                if new_workers != self.current_workers:
                    with self._lock:
                        # Create new executor with updated worker count
                        old_executor = self.executor
                        self.executor = ThreadPoolExecutor(max_workers=new_workers)
                        self.current_workers = new_workers
                        # Shutdown old executor gracefully
                        old_executor.shutdown(wait=False)
                        
                        logger.info(f"Adjusted thread pool size to {new_workers} workers")
                
            except Exception as e:
                logger.error(f"Error in thread pool optimization: {e}")
            
            time.sleep(5)  # Check every 5 seconds
    
    def shutdown(self):
        """Shutdown the thread pool."""
        self.is_optimizing = False
        self.executor.shutdown(wait=True) 
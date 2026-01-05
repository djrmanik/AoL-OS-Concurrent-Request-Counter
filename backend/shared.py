import time
import math
from dataclasses import dataclass
from prometheus_client import Counter, Histogram

# Prometheus Metrics
REQUEST_COUNT = Counter('app_requests_total', 'Total HTTP Requests', ['version', 'status'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency', ['version'])
GLOBAL_COUNTER_GAUGE = Counter('app_global_counter', 'Value of the global shared counter') 

@dataclass
class ProcessingResult:
    request_id: str
    processing_time_ms: float
    total_processed_requests: int
    worker_id: str

class GlobalCounter:
    """
    A shared resource representing the 'Ledger'.
    Demonstrates race conditions when locking is absent.
    """
    def __init__(self):
        self._value = 0

    def get_value(self):
        return self._value

    def increment_unsafe(self):
        """
        Increments the counter without any synchronization.
        Susceptible to race conditions (read-modify-write).
        """
        current = self._value
        # Artificial delay to widen the race condition window
        time.sleep(0.001) 
        self._value = current + 1
        return self._value
    
    def increment_safe(self, lock):
        """
        Increments the counter using a mutex.
        Thread-safe but incurs synchronization overhead.
        """
        with lock:
            current = self._value
            # Even with delay, the lock ensures mutual exclusion
            time.sleep(0.001)
            self._value = current + 1
            return self._value

def cpu_bound_task(duration_ms=50):
    """
    Simulates CPU intensive work (arithmetic operations).
    """
    end_time = time.time() + (duration_ms / 1000.0)
    while time.time() < end_time:
        _ = math.sqrt(64 * 64) * math.sqrt(25 * 25)

def io_bound_task(duration_ms=50):
    """
    Simulates I/O intensive work (waiting/sleeping).
    """
    time.sleep(duration_ms / 1000.0)

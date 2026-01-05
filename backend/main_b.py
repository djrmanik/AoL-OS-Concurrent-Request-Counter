import time
import uuid
import os
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared import GlobalCounter, cpu_bound_task, io_bound_task, ProcessingResult, REQUEST_COUNT, REQUEST_LATENCY

app = FastAPI(title="OS Experiment - Version B (Concurrent)")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared Global State
counter = GlobalCounter()
counter_lock = threading.Lock()

# Thread Pool for Worker Threads
# We use a limited pool to simulate a specific number of "Cashiers"
executor = ThreadPoolExecutor(max_workers=8)

def process_workload_sync(workload_type: str, duration_ms: int, use_lock: bool, req_id: str):
    """
    The actual function running inside a thread.
    """
    start_time = time.time()
    
    # 1. Simulate Workload
    if workload_type == "io":
        io_bound_task(duration_ms)
    else:
        cpu_bound_task(duration_ms)
    
    # 2. Update Shared Resource
    if use_lock:
        new_count = counter.increment_safe(counter_lock)
    else:
        new_count = counter.increment_unsafe()
        
    end_time = time.time()
    processing_time = (end_time - start_time) * 1000

    # Record Metrics
    REQUEST_COUNT.labels(version='B', status='success').inc()
    REQUEST_LATENCY.labels(version='B').observe(processing_time / 1000.0)
    
    return ProcessingResult(
        request_id=req_id,
        processing_time_ms=round(processing_time, 2),
        total_processed_requests=new_count,
        worker_id=f"thread_{threading.get_ident()}"
    )

@app.post("/process")
async def process_request(workload_type: str = "cpu", duration_ms: int = 50, use_lock: bool = False):
    """
    Version B: Concurrent Processing.
    Offloads work to a ThreadPoolExecutor.
    - use_lock=False -> Race Conditions (Buggy)
    - use_lock=True -> Correct (Synchronized)
    """
    req_id = str(uuid.uuid4())
    
    # Offload to thread pool to unblock the main asyncio loop and allow true concurrency
    # (subject to GIL, but effective for I/O and demonstrable for race conditions)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor, 
        process_workload_sync, 
        workload_type, 
        duration_ms, 
        use_lock, 
        req_id
    )
    
    return result

@app.get("/metrics")
def get_metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/reset")
def reset_counter():
    # We should probably lock this too in a real app, but for reset it's fine
    with counter_lock:
        counter._value = 0
    return {"message": "Counter reset"}

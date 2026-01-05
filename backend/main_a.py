import time
import uuid
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared import GlobalCounter, cpu_bound_task, io_bound_task, ProcessingResult, REQUEST_COUNT, REQUEST_LATENCY

app = FastAPI(title="OS Experiment - Version A (Serial)")

# CORS to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared Global State
counter = GlobalCounter()

@app.post("/process")
async def process_request(workload_type: str = "cpu", duration_ms: int = 50):
    """
    Version A: Serial Processing.
    FastAPI with a single worker effectively processes these sequentially
    if the workload is blocking (CPU bound) or if the event loop is blocked.
    """
    start_time = time.time()
    req_id = str(uuid.uuid4())
    
    # 1. Simulate Workload (Blocking)
    # Note: We are deliberately NOT using 'await' for the CPU task or using async sleep 
    # to simulate a blocking OS process/thread behavior in this single-worker environment.
    if workload_type == "io":
        io_bound_task(duration_ms)
    else:
        cpu_bound_task(duration_ms)
    
    # 2. Update Shared Resource
    # No lock needed because we assume single-threaded execution for Version A
    new_count = counter.increment_unsafe()
    
    end_time = time.time()
    processing_time = (end_time - start_time) * 1000
    
    # Record Metrics
    REQUEST_COUNT.labels(version='A', status='success').inc()
    REQUEST_LATENCY.labels(version='A').observe(processing_time / 1000.0)
    
    return ProcessingResult(
        request_id=req_id,
        processing_time_ms=round(processing_time, 2),
        total_processed_requests=new_count,
        worker_id=f"worker_A_{os.getpid()}" # Narrative: Single process
    )

@app.get("/metrics")
def get_metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/reset")
def reset_counter():
    counter._value = 0
    return {"message": "Counter reset"}

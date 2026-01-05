OS Concurrency Experiment - Walkthrough
1. System Overview
This system is an experimental tool designed to demonstrate operating system concepts:

Scheduling: Contrast between single-threaded (Version A) and multi-threaded (Version B) execution.
Race Conditions: Visualized by the "Shared Counter" deviating from the expected value when locking is disabled.
Synchronization: Demonstrated by enabling the "Safe" mode in Version B.

2. Running the System
Prerequisites
Docker & Docker Compose installed.

3. Start the System
Run the following command in the project root:
docker-compose up --build

4. Access Points
Component	URL	Description
- Frontend UI	http://localhost:8081	--> The main visualization dashboard.
- Backend A	http://localhost:8001/docs --> Serial API (Baseline).
- Backend B	http://localhost:8002/docs --> Concurrent API.
- Prometheus	http://localhost:9091	--> Metrics collection.
- Grafana	http://localhost:3001	--> Performance dashboards

3. Experiment Flow
Experiment A: The Bottleneck (Version A)
- Open the Frontend UI.
- Select Version A (Serial).
- Click Send 50 Requests.

Observe:
- The "Cashier" (Backend Worker) processes one request at a time.
- Latency for later requests is huge (queueing delay).
- OS Narrative: "The single thread is blocked by CPU work, causing a convoy effect."

Experiment B: Race Condition (Version B - Unsafe)
- Select Version B (Concurrent).
- Select Unsafe (Race Condition).
- Click Reset Counter.
- Click Send 100 Requests.

Observe:
- Multiple "Cashiers" light up simultaneously (Parallelism).
- Requests complete much faster.
- Critical: The "Total Processed" counter will likely be less than 100 (e.g., 95, 98).
- OS Narrative: "Multiple threads read-modify-write the shared counter simultaneously, causing lost updates."

Experiment C: Synchronization (Version B - Safe)
- Select Safe (With Lock).
- Click Reset Counter.
- Click Send 100 Requests.

Observe:
- Performance is still high (parallelism).
- Total Processed is exactly 100.
- OS Narrative: "The Mutex ensures mutual exclusion for the critical section, restoring correctness at a slight synchronization cost."

4. Monitoring & Load Testing
- Viewing Metrics in Grafana
- Log in to Grafana (admin/admin).
- Add Prometheus as a Data Source.
- URL: http://prometheus:9090 (Keep this because internally in Docker they still communicate on 9090).

Create a Dashboard with query: rate(app_requests_total[1m]).
Running Load Tests
Use Locust to saturate the system:

# In a new terminal
cd load_test
locust -f locustfile.py --host http://localhost:8001 # For Version A

5. File Structure
backend/shared.py: Contains the GlobalCounter and race condition logic.
backend/main_a.py: Single-threaded implementation.
backend/main_b.py: Multi-threaded ThreadPoolExecutor implementation.
frontend/index.html: The visualization logic.

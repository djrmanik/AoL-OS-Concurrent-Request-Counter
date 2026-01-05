from locust import HttpUser, task, between

class OSWebUser(HttpUser):
    wait_time = between(0.5, 2)

    @task
    def process_request(self):
        # We target the /process endpoint
        # The host is set via command line or UI
        # We can randomize parameters if needed
        self.client.post("/process?workload_type=cpu&duration_ms=50")

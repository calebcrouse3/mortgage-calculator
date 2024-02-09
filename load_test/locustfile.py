from locust import HttpUser, task, between

class MortgageSimulatorUser(HttpUser):
    wait_time = between(2, 10) # Wait time between tasks (1 to 5 seconds)

    @task
    def view_main_page(self):
        self.client.get("/") # Simulating a visit to the main page
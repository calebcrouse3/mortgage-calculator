from locust import HttpUser, task, between

class MortgageSimulatorUser(HttpUser):
    wait_time = between(1, 5) # Wait time between tasks (1 to 5 seconds)

    @task
    def view_main_page(self):
        self.client.get("/") # Simulating a visit to the main page

    # @task
    # def simulate_button_click(self):
    #     # Replace the below URL and data with the actual endpoint and data sent when a user clicks a button on your site
    #     self.client.post("/button-click-endpoint", {
    #         "key": "value" # Example payload, adjust based on your application's requirements
    #     })
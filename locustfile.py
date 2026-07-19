'''import random
from locust import HttpUser, task, between, SequentialTaskSet

class AstroUserWorkflow(SequentialTaskSet):
    """
    A sequential workflow mimicking a user signing up, logging in,
    browsing the dashboard, searching, and adding/deleting targets.
    """
    
    def on_start(self):
        """Runs once when a virtual user is spawned."""
        # Generate a unique username for this virtual test runner
        self.username = f"test_user_{random.randint(10000, 99999)}"
        self.password = "SecurePassword123!"
        self.created_target_ids = []

    @task
    def view_signup_page(self):
        self.client.get("/signup")

    @task
    def complete_signup(self):
        # Use 'data=' for standard form submissions (request.form.get)
        payload = {
            "username": self.username,
            "password": self.password
        }
        self.client.post("/signup-process", data=payload)

    @task
    def view_login_page(self):
        self.client.get("/login")

    @task
    def complete_login(self):
        payload = {
            "username": self.username,
            "password": self.password
        }
        # Locust automatically captures the session cookie set by Flask
        self.client.post("/login-process", data=payload)

    @task
    def view_dashboard(self):
        self.client.get("/")

    @task
    def search_targets(self):
        # Test the search query route
        queries = ["Orion", "Andromeda", "Mars", "M45"]
        selected_query = random.choice(queries)
        self.client.get(f"/search?q={selected_query}&page=0")

    @task
    def load_more_pagination(self):
        self.client.get("/load-more?page=1")

    @task
    def add_astronomy_target(self):
        payload = {
            "name": f"Target-{random.randint(1,1000)}",
            "ra": "05h 35m 17s",
            "dec": "-05° 23′ 28″",
            "notes": "Automated Locust Load Test Observation Run"
        }
        response = self.client.post("/add-target", data=payload)
        
        # Note: If your backend returns the new ID inside fragment HTML, 
        # a real-world script could parse it out here to dynamically delete it later.

    @task
    def view_profile_and_settings(self):
        self.client.get("/profile")
        self.client.get("/settings")
        self.client.post("/settings_saving_process")

    @task
    def perform_logout(self):
        self.client.get("/logout")
        # Stop this sequential task routine and cycle to a new user iteration
        self.interrupt()


class WebsiteLoadTester(HttpUser):
    # Tasks to execute
    tasks = [AstroUserWorkflow]
    
    # Simulates human think-time between clicks (1 to 3 seconds)
    wait_time = between(1.0, 3.0)'''

import random
from locust import HttpUser, task, between

Test_Users = [
        {"test_user_64345"},
        {"test_user_76813"},
        {"test_user_58505"}
    ]

class AstroHeavyTrafficUser(HttpUser):
    wait_time = between(3, 5)

    def on_start(self):
        """Log in once when the user spawns, using one of the users we know exists."""
        
        self.username = random.choice(Test_Users)
        self.password = "SecurePassword123!"
        
        payload = {"username": self.username, "password": self.password}
        self.client.post("/login-process", data=payload)

    @task(10)  
    def view_dashboard(self):
        self.client.get("/")

    @task(8) 
    def search_targets(self):
        queries = ["Orion", "Andromeda", "Mars", "M45", "Nebula", "Star"]
        self.client.get(f"/search?q={random.choice(queries)}&page=0")

    @task(5)   
    def load_more_pagination(self):
        self.client.get(f"/load-more?page={random.randint(1, 3)}")

    @task(1)
    def add_astronomy_target(self):
        payload = {
            "name": f"Locust-Obs-{random.randint(100,999)}",
            "ra": "18h 36m 56s",
            "dec": "+38° 47′ 01″",
            "notes": "Stress test write operation."
        }
        self.client.post("/add-target", data=payload)
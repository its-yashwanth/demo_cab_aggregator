import locust
import random

class CabAggregatorUser(locust.HttpUser):
    wait_time = locust.between(1, 3)
    
    def on_start(self):
        # Register and login one user for this locust "User"
        self.email = f"locust_user_{random.randint(1, 1000000)}@example.com"
        self.password = "locustpass"
        
        self.client.post("/auth/register", json={
            "name": "Locust User",
            "email": self.email,
            "password": self.password,
            "role": "passenger"
        })
        
        # Verify (using the known mock OTP)
        self.client.post("/auth/verify_otp", json={"email": self.email, "otp": "123456"})
        
        # Login
        r = self.client.post("/auth/login", json={"email": self.email, "password": self.password})
        self.token = r.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @locust.task(10)
    def book_ride_flow(self):
        # Get estimate
        self.client.post("/rides/estimate_fare", json={
            "pickup_lat": 12.9716, "pickup_lon": 77.5946,
            "drop_lat": 12.9345, "drop_lon": 77.6244
        }, headers=self.headers)
        
        # Book
        self.client.post("/rides/book", json={
            "email": self.email,
            "pickup": "Central Bangalore",
            "drop": "Koramangala",
            "pickup_lat": 12.9716, "pickup_lon": 77.5946,
            "drop_lat": 12.9345, "drop_lon": 77.6244
        }, headers=self.headers)

    @locust.task(2)
    def view_history(self):
        self.client.get(f"/rides/history/{self.email}", headers=self.headers)
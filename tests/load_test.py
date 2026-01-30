"""
Load testing suite for ScaleMart using Locust.
Tests the flash sale functionality under high concurrency.

Run with: locust -f tests/load_test.py --host=http://localhost:8000
"""
from locust import HttpUser, task, between, events
import random
import json

class ScaleMartUser(HttpUser):
    """Simulates a user buying products during a flash sale"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a user starts - login and get token"""
        # Create a unique user for this test
        user_id = random.randint(1, 1000000)
        self.email = f"test_user_{user_id}@example.com"
        self.password = "testpassword123"
        
        # Signup
        response = self.client.post("/api/auth/signup", json={
            "email": self.email,
            "password": self.password,
            "name": f"Test User {user_id}"
        })
        
        if response.status_code == 200:
            self.token = response.json()["token"]
        else:
            # Try login if signup fails (user might already exist)
            response = self.client.post("/api/auth/login", json={
                "email": self.email,
                "password": self.password
            })
            if response.status_code == 200:
                self.token = response.json()["token"]
            else:
                self.token = None
    
    @task(3)
    def view_products(self):
        """View product catalog (most common action)"""
        if not self.token:
            return
        
        self.client.get(
            "/api/products",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/products"
        )
    
    @task(5)
    def flash_buy(self):
        """Attempt to buy a flash sale product (main test)"""
        if not self.token:
            return
        
        # Random product ID (prod_1 to prod_6)
        product_id = f"prod_{random.randint(1, 6)}"
        
        response = self.client.post(
            "/api/flash-buy",
            json={
                "product_id": product_id,
                "quantity": 1
            },
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/flash-buy"
        )
        
        # Log if we got out of stock
        if response.status_code == 400:
            if "Out of stock" in response.text:
                print(f"✓ Product {product_id} sold out (expected behavior)")
    
    @task(1)
    def view_orders(self):
        """View order history"""
        if not self.token:
            return
        
        self.client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/orders"
        )
    
    @task(1)
    def view_admin_stats(self):
        """View admin dashboard (simulates admin users)"""
        if not self.token:
            return
        
        self.client.get(
            "/api/admin/stats",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/admin/stats"
        )


class ConcurrencyTestUser(HttpUser):
    """Specialized user for testing atomic inventory under extreme concurrency"""
    
    wait_time = between(0.1, 0.5)  # Very fast requests
    
    def on_start(self):
        """Login once"""
        user_id = random.randint(1, 1000000)
        self.email = f"concurrent_user_{user_id}@example.com"
        self.password = "testpassword123"
        
        response = self.client.post("/api/auth/signup", json={
            "email": self.email,
            "password": self.password,
            "name": f"Concurrent User {user_id}"
        })
        
        if response.status_code == 200:
            self.token = response.json()["token"]
        else:
            response = self.client.post("/api/auth/login", json={
                "email": self.email,
                "password": self.password
            })
            self.token = response.json().get("token") if response.status_code == 200 else None
    
    @task
    def rapid_flash_buy(self):
        """Rapidly attempt to buy the same product (tests atomic operations)"""
        if not self.token:
            return
        
        # Everyone tries to buy prod_1 (highest contention)
        self.client.post(
            "/api/flash-buy",
            json={
                "product_id": "prod_1",
                "quantity": 1
            },
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/flash-buy [concurrent]"
        )


# Custom events for reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("\n" + "="*80)
    print("🚀 ScaleMart Load Test Started")
    print("="*80)
    print("\nTest Scenarios:")
    print("  1. Normal user behavior (view products, buy, check orders)")
    print("  2. High concurrency test (everyone buys same product)")
    print("\nExpected Results:")
    print("  ✓ No overselling (stock never goes negative)")
    print("  ✓ Response time < 100ms for 95th percentile")
    print("  ✓ Error rate < 1% (excluding out-of-stock)")
    print("  ✓ System handles 1000+ concurrent users")
    print("\n" + "="*80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n" + "="*80)
    print("🏁 ScaleMart Load Test Completed")
    print("="*80)
    print("\nCheck Locust web UI for detailed metrics:")
    print("  - Request statistics")
    print("  - Response time charts")
    print("  - Failure analysis")
    print("\n" + "="*80 + "\n")

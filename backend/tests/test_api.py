"""
Basic test suite for ScaleMart backend.
Run with: pytest
"""
import pytest
from httpx import AsyncClient
from server import app
import os

# Test configuration
os.environ['MONGO_URL'] = 'mongodb://localhost:27017'
os.environ['REDIS_URL'] = 'redis://localhost:6379'
os.environ['DB_NAME'] = 'scalemart_test'
os.environ['JWT_SECRET'] = 'test-secret-key'

@pytest.fixture
async def client():
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def auth_token(client):
    """Get authentication token for tests"""
    response = await client.post("/api/auth/signup", json={
        "email": "test@example.com",
        "password": "testpass123",
        "name": "Test User"
    })
    return response.json()["token"]

@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint"""
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_signup(client):
    """Test user signup"""
    response = await client.post("/api/auth/signup", json={
        "email": "newuser@example.com",
        "password": "password123",
        "name": "New User"
    })
    assert response.status_code == 200
    assert "token" in response.json()
    assert "user" in response.json()

@pytest.mark.asyncio
async def test_login(client):
    """Test user login"""
    # First signup
    await client.post("/api/auth/signup", json={
        "email": "logintest@example.com",
        "password": "password123",
        "name": "Login Test"
    })
    
    # Then login
    response = await client.post("/api/auth/login", json={
        "email": "logintest@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "token" in response.json()

@pytest.mark.asyncio
async def test_get_products(client, auth_token):
    """Test getting products"""
    response = await client.get(
        "/api/products",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_flash_buy(client, auth_token):
    """Test flash buy functionality"""
    response = await client.post(
        "/api/flash-buy",
        json={"product_id": "prod_1", "quantity": 1},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    # Should succeed or return out of stock
    assert response.status_code in [200, 400]

@pytest.mark.asyncio
async def test_rate_limiting(client, auth_token):
    """Test rate limiting enforcement"""
    # Make 11 rapid requests (limit is 10)
    for i in range(11):
        response = await client.post(
            "/api/flash-buy",
            json={"product_id": "prod_1", "quantity": 1},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
    
    # Last request should be rate limited
    assert response.status_code == 429

@pytest.mark.asyncio
async def test_unauthorized_access(client):
    """Test that endpoints require authentication"""
    response = await client.get("/api/products")
    assert response.status_code == 403  # Forbidden without token

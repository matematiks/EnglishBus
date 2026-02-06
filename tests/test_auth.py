import pytest
from fastapi.testclient import TestClient
import sqlite3
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.api.dependencies import get_db

client = TestClient(app)

def cleanup_test_user(username):
    """Remove test user from DB"""
    try:
        # Connect to the actual test DB being used
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "englishbus.db")
        conn = sqlite3.connect(db_path)
        conn.execute("DELETE FROM Users WHERE username = ?", (username,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Cleanup failed: {e}")

@pytest.fixture
def test_user():
    username = "test_auth_user"
    password = "securepassword123"
    request_data = {"username": username, "password": password}
    
    # Ensure clean state
    cleanup_test_user(username)
    
    # Register
    response = client.post("/auth/register", json=request_data)
    assert response.status_code == 200
    
    yield request_data
    
    # Cleanup
    cleanup_test_user(username)

def test_register_new_user():
    username = "new_register_user"
    cleanup_test_user(username)
    
    response = client.post("/auth/register", json={"username": username, "password": "password123"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    cleanup_test_user(username)

def test_register_existing_user(test_user):
    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 400

def test_login_success(test_user):
    response = client.post("/auth/login", json=test_user)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user_id" in data

def test_login_wrong_password(test_user):
    response = client.post("/auth/login", json={
        "username": test_user["username"],
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_login_nonexistent_user():
    response = client.post("/auth/login", json={
        "username": "nonexistent_user_999",
        "password": "password"
    })
    assert response.status_code == 401

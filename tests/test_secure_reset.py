import pytest
from fastapi.testclient import TestClient
import sqlite3
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

client = TestClient(app)

def cleanup_test_user(username):
    """Remove test user from DB"""
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "englishbus.db")
        conn = sqlite3.connect(db_path)
        conn.execute("DELETE FROM Users WHERE username = ?", (username,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Cleanup failed: {e}")

@pytest.fixture
def test_user_token():
    username = "reset_test_user"
    password = "resetpassword123"
    cleanup_test_user(username)
    
    # Register
    client.post("/auth/register", json={"username": username, "password": password})
    
    # Login
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    yield {"token": token, "password": password, "username": username}
    
    cleanup_test_user(username)

def test_reset_progress_success(test_user_token):
    # Authenticated reset with correct password
    response = client.post(
        "/reset",
        json={
            "course_id": 1,
            "password": test_user_token["password"]
        },
        headers={"Authorization": f"Bearer {test_user_token['token']}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

def test_reset_progress_wrong_password(test_user_token):
    # Authenticated reset with wrong password
    response = client.post(
        "/reset",
        json={
            "course_id": 1,
            "password": "wrong_password"
        },
        headers={"Authorization": f"Bearer {test_user_token['token']}"}
    )
    assert response.status_code == 401
    assert "Incorrect password" in response.json()["detail"]

def test_reset_progress_no_token(test_user_token):
    # Unauthenticated reset
    response = client.post(
        "/reset",
        json={
            "course_id": 1,
            "password": test_user_token["password"]
        }
    )
    # Should get 401 because Missing Authorization header
    assert response.status_code == 401

def test_reset_progress_invalid_token(test_user_token):
    # Invalid token reset
    response = client.post(
        "/reset",
        json={
            "course_id": 1,
            "password": test_user_token["password"]
        },
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert response.status_code == 401

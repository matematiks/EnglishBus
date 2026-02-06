import requests
import string
import random

BASE_URL = "http://localhost:8000"

def random_string(length=8):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))

def test_register():
    username = f"testuser_{random_string()}"
    password = "testpassword123"
    
    print(f"Attempting to register user: {username}")
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json={"username": username, "password": password})
        
        if response.status_code == 200:
            print("✅ Registration successful!")
            print(response.json())
        else:
            print(f"❌ Registration failed with status {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error during request: {e}")

if __name__ == "__main__":
    test_register()

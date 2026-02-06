import requests
import concurrent.futures
import time
import random
import string

BASE_URL = "http://localhost:8000"
NUM_USERS = 50  # Number of concurrent users
CONCURRENT_THREADS = 10

def random_string(length=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def register_and_login(user_id):
    username = f"stress_user_{user_id}_{random_string(5)}"
    password = "password123"
    
    # Register
    start_time = time.time()
    try:
        reg_response = requests.post(f"{BASE_URL}/auth/register", json={"username": username, "password": password})
        reg_time = time.time() - start_time
        
        if reg_response.status_code != 200:
            return False, f"Register failed: {reg_response.text}", reg_time
            
        # Login
        start_time = time.time()
        login_response = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
        login_time = time.time() - start_time
        
        if login_response.status_code != 200:
            return False, f"Login failed: {login_response.text}", login_time
            
        return True, "Success", login_time
        
    except Exception as e:
        return False, str(e), 0

def run_stress_test():
    print(f"Starting stress test with {NUM_USERS} users, {CONCURRENT_THREADS} threads...")
    
    start_total = time.time()
    success_count = 0
    fail_count = 0
    total_time = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_THREADS) as executor:
        futures = [executor.submit(register_and_login, i) for i in range(NUM_USERS)]
        
        for future in concurrent.futures.as_completed(futures):
            success, message, duration = future.result()
            if success:
                success_count += 1
                total_time += duration
            else:
                fail_count += 1
                print(f"Failure: {message}")

    end_total = time.time()
    
    print("\n--- Stress Test Results ---")
    print(f"Total Users: {NUM_USERS}")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Total Time: {end_total - start_total:.2f}s")
    if success_count > 0:
        print(f"Avg Request Time: {total_time / success_count:.4f}s")

if __name__ == "__main__":
    run_stress_test()

#!/usr/bin/env python3
"""
EnglishBus System Test - Autonomous 3-Cycle Validation
Tests all critical endpoints end-to-end without user interaction
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"
COLORS = {
    "green": "\033[92m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "reset": "\033[0m"
}

class TestRunner:
    def __init__(self):
        self.errors = []
        self.passed = 0
        self.failed = 0
        
    def log(self, message, color="reset"):
        print(f"{COLORS[color]}{message}{COLORS['reset']}")
    
    def test(self, name, func):
        """Run a single test"""
        try:
            self.log(f"\n► Testing: {name}", "blue")
            func()
            self.passed += 1
            self.log(f"✅ PASSED: {name}", "green")
            return True
        except Exception as e:
            self.failed += 1
            error_msg = f"❌ FAILED: {name} - {str(e)}"
            self.log(error_msg, "red")
            self.errors.append(error_msg)
            return False
    
    def assert_status(self, response, expected=200, msg=""):
        if response.status_code != expected:
            raise Exception(f"{msg} - Expected {expected}, got {response.status_code}: {response.text[:200]}")
    
    def assert_field(self, data, field, msg=""):
        if field not in data:
            raise Exception(f"{msg} - Missing field: {field}")
        return data[field]

# Initialize test runner
runner = TestRunner()

def test_health_check():
    """Test API health endpoint"""
    resp = requests.get(f"{BASE_URL}/health")
    runner.assert_status(resp, 200, "Health check failed")
    data = resp.json()
    runner.assert_field(data, "status", "Health check")
    if data["status"] != "healthy":
        raise Exception("API not healthy")

def test_register_new_user():
    """Test user registration"""
    import time
    timestamp = str(int(time.time() * 1000000))  # Microseconds for uniqueness
    username = f"autotest_{timestamp}"
    password = "securepass123"
    
    resp = requests.post(f"{BASE_URL}/auth/register", json={
        "username": username,
        "password": password
    })
    runner.assert_status(resp, 200, "Registration failed")
    data = resp.json()
    runner.assert_field(data, "status", "Registration response")
    
    # Store for next tests
    runner.test_username = username
    runner.test_password = password
    runner.log(f"  → Created user: {username}", "yellow")

def test_login():
    """Test user login"""
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": runner.test_username,
        "password": runner.test_password
    })
    runner.assert_status(resp, 200, "Login failed")
    data = resp.json()
    user_id = runner.assert_field(data, "user_id", "Login response")
    username = runner.assert_field(data, "username", "Login response")
    
    # Store for session tests
    runner.user_id = user_id
    runner.log(f"  → Logged in as user_id: {user_id}", "yellow")

def test_session_start():
    """Test starting a study session"""
    resp = requests.post(f"{BASE_URL}/session/start", json={
        "user_id": runner.user_id,
        "course_id": 1,
        "unit_id": 1
    })
    runner.assert_status(resp, 200, "Session start failed")
    data = resp.json()
    
    session_id = runner.assert_field(data, "session_id", "Session response")
    items = runner.assert_field(data, "items", "Session response")
    current_step = runner.assert_field(data, "current_step", "Session response")
    
    runner.session_items = items
    runner.current_step = current_step
    runner.log(f"  → Session started: {len(items)} items, step {current_step}", "yellow")

def test_session_complete():
    """Test completing a study session"""
    if not runner.session_items:
        raise Exception("No session items to complete")
    
    # Extract word IDs from session items
    word_ids = [item.get("word_id") for item in runner.session_items if item.get("word_id")]
    
    if not word_ids:
        runner.log("  → No word IDs found, skipping session complete", "yellow")
        return
    
    resp = requests.post(f"{BASE_URL}/session/complete", json={
        "user_id": runner.user_id,
        "course_id": 1,
        "completed_word_ids": word_ids
    })
    runner.assert_status(resp, 200, "Session complete failed")
    data = resp.json()
    
    new_step = runner.assert_field(data, "new_step", "Complete response")
    words_updated = runner.assert_field(data, "words_updated", "Complete response")
    runner.log(f"  → Session completed: {words_updated} words, new step {new_step}", "yellow")

def test_practice_sentences():
    """Test sentence practice endpoint"""
    resp = requests.get(f"{BASE_URL}/practice/sentences", params={
        "user_id": runner.user_id,
        "course_id": 1,
        "count": 5
    })
    runner.assert_status(resp, 200, "Practice sentences failed")
    data = resp.json()
    
    sentences = runner.assert_field(data, "sentences", "Sentences response")
    if not isinstance(sentences, list):
        raise Exception("Sentences should be a list")
    
    runner.log(f"  → Generated {len(sentences)} practice sentences", "yellow")

def test_units_status():
    """Test getting units status"""
    resp = requests.get(f"{BASE_URL}/courses/1/units/status", params={
        "user_id": runner.user_id
    })
    runner.assert_status(resp, 200, "Units status failed")
    data = resp.json()
    
    units = runner.assert_field(data, "units", "Units response")
    if not isinstance(units, list):
        raise Exception("Units should be a list")
    
    runner.log(f"  → Retrieved {len(units)} units status", "yellow")

def test_courses_list():
    """Test getting available courses"""
    resp = requests.get(f"{BASE_URL}/courses")
    runner.assert_status(resp, 200, "Courses list failed")
    data = resp.json()
    
    courses = runner.assert_field(data, "courses", "Courses response")
    if not isinstance(courses, list):
        raise Exception("Courses should be a list")
    
    runner.log(f"  → Retrieved {len(courses)} courses", "yellow")

def run_test_cycle(cycle_num):
    """Run one complete test cycle"""
    runner.log(f"\n{'='*60}", "blue")
    runner.log(f"STARTING TEST CYCLE #{cycle_num}", "blue")
    runner.log(f"{'='*60}", "blue")
    
    # Core functionality tests
    runner.test("Health Check", test_health_check)
    runner.test("User Registration", test_register_new_user)
    runner.test("User Login", test_login)
    runner.test("Courses List", test_courses_list)
    runner.test("Session Start", test_session_start)
    runner.test("Session Complete", test_session_complete)
    runner.test("Practice Sentences", test_practice_sentences)
    runner.test("Units Status", test_units_status)
    
    # Summary
    runner.log(f"\n{'='*60}", "blue")
    runner.log(f"CYCLE #{cycle_num} RESULTS:", "blue")
    runner.log(f"  Passed: {runner.passed}", "green")
    runner.log(f"  Failed: {runner.failed}", "red")
    runner.log(f"{'='*60}", "blue")
    
    return runner.failed == 0

def main():
    runner.log("\n🚀 ENGLISHBUS AUTONOMOUS SYSTEM TEST", "blue")
    runner.log("Testing backend APIs through 3 complete cycles\n", "blue")
    
    total_errors = []
    cycles_passed = 0
    
    for i in range(1, 4):
        # Reset counters for each cycle
        runner.errors = []
        runner.passed = 0
        runner.failed = 0
        
        success = run_test_cycle(i)
        
        if success:
            cycles_passed += 1
            runner.log(f"\n✅ CYCLE #{i} PASSED - NO ERRORS!\n", "green")
        else:
            runner.log(f"\n❌ CYCLE #{i} FAILED - {runner.failed} errors\n", "red")
            total_errors.extend(runner.errors)
    
    # Final Report
    runner.log("\n" + "="*60, "blue")
    runner.log("FINAL RESULTS", "blue")
    runner.log("="*60, "blue")
    runner.log(f"Cycles Passed: {cycles_passed}/3", "green" if cycles_passed == 3 else "yellow")
    
    if cycles_passed == 3:
        runner.log("\n🎉 SUCCESS! ALL 3 CYCLES COMPLETED WITHOUT ERRORS!", "green")
        runner.log("✅ System is ready for production use.", "green")
        return 0
    else:
        runner.log(f"\n⚠️  {3 - cycles_passed} cycle(s) had errors:", "yellow")
        for error in total_errors:
            runner.log(f"  {error}", "red")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        runner.log("\n\n⚠️  Test interrupted by user", "yellow")
        sys.exit(130)
    except Exception as e:
        runner.log(f"\n\n❌ CRITICAL ERROR: {str(e)}", "red")
        import traceback
        traceback.print_exc()
        sys.exit(1)

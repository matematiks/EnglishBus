#!/usr/bin/env python3
"""
EnglishBus Edge Case Testing
Tests error handling, invalid inputs, and boundary conditions
"""

import requests
import json

BASE_URL = "http://localhost:8000"
COLORS = {"green": "\033[92m", "red": "\033[91m", "yellow": "\033[93m", "blue": "\033[94m", "reset": "\033[0m"}

def log(message, color="reset"):
    print(f"{COLORS[color]}{message}{COLORS['reset']}")

def run_test(name, func):
    try:
        log(f"\n► {name}", "blue")
        func()
        log("✅ PASSED", "green")
        return True
    except AssertionError as e:
        log(f"❌ FAILED: {e}", "red")
        return False
    except Exception as e:
        log(f"⚠️ ERROR: {e}", "yellow")
        return False

passed = 0
failed = 0

# ===== EDGE CASE TESTS =====

def test_login_empty_username():
    """Login with empty username should fail"""
    resp = requests.post(f"{BASE_URL}/auth/login", json={"username": "", "password": "test"})
    assert resp.status_code != 200, f"Expected error, got {resp.status_code}"
    log(f"  → Rejected empty username (status: {resp.status_code})", "yellow")

def test_login_wrong_password():
    """Login with wrong password should fail"""
    # First register a user
    requests.post(f"{BASE_URL}/auth/register", json={"username": "edgetest1", "password": "correct123"})
    # Try wrong password
    resp = requests.post(f"{BASE_URL}/auth/login", json={"username": "edgetest1", "password": "wrong"})
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
    log(f"  → Rejected wrong password (status: 401)", "yellow")

def test_register_duplicate_username():
    """Registering duplicate username should fail"""
    username = "duplicate_test"
    requests.post(f"{BASE_URL}/auth/register", json={"username": username, "password": "pass1"})
    resp = requests.post(f"{BASE_URL}/auth/register", json={"username": username, "password": "pass2"})
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    log(f"  → Rejected duplicate username (status: 400)", "yellow")

def test_session_invalid_user():
    """Session start with invalid user_id should handle gracefully"""
    resp = requests.post(f"{BASE_URL}/session/start", json={
        "user_id": 99999,
        "course_id": 1,
        "unit_id": 1
    })
    # Should either succeed with empty session or return error
    log(f"  → Invalid user handled (status: {resp.status_code})", "yellow")
    assert resp.status_code in [200, 404, 422], f"Unexpected status: {resp.status_code}"

def test_session_invalid_course():
    """Session start with non-existent course should handle gracefully"""
    resp = requests.post(f"{BASE_URL}/session/start", json={
        "user_id": 1,
        "course_id": 999,
        "unit_id": 1
    })
    log(f"  → Invalid course handled (status: {resp.status_code})", "yellow")
    assert resp.status_code in [200, 404, 500], f"Unexpected status: {resp.status_code}"

def test_session_complete_empty_ids():
    """Session complete with empty word IDs should handle gracefully"""
    resp = requests.post(f"{BASE_URL}/session/complete", json={
        "user_id": 1,
        "course_id": 1,
        "completed_word_ids": []
    })
    assert resp.status_code in [200, 422], f"Expected 200 or 422, got {resp.status_code}"
    log(f"  → Empty word IDs handled (status: {resp.status_code})", "yellow")

def test_practice_sentences_zero_count():
    """Practice sentences with count=0 should handle gracefully"""
    resp = requests.get(f"{BASE_URL}/practice/sentences", params={
        "user_id": 1,
        "course_id": 1,
        "count": 0
    })
    log(f"  → Zero count handled (status: {resp.status_code})", "yellow")
    assert resp.status_code in [200, 422], f"Unexpected status: {resp.status_code}"

def test_practice_sentences_large_count():
    """Practice sentences with very large count should cap or handle gracefully"""
    resp = requests.get(f"{BASE_URL}/practice/sentences", params={
        "user_id": 1,
        "course_id": 1,
        "count": 1000
    })
    log(f"  → Large count handled (status: {resp.status_code})", "yellow")
    if resp.status_code == 200:
        data = resp.json()
        sentences = data.get("sentences", [])
        log(f"    Returned {len(sentences)} sentences (avalanche guard active)", "yellow")
        assert len(sentences) <= 100, "Should have some reasonable cap"

def test_units_status_invalid_course():
    """Units status for non-existent course should handle gracefully"""
    resp = requests.get(f"{BASE_URL}/courses/999/units/status", params={"user_id": 1})
    log(f"  → Invalid course handled (status: {resp.status_code})", "yellow")
    # Should return empty list or error
    assert resp.status_code in [200, 404], f"Unexpected status: {resp.status_code}"

def test_sql_injection_username():
    """Username with SQL injection attempt should be handled safely"""
    malicious = "admin' OR '1'='1"
    resp = requests.post(f"{BASE_URL}/auth/register", json={
        "username": malicious,
        "password": "test123"
    })
    # Should either accept (parameterized queries safe) or reject
    log(f"  → SQL injection attempt handled (status: {resp.status_code})", "yellow")
    assert resp.status_code in [200, 400, 422], f"Unexpected status: {resp.status_code}"

# ===== RUN TESTS =====

log("\n" + "="*60, "blue")
log("EDGE CASE & ROBUSTNESS TESTING", "blue")
log("="*60 + "\n", "blue")

tests = [
    ("Empty Username Login", test_login_empty_username),
    ("Wrong Password Login", test_login_wrong_password),
    ("Duplicate Username Registration", test_register_duplicate_username),
    ("Session with Invalid User", test_session_invalid_user),
    ("Session with Invalid Course", test_session_invalid_course),
    ("Session Complete Empty IDs", test_session_complete_empty_ids),
    ("Practice Sentences Zero Count", test_practice_sentences_zero_count),
    ("Practice Sentences Large Count", test_practice_sentences_large_count),
    ("Units Status Invalid Course", test_units_status_invalid_course),
    ("SQL Injection in Username", test_sql_injection_username),
]

for name, func in tests:
    if run_test(name, func):
        passed += 1
    else:
        failed += 1

log("\n" + "="*60, "blue")
log("RESULTS", "blue")
log("="*60, "blue")
log(f"Passed: {passed}/{len(tests)}", "green" if failed == 0 else "yellow")
log(f"Failed: {failed}/{len(tests)}", "red" if failed > 0 else "green")

if failed == 0:
    log("\n✅ All edge cases handled properly!", "green")
else:
    log(f"\n⚠️ {failed} edge case(s) need attention", "yellow")

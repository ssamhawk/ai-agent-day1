#!/usr/bin/env python3
"""Test field validation after security fixes"""

import requests

BASE_URL = "http://127.0.0.1:5002"

def test_invalid_field_names():
    """Test that invalid field names are rejected"""
    print("\n=== Testing Invalid Field Names ===")

    # Get CSRF token first
    session = requests.Session()
    csrf_response = session.get(f"{BASE_URL}/api/csrf-token")
    csrf_token = csrf_response.json()['csrf_token']
    headers = {'X-CSRFToken': csrf_token}

    # Test 1: Field starting with number
    response = session.post(f"{BASE_URL}/api/chat",
        json={
            "message": "test",
            "format": "json",
            "fields": ["123invalid"]
        },
        headers=headers
    )
    print(f"1. Field starting with number: {response.status_code} - Expected 400 - {'✅ PASS' if response.status_code == 400 else '❌ FAIL'}")

    # Test 2: Field with spaces
    response = session.post(f"{BASE_URL}/api/chat",
        json={
            "message": "test",
            "format": "json",
            "fields": ["invalid field"]
        },
        headers=headers
    )
    print(f"2. Field with spaces: {response.status_code} - Expected 400 - {'✅ PASS' if response.status_code == 400 else '❌ FAIL'}")

    # Test 3: Field with special characters
    response = session.post(f"{BASE_URL}/api/chat",
        json={
            "message": "test",
            "format": "json",
            "fields": ["invalid-field"]
        },
        headers=headers
    )
    print(f"3. Field with dash: {response.status_code} - Expected 400 - {'✅ PASS' if response.status_code == 400 else '❌ FAIL'}")


def test_valid_field_names():
    """Test that valid field names are accepted"""
    print("\n=== Testing Valid Field Names ===")

    # Get CSRF token
    session = requests.Session()
    csrf_response = session.get(f"{BASE_URL}/api/csrf-token")
    csrf_token = csrf_response.json()['csrf_token']
    headers = {'X-CSRFToken': csrf_token}

    response = session.post(f"{BASE_URL}/api/chat",
        json={
            "message": "What is Python?",
            "format": "json",
            "fields": ["answer", "category", "my_custom_field"]
        },
        headers=headers
    )
    print(f"Valid fields: {response.status_code}")
    if response.status_code == 200:
        print("✅ Valid field names accepted")
    else:
        print(f"❌ Error: {response.json()}")


def test_csrf_protection():
    """Test CSRF token"""
    print("\n=== Testing CSRF Protection ===")

    # Get CSRF token
    response = requests.get(f"{BASE_URL}/api/csrf-token")
    data = response.json()
    print(f"CSRF token received: {data.get('csrf_token')[:20]}...")


def test_security_headers():
    """Test security headers"""
    print("\n=== Testing Security Headers ===")

    response = requests.get(BASE_URL)
    headers = response.headers

    security_headers = [
        'Content-Security-Policy',
        'X-Content-Type-Options',
        'X-Frame-Options',
        'X-XSS-Protection',
        'Referrer-Policy'
    ]

    for header in security_headers:
        if header in headers:
            print(f"✅ {header}: {headers[header][:50]}...")
        else:
            print(f"❌ {header}: Missing")


if __name__ == "__main__":
    print("🔒 Testing Security Fixes\n")

    test_security_headers()
    test_csrf_protection()
    test_invalid_field_names()
    test_valid_field_names()

    print("\n✨ Tests completed!")

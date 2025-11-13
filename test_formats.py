#!/usr/bin/env python3
"""Test all response formats for Day 2 AI Configuration"""

import requests
import json

BASE_URL = "http://127.0.0.1:5002"

def test_format(format_name):
    """Test a specific response format"""
    print(f"\n{'='*60}")
    print(f"Testing {format_name.upper()} format")
    print(f"{'='*60}")

    payload = {
        "message": "What is Python?",
        "format": format_name
    }

    try:
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        data = response.json()

        if data.get('success'):
            print(f"✅ Success!")
            print(f"\nFormat: {data.get('format')}")
            print(f"\nResponse:\n{data.get('response')}")

            if data.get('parsed'):
                print(f"\n📦 Parsed JSON:")
                print(json.dumps(data.get('parsed'), indent=2))
        else:
            print(f"❌ Error: {data.get('error')}")

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    formats = ['plain', 'json', 'markdown', 'xml']

    print("🚀 Testing Day 2 AI Configuration - All Formats")
    print(f"Server: {BASE_URL}")

    for fmt in formats:
        test_format(fmt)
        print()

    print("\n✨ All tests completed!")

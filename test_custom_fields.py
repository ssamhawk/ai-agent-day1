#!/usr/bin/env python3
"""Test custom fields configuration for Day 2 AI Configuration"""

import requests
import json

BASE_URL = "http://127.0.0.1:5002"

def test_custom_fields():
    """Test JSON format with custom fields"""
    print(f"\n{'='*60}")
    print(f"Testing JSON with Custom Fields")
    print(f"{'='*60}")

    # Test with custom fields: answer, category, examples, best_practices
    payload = {
        "message": "What is Python?",
        "format": "json",
        "fields": ["answer", "category", "examples", "best_practices"]
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


def test_xml_custom_fields():
    """Test XML format with custom fields"""
    print(f"\n{'='*60}")
    print(f"Testing XML with Custom Fields")
    print(f"{'='*60}")

    # Test with custom fields including sources and related_topics
    payload = {
        "message": "Explain machine learning",
        "format": "xml",
        "fields": ["answer", "category", "sources", "related_topics"]
    }

    try:
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        data = response.json()

        if data.get('success'):
            print(f"✅ Success!")
            print(f"\nFormat: {data.get('format')}")
            print(f"\nResponse:\n{data.get('response')}")
        else:
            print(f"❌ Error: {data.get('error')}")

    except Exception as e:
        print(f"❌ Exception: {e}")


def test_minimal_fields():
    """Test with minimal fields (answer only)"""
    print(f"\n{'='*60}")
    print(f"Testing JSON with Minimal Fields (answer only)")
    print(f"{'='*60}")

    payload = {
        "message": "What is JavaScript?",
        "format": "json",
        "fields": ["answer"]
    }

    try:
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        data = response.json()

        if data.get('success'):
            print(f"✅ Success!")
            print(f"\nResponse:\n{data.get('response')}")

            if data.get('parsed'):
                print(f"\n📦 Parsed JSON:")
                print(json.dumps(data.get('parsed'), indent=2))
        else:
            print(f"❌ Error: {data.get('error')}")

    except Exception as e:
        print(f"❌ Exception: {e}")


if __name__ == "__main__":
    print("🚀 Testing Day 2 AI Configuration - Custom Fields")
    print(f"Server: {BASE_URL}")

    test_custom_fields()
    print()

    test_xml_custom_fields()
    print()

    test_minimal_fields()
    print()

    print("\n✨ All tests completed!")

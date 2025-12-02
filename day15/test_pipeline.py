"""
Test script for Day 10 Pipeline Agent
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:5010"

def test_write_file():
    """Test write_file tool directly"""
    print("\n" + "="*70)
    print("TEST 1: Direct write_file tool call")
    print("="*70)

    # Get CSRF token
    csrf_response = requests.get(f"{BASE_URL}/api/csrf-token")
    csrf_token = csrf_response.json()['csrf_token']

    # Create session to maintain cookies
    session = requests.Session()

    # Get CSRF token with session
    csrf_response = session.get(f"{BASE_URL}/api/csrf-token")
    csrf_token = csrf_response.json()['csrf_token']

    # Test write_file
    response = session.post(
        f"{BASE_URL}/api/mcp/call",
        headers={'X-CSRFToken': csrf_token},
        json={
            "server_name": "filesystem",
            "tool_name": "write_file",
            "arguments": {
                "path": "/Users/viacheslavskrynnyk/projects/ai-challange/day10/test_outputs/test_write.txt",
                "content": "Hello from write_file tool test!\nThis file was created by MCP."
            }
        }
    )

    result = response.json()
    print(f"Status: {'✅ SUCCESS' if result.get('success') else '❌ FAILED'}")
    print(f"Result: {json.dumps(result, indent=2)}")

    return result.get('success', False)


def test_pipeline_agent():
    """Test pipeline agent with search → summarize → save"""
    print("\n" + "="*70)
    print("TEST 2: Pipeline Agent - Search → Summarize → Save")
    print("="*70)

    # Create session
    session = requests.Session()

    # Get CSRF token
    csrf_response = session.get(f"{BASE_URL}/api/csrf-token")
    csrf_token = csrf_response.json()['csrf_token']

    # Test pipeline
    query = "Search for Python 3.12 new features and save a summary to /Users/viacheslavskrynnyk/projects/ai-challange/day10/test_outputs/python_3.12_summary.md"

    print(f"\nQuery: {query}")
    print("\nExecuting pipeline...")

    response = session.post(
        f"{BASE_URL}/api/pipeline/execute",
        headers={'X-CSRFToken': csrf_token},
        json={
            "query": query,
            "temperature": 0.7
        }
    )

    result = response.json()

    print(f"\nStatus: {'✅ SUCCESS' if result.get('success') else '❌ FAILED'}")
    print(f"\nTotal Steps: {result.get('total_steps', 0)}")
    print(f"Tools Used: {', '.join(result.get('tools_used', []))}")

    if result.get('steps'):
        print("\nPipeline Steps:")
        for step in result['steps']:
            icon = '✅' if step.get('success') else '❌'
            cmd_type = step.get('command', {}).get('type', 'unknown')
            print(f"  {icon} Step {step.get('step')}: {cmd_type}")

    if result.get('errors'):
        print("\nErrors:")
        for err in result['errors']:
            print(f"  ⚠️ Step {err.get('step')}: {err.get('error')}")

    print(f"\nFinal Answer:\n{result.get('answer', 'No answer')[:200]}...")

    return result.get('success', False)


def test_read_created_file():
    """Read the file created by pipeline"""
    print("\n" + "="*70)
    print("TEST 3: Verify created file")
    print("="*70)

    file_path = "/Users/viacheslavskrynnyk/projects/ai-challange/day10/test_outputs/python_3.12_summary.md"

    try:
        with open(file_path, 'r') as f:
            content = f.read()
        print(f"✅ File exists: {file_path}")
        print(f"Content length: {len(content)} characters")
        print(f"\nFirst 300 characters:")
        print("-" * 70)
        print(content[:300])
        print("-" * 70)
        return True
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n🚀 Day 10 Pipeline Agent Test Suite")
    print("="*70)

    # Wait for server to be ready
    print("\nWaiting for server to be ready...")
    time.sleep(2)

    results = []

    # Test 1: Direct write_file
    try:
        results.append(("Write File Tool", test_write_file()))
    except Exception as e:
        print(f"❌ Test 1 failed: {str(e)}")
        results.append(("Write File Tool", False))

    time.sleep(1)

    # Test 2: Pipeline agent
    try:
        results.append(("Pipeline Agent", test_pipeline_agent()))
    except Exception as e:
        print(f"❌ Test 2 failed: {str(e)}")
        results.append(("Pipeline Agent", False))

    time.sleep(1)

    # Test 3: Verify file
    try:
        results.append(("Verify Created File", test_read_created_file()))
    except Exception as e:
        print(f"❌ Test 3 failed: {str(e)}")
        results.append(("Verify Created File", False))

    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Day 10 Pipeline Agent is working!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")

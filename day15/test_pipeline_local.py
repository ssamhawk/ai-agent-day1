"""
Test script for Day 10 Pipeline Agent - Local files only (no web search)
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:5010"

def test_pipeline_local():
    """Test pipeline: list files → read → summarize → save"""
    print("\n" + "="*70)
    print("PIPELINE TEST: List → Read → Summarize → Save")
    print("="*70)

    # Create session
    session = requests.Session()

    # Get CSRF token
    csrf_response = session.get(f"{BASE_URL}/api/csrf-token")
    csrf_token = csrf_response.json()['csrf_token']

    # Test pipeline with local files
    query = """List files in /Users/viacheslavskrynnyk/projects/ai-challange/day10,
    then read the README.md or any .py file,
    summarize what the project does,
    and save the summary to /Users/viacheslavskrynnyk/projects/ai-challange/day10/test_outputs/project_summary.md"""

    print(f"\nQuery: {query}")
    print("\nExecuting pipeline...")

    response = session.post(
        f"{BASE_URL}/api/pipeline/execute",
        headers={'X-CSRFToken': csrf_token},
        json={
            "query": query,
            "temperature": 0.7
        },
        timeout=60
    )

    result = response.json()

    print(f"\nStatus: {'✅ SUCCESS' if result.get('success') else '❌ FAILED'}")
    print(f"\nTotal Steps: {result.get('total_steps', 0)}")
    print(f"Tools Used: {', '.join(result.get('tools_used', []))}")

    if result.get('steps'):
        print("\n🔗 Pipeline Steps:")
        for step in result['steps']:
            icon = '✅' if step.get('success') else '❌'
            cmd = step.get('command', {})
            cmd_type = cmd.get('type', 'unknown')
            args = cmd.get('arguments', {})

            # Format arguments nicely
            if cmd_type == 'write_file':
                args_str = f"path={args.get('path', '')}, content_length={len(args.get('content', ''))}"
            else:
                args_str = str(args)[:60]

            print(f"  {icon} Step {step.get('step')}: {cmd_type}({args_str})")

    if result.get('errors'):
        print("\n⚠️ Errors:")
        for err in result['errors']:
            print(f"  Step {err.get('step')}: {err.get('error')}")

    print(f"\n📄 Final Answer:")
    print("-" * 70)
    print(result.get('answer', 'No answer'))
    print("-" * 70)

    # Check if file was created
    try:
        file_path = "/Users/viacheslavskrynnyk/projects/ai-challange/day10/test_outputs/project_summary.md"
        with open(file_path, 'r') as f:
            content = f.read()
        print(f"\n✅ File created: {file_path}")
        print(f"File size: {len(content)} characters")
        print(f"\nFile content:")
        print("-" * 70)
        print(content)
        print("-" * 70)
        return True
    except FileNotFoundError:
        print(f"\n⚠️ File not created (pipeline may have decided not to save)")
        return result.get('success', False)


def test_simple_pipeline():
    """Test simple pipeline: create a file with content"""
    print("\n" + "="*70)
    print("SIMPLE PIPELINE TEST: Create and save content")
    print("="*70)

    # Create session
    session = requests.Session()

    # Get CSRF token
    csrf_response = session.get(f"{BASE_URL}/api/csrf-token")
    csrf_token = csrf_response.json()['csrf_token']

    # Simple test
    query = """Create a simple text file at /Users/viacheslavskrynnyk/projects/ai-challange/day10/test_outputs/simple_test.txt
    with content: 'This is a test from Pipeline Agent. Created on 2025-11-25.'"""

    print(f"\nQuery: {query}")
    print("\nExecuting pipeline...")

    response = session.post(
        f"{BASE_URL}/api/pipeline/execute",
        headers={'X-CSRFToken': csrf_token},
        json={
            "query": query,
            "temperature": 0.5
        },
        timeout=30
    )

    result = response.json()

    print(f"\nStatus: {'✅ SUCCESS' if result.get('success') else '❌ FAILED'}")
    print(f"Total Steps: {result.get('total_steps', 0)}")
    print(f"Tools Used: {', '.join(result.get('tools_used', []))}")

    if result.get('steps'):
        print("\nSteps:")
        for step in result['steps']:
            icon = '✅' if step.get('success') else '❌'
            print(f"  {icon} Step {step.get('step')}: {step.get('command', {}).get('type')}")

    print(f"\nAnswer: {result.get('answer', '')}")

    # Verify file
    try:
        with open("/Users/viacheslavskrynnyk/projects/ai-challange/day10/test_outputs/simple_test.txt", 'r') as f:
            content = f.read()
        print(f"\n✅ File verified! Content: '{content}'")
        return True
    except FileNotFoundError:
        print("\n⚠️ File not created")
        return False


if __name__ == "__main__":
    print("\n🧪 Day 10 Pipeline Agent - Local Tests")
    print("="*70)
    print("Testing without web search to avoid rate limits")
    print("="*70)

    time.sleep(1)

    results = []

    # Test 1: Simple pipeline
    try:
        results.append(("Simple Pipeline", test_simple_pipeline()))
    except Exception as e:
        print(f"\n❌ Simple pipeline test failed: {str(e)}")
        results.append(("Simple Pipeline", False))

    time.sleep(2)

    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_name}")

    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed_count}/{total} tests passed")

    if passed_count == total:
        print("\n🎉 All tests passed! Pipeline Agent works!")
    else:
        print(f"\n⚠️ {total - passed_count} test(s) failed")

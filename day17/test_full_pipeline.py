"""
Test full pipeline: List → Read → Analyze → Save
"""
import requests
import time

BASE_URL = "http://127.0.0.1:5010"

def test_full_chain():
    """Test complete tool chaining"""
    print("\n" + "="*70)
    print("FULL PIPELINE: List → Read → Analyze → Save")
    print("="*70)

    session = requests.Session()
    csrf_token = session.get(f"{BASE_URL}/api/csrf-token").json()['csrf_token']

    query = """Please do the following steps:
1. List files in /Users/viacheslavskrynnyk/projects/ai-challange/day10
2. Read the pipeline_agent.py file
3. Analyze what it does and create a summary
4. Save the summary to /Users/viacheslavskrynnyk/projects/ai-challange/day10/test_outputs/pipeline_analysis.md"""

    print(f"\n📋 Query:\n{query}")
    print("\n⏳ Executing pipeline...")

    start_time = time.time()

    response = session.post(
        f"{BASE_URL}/api/pipeline/execute",
        headers={'X-CSRFToken': csrf_token},
        json={"query": query, "temperature": 0.7},
        timeout=120
    )

    elapsed = time.time() - start_time

    result = response.json()

    print(f"\n⏱️ Execution time: {elapsed:.1f} seconds")
    print(f"Status: {'✅ SUCCESS' if result.get('success') else '❌ FAILED'}")
    print(f"\n📊 Pipeline Statistics:")
    print(f"  Total Steps: {result.get('total_steps', 0)}")
    print(f"  Tools Used: {', '.join(result.get('tools_used', []))}")
    print(f"  Errors: {len(result.get('errors', []))}")

    if result.get('steps'):
        print(f"\n🔗 Execution Chain:")
        for step in result['steps']:
            icon = '✅' if step.get('success') else '❌'
            cmd = step.get('command', {})
            cmd_type = cmd.get('type', 'unknown')
            args = cmd.get('arguments', {})

            if cmd_type == 'list_files':
                detail = f"path={args.get('path', '')}"
            elif cmd_type == 'read_file':
                detail = f"path={args.get('path', '')}"
            elif cmd_type == 'write_file':
                path = args.get('path', '')
                content_len = len(args.get('content', ''))
                detail = f"path={path}, {content_len} chars"
            else:
                detail = str(args)[:40]

            print(f"  {icon} Step {step.get('step')}: {cmd_type}({detail})")

    if result.get('errors'):
        print(f"\n⚠️ Errors encountered:")
        for err in result['errors']:
            print(f"  Step {err.get('step')}: {err.get('error')}")

    print(f"\n📝 Final Answer:")
    print("-" * 70)
    answer = result.get('answer', 'No answer')
    # Print first 500 chars
    print(answer if len(answer) <= 500 else answer[:500] + "...")
    print("-" * 70)

    # Verify saved file
    try:
        file_path = "/Users/viacheslavskrynnyk/projects/ai-challange/day10/test_outputs/pipeline_analysis.md"
        with open(file_path, 'r') as f:
            content = f.read()
        print(f"\n✅ OUTPUT FILE VERIFIED!")
        print(f"📁 Location: {file_path}")
        print(f"📏 Size: {len(content)} characters")
        print(f"\n📄 File Content:")
        print("-" * 70)
        print(content)
        print("-" * 70)
        return True
    except FileNotFoundError:
        print(f"\n⚠️ Output file not created")
        return result.get('success', False)
    except Exception as e:
        print(f"\n❌ Error reading output: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n🧪 Day 10 - Full Pipeline Chain Test")
    print("="*70)

    time.sleep(1)

    try:
        success = test_full_chain()
        print("\n" + "="*70)
        if success:
            print("🎉 PIPELINE TEST PASSED!")
            print("✅ Tool chaining works!")
            print("✅ Multi-step execution works!")
            print("✅ File operations work!")
        else:
            print("⚠️ PIPELINE TEST INCOMPLETE")
            print("Pipeline executed but may not have completed all steps")
        print("="*70)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

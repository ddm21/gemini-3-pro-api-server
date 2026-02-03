"""
Test script for code execution feature.

This script tests the new code execution functionality with different configurations.
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Get API key from environment
SERVER_API_KEY = os.getenv("SERVER_API_KEY")
BASE_URL = "http://localhost:8000"

def test_code_execution_with_high_thinking():
    """Test code execution enabled with HIGH thinking level (optimal)."""
    print("\n" + "="*60)
    print("TEST 1: Code execution ON + HIGH thinking level")
    print("="*60)
    
    payload = {
        "user_prompt": "Calculate the factorial of 10",
        "enable_code_execution": True,
        "thinking_level": "HIGH"
    }
    
    response = requests.post(
        f"{BASE_URL}/generate",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": SERVER_API_KEY
        },
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    # Verify code execution metadata is present
    if "code_execution_metadata" in result:
        metadata = result["code_execution_metadata"]
        print(f"\n✅ Code execution metadata present:")
        print(f"   - Executed: {metadata.get('executed')}")
        print(f"   - Execution count: {metadata.get('execution_count')}")
        if metadata.get('code_snippets'):
            print(f"   - Code snippets: {len(metadata['code_snippets'])} snippet(s)")
            for i, snippet in enumerate(metadata['code_snippets'], 1):
                print(f"     Snippet {i}: {snippet[:80]}...")
        if metadata.get('execution_results'):
            print(f"   - Results: {len(metadata['execution_results'])} result(s)")
            for i, result_text in enumerate(metadata['execution_results'], 1):
                print(f"     Result {i}: {result_text[:80]}...")
    else:
        print("\n⚠️  No code execution metadata (model may not have used code execution)")
    
    if "warning" in result:
        print(f"⚠️  WARNING PRESENT: {result['warning']}")
    else:
        print("✅ No warning (expected for optimal config)")
    
    return response.status_code == 200


def test_code_execution_with_low_thinking():
    """Test code execution enabled with LOW thinking level (suboptimal)."""
    print("\n" + "="*60)
    print("TEST 2: Code execution ON + LOW thinking level")
    print("="*60)
    
    payload = {
        "user_prompt": "Calculate the factorial of 10",
        "enable_code_execution": True,
        "thinking_level": "LOW"
    }
    
    response = requests.post(
        f"{BASE_URL}/generate",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": SERVER_API_KEY
        },
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    # Verify code execution metadata is present
    if "code_execution_metadata" in result:
        metadata = result["code_execution_metadata"]
        print(f"\n✅ Code execution metadata present:")
        print(f"   - Executed: {metadata.get('executed')}")
        print(f"   - Execution count: {metadata.get('execution_count')}")
    else:
        print("\n⚠️  No code execution metadata")
    
    if "warning" in result:
        print(f"⚠️  WARNING PRESENT (expected): {result['warning']}")
    else:
        print("❌ No warning (unexpected - should warn about thinking level)")
    
    return response.status_code == 200 and "warning" in result


def test_code_execution_disabled():
    """Test with code execution disabled (backward compatibility)."""
    print("\n" + "="*60)
    print("TEST 3: Code execution OFF (backward compatibility)")
    print("="*60)
    
    payload = {
        "user_prompt": "What is 2+2?",
        "enable_code_execution": False
    }
    
    response = requests.post(
        f"{BASE_URL}/generate",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": SERVER_API_KEY
        },
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if "warning" in result:
        print(f"⚠️  WARNING PRESENT (unexpected): {result['warning']}")
    else:
        print("✅ No warning (expected for disabled code execution)")
    
    return response.status_code == 200


def test_default_behavior():
    """Test default behavior (code execution not specified)."""
    print("\n" + "="*60)
    print("TEST 4: Default behavior (no enable_code_execution param)")
    print("="*60)
    
    payload = {
        "user_prompt": "What is 2+2?"
    }
    
    response = requests.post(
        f"{BASE_URL}/generate",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": SERVER_API_KEY
        },
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    return response.status_code == 200


if __name__ == "__main__":
    if not SERVER_API_KEY:
        print("❌ ERROR: SERVER_API_KEY not found in .env file")
        exit(1)
    
    print("\n🧪 Testing Code Execution Feature Implementation")
    print(f"Server: {BASE_URL}")
    
    results = []
    
    try:
        results.append(("Test 1: Optimal config", test_code_execution_with_high_thinking()))
        results.append(("Test 2: Suboptimal config", test_code_execution_with_low_thinking()))
        results.append(("Test 3: Disabled", test_code_execution_disabled()))
        results.append(("Test 4: Default", test_default_behavior()))
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed")

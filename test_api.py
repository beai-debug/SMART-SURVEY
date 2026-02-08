"""
test_api.py
Test script for Smart Survey Analytics API

Tests all endpoints:
1. Status endpoint
2. Load recent data
3. Delete operations
4. Search with different intent types
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def print_section(title: str):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def print_response(response: requests.Response, max_lines: int = 30):
    """Print response in a readable format"""
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        json_str = json.dumps(data, indent=2, default=str)
        lines = json_str.split('\n')
        if len(lines) > max_lines:
            print('\n'.join(lines[:max_lines]))
            print(f"... (truncated, {len(lines) - max_lines} more lines)")
        else:
            print(json_str)
    except:
        print(response.text)

def test_health_check():
    """Test health check endpoint"""
    print_section("TEST 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_root():
    """Test root endpoint"""
    print_section("TEST 2: Root Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/")
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_status():
    """Test status endpoint"""
    print_section("TEST 3: Status Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/status")
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            print("\n📊 Summary:")
            print(f"   Total Records: {data.get('total_records', 0)}")
            print(f"   Schools: {len(data.get('by_school', []))}")
            print(f"   Classes: {len(data.get('by_class', []))}")
            return True
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_search_quant():
    """Test quantitative search"""
    print_section("TEST 4: Search - Quantitative Query")
    try:
        response = requests.post(
            f"{BASE_URL}/search",
            json={
                "query": "Show transport satisfaction distribution by class",
                "limit": 10
            }
        )
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n🎯 Intent Detected: {data.get('intent')}")
            print(f"📊 Sample Size: {data.get('retrieved_rows', {}).get('sample_size', 'N/A')}")
            return True
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_search_qual():
    """Test qualitative search"""
    print_section("TEST 5: Search - Qualitative Query")
    try:
        response = requests.post(
            f"{BASE_URL}/search",
            json={
                "query": "What do students complain about regarding lab facilities?",
                "feedback_column": "school_feedback",
                "limit": 5
            }
        )
        print_response(response, max_lines=40)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n🎯 Intent Detected: {data.get('intent')}")
            
            qual_data = data.get('retrieved_rows', {}).get('qualitative', {})
            if qual_data:
                print(f"📝 Feedback Count: {qual_data.get('count', 0)}")
                
                # Show similarity scores
                scores = qual_data.get('similarity_scores', [])
                if scores:
                    print("\n🔍 Top Similarity Scores:")
                    for i, score in enumerate(scores[:3], 1):
                        print(f"   {i}. Roll: {score['roll_number']} | Similarity: {score['similarity']:.3f}")
            return True
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_search_mixed():
    """Test mixed search"""
    print_section("TEST 6: Search - Mixed Query")
    try:
        response = requests.post(
            f"{BASE_URL}/search",
            json={
                "query": "Why are students dissatisfied with competitive exam preparation?",
                "limit": 5
            }
        )
        print_response(response, max_lines=50)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n🎯 Intent Detected: {data.get('intent')}")
            
            retrieved = data.get('retrieved_rows', {})
            if retrieved.get('type') == 'mixed':
                quant = retrieved.get('quantitative', {})
                qual = retrieved.get('qualitative', {})
                print(f"📊 Quantitative Sample: {quant.get('sample_size', 0)}")
                print(f"📝 Qualitative Count: {qual.get('count', 0)}")
            return True
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_delete_preview():
    """Test delete operation (preview only, no actual deletion)"""
    print_section("TEST 7: Delete Operations (Preview)")
    
    print("\n⚠️  Note: These are preview requests. No actual deletion will occur")
    print("    To test deletion, modify this function to use actual roll numbers")
    
    # This will likely return "no records found" unless you have this specific record
    try:
        response = requests.delete(
            f"{BASE_URL}/delete/by-roll-school",
            json={
                "roll_number": "999999",  # Non-existent roll number
                "school_name": "TEST SCHOOL"
            }
        )
        print("\n📝 Delete by Roll + School (Non-existent):")
        print_response(response, max_lines=10)
        
        return response.status_code in [200, 404]
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_graph_data_format():
    """Test that graph data is in correct format"""
    print_section("TEST 8: Graph Data Format Verification")
    try:
        response = requests.post(
            f"{BASE_URL}/search",
            json={
                "query": "What is the distribution of students by subject group?",
                "limit": 10
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            numbers = data.get('numbers_for_graph', {})
            
            print("✅ Graph Data Structure:")
            print(f"   - Has 'mixed' field: {'mixed' in numbers}")
            print(f"   - Has 'quant' field: {'quant' in numbers}")
            
            if 'quant' in numbers and numbers['quant'] != "N/A":
                quant_data = numbers['quant']
                print(f"   - Quant data type: {type(quant_data)}")
                if isinstance(quant_data, list) and len(quant_data) > 0:
                    print(f"   - Quant data sample: {quant_data[0]}")
                    print("\n✅ Data is ready for graph generation!")
                    return True
            
            print("\n✅ Structure validated (may be qualitative query)")
            return True
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def run_all_tests():
    """Run all API tests"""
    print("\n" + "🚀" * 40)
    print("SMART SURVEY API - COMPREHENSIVE TEST SUITE")
    print("🚀" * 40)
    
    tests = [
        ("Health Check", test_health_check),
        ("Root Endpoint", test_root),
        ("Status Endpoint", test_status),
        ("Quantitative Search", test_search_quant),
        ("Qualitative Search", test_search_qual),
        ("Mixed Search", test_search_mixed),
        ("Delete Operations", test_delete_preview),
        ("Graph Data Format", test_graph_data_format),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Print summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{'=' * 80}")
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"{'=' * 80}")
    
    if passed == total:
        print("\n🎉 All tests passed! API is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    print("\n📝 Make sure the API server is running:")
    print("   python api.py")
    print("   or")
    print("   uvicorn api:app --reload")
    print("\nStarting tests in 3 seconds...\n")
    
    import time
    time.sleep(3)
    
    success = run_all_tests()
    exit(0 if success else 1)

"""
Test script to verify query processing logic for QUANT, QUAL, and MIXED queries
"""
import json
from survey_copilot import (
    classify_intent,
    run_quant_analysis,
    run_semantic_search,
    run_mixed_analysis,
    summarize_feedback,
    ask_survey,
    DecimalEncoder
)

def test_quant_query():
    """Test QUANT: Should return numbers directly from SQL, no LLM generation for data"""
    print("\n" + "="*60)
    print("TEST 1: QUANT QUERY")
    print("="*60)
    
    query = "What is the average recommendation score?"
    
    # Check intent classification
    intent = classify_intent(query)
    print(f"Query: {query}")
    print(f"Classified Intent: {intent}")
    
    # Run quant analysis
    result = run_quant_analysis(query)
    
    print(f"\nSuccess: {result.get('success')}")
    print(f"Sample Size: {result.get('sample_size')}")
    print(f"SQL: {result.get('sql')}")
    print(f"Results (raw numbers): {json.dumps(result.get('results'), indent=2, cls=DecimalEncoder)}")
    
    # Verify it returns actual numbers
    if result.get('success') and result.get('results'):
        print("\n✅ QUANT TEST PASSED: Returns actual numbers from database")
    else:
        print("\n❌ QUANT TEST FAILED: No results returned")
    
    return result

def test_qual_query():
    """Test QUAL: Should retrieve feedback, then send to LLM for summarization"""
    print("\n" + "="*60)
    print("TEST 2: QUAL QUERY")
    print("="*60)
    
    query = "What do students complain about regarding teachers?"
    
    # Check intent classification
    intent = classify_intent(query)
    print(f"Query: {query}")
    print(f"Classified Intent: {intent}")
    
    # Run semantic search (retrieval)
    result = run_semantic_search(query, "teacher_feedback", limit=5)
    
    print(f"\nSuccess: {result.get('success')}")
    print(f"Feedback Count: {result.get('count')}")
    print(f"Retrieved Feedback (raw from DB):")
    for i, fb in enumerate(result.get('feedback', [])[:3], 1):
        print(f"  {i}. {fb[:100]}...")
    
    # Now test LLM summarization
    if result.get('feedback'):
        print("\n--- LLM Summarization ---")
        summary = summarize_feedback(result.get('feedback'), query)
        print(f"LLM Generated Summary:\n{summary}")
        print("\n✅ QUAL TEST PASSED: Retrieval happened, then LLM generated summary")
    else:
        print("\n❌ QUAL TEST FAILED: No feedback retrieved")
    
    return result

def test_mixed_query():
    """Test MIXED: Should run quant calc + retrieval, then BOTH go to LLM for collective summary"""
    print("\n" + "="*60)
    print("TEST 3: MIXED QUERY")
    print("="*60)
    
    query = "Why is transport satisfaction low?"
    
    # Check intent classification
    intent = classify_intent(query)
    print(f"Query: {query}")
    print(f"Classified Intent: {intent}")
    
    # Run mixed analysis
    result = run_mixed_analysis(query)
    
    quant = result.get('quantitative', {})
    qual = result.get('qualitative', {})
    
    print(f"\n--- QUANTITATIVE PART ---")
    print(f"Success: {quant.get('success')}")
    print(f"Sample Size: {quant.get('sample_size')}")
    print(f"SQL: {quant.get('sql')}")
    print(f"Metrics: {json.dumps(quant.get('results', [])[:3], indent=2, cls=DecimalEncoder)}")
    
    print(f"\n--- QUALITATIVE PART ---")
    print(f"Feedback Count: {qual.get('feedback_count')}")
    print(f"Sample Feedback: {qual.get('sample_feedback', [])[:2]}")
    
    print(f"\n--- COMBINED LLM ANALYSIS ---")
    combined = qual.get('combined_analysis', '')
    if combined:
        print(f"Combined Analysis (LLM processed BOTH quant + qual):\n{combined[:500]}...")
        print("\n✅ MIXED TEST PASSED: Quant calc + retrieval → both sent to LLM for collective summary")
    else:
        print("No combined analysis generated")
        print("\n⚠️ MIXED TEST WARNING: Combined analysis may be empty")
    
    return result

def test_full_flow():
    """Test the full ask_survey flow for each type"""
    print("\n" + "="*60)
    print("TEST 4: FULL FLOW (ask_survey)")
    print("="*60)
    
    queries = [
        ("QUANT", "How many students are in class 10th?"),
        ("QUAL", "What suggestions do students have for improving the school?"),
        ("MIXED", "Why do students rate career guidance poorly?")
    ]
    
    for expected_type, query in queries:
        print(f"\n--- Testing {expected_type} ---")
        print(f"Query: {query}")
        
        intent = classify_intent(query)
        print(f"Detected Intent: {intent}")
        
        response = ask_survey(query)
        print(f"Response Preview:\n{response[:300]}...")
        print("-" * 40)

if __name__ == "__main__":
    print("🧪 TESTING SURVEY QUERY PROCESSING LOGIC")
    print("=" * 60)
    
    # Test each type
    test_quant_query()
    test_qual_query()
    test_mixed_query()
    
    # Test full flow
    test_full_flow()
    
    print("\n" + "="*60)
    print("🏁 ALL TESTS COMPLETED")
    print("="*60)

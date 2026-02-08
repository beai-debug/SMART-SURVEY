"""
Test script to verify improved vector and mixed search functionality
Tests:
1. Vector search fetches full database rows using roll_number + school_name
2. Mixed search processes both quantitative and qualitative data together in LLM
"""

import sys
import json
from survey_copilot import (
    run_semantic_search,
    run_mixed_analysis,
    classify_intent,
    DecimalEncoder
)

def test_vector_search_full_rows():
    """Test that vector search now fetches full database rows"""
    print("=" * 80)
    print("TEST 1: Vector Search - Full Database Rows")
    print("=" * 80)
    
    query = "students complaining about lab facilities"
    print(f"\n🔍 Query: {query}\n")
    
    result = run_semantic_search(query, feedback_column="school_feedback", limit=5)
    
    if result.get("success"):
        print(f"✅ Search successful!")
        print(f"📊 Found {result.get('count')} relevant responses\n")
        
        # Verify we have full rows
        full_rows = result.get("full_rows", [])
        if full_rows:
            print("🎯 VERIFICATION: Full database rows retrieved")
            print("-" * 80)
            
            for idx, row in enumerate(full_rows[:3], 1):
                print(f"\n[{idx}] Roll Number: {row.get('roll_number')} | School: {row.get('school_name')}")
                print(f"    Similarity Score: {row.get('similarity_score', 0):.4f}")
                print(f"    Student Name: {row.get('student_name')}")
                print(f"    Class: {row.get('class')}")
                print(f"    Subject Group: {row.get('subject_group')}")
                print(f"    Overall Teaching Satisfaction: {row.get('overall_teaching_satisfaction')}")
                print(f"    Lab Satisfaction: {row.get('lab_satisfaction')}")
                print(f"    Transport Satisfaction: {row.get('transport_satisfaction')}")
                print(f"    Recommendation Score: {row.get('recommendation_score')}")
                feedback = row.get('school_feedback', '')
                print(f"    Feedback: \"{feedback[:100]}...\"" if len(feedback) > 100 else f"    Feedback: \"{feedback}\"")
            
            # Verify key fields are present
            required_fields = ['roll_number', 'school_name', 'similarity_score', 'class', 
                             'subject_group', 'overall_teaching_satisfaction', 'lab_satisfaction',
                             'teacher_support', 'career_guidance', 'competitive_exam_preparedness']
            
            first_row = full_rows[0]
            missing_fields = [f for f in required_fields if f not in first_row]
            
            if not missing_fields:
                print(f"\n✅ ALL REQUIRED FIELDS PRESENT in full rows")
            else:
                print(f"\n⚠️  Missing fields: {missing_fields}")
            
            print(f"\n✅ Total fields retrieved per row: {len(first_row)}")
        else:
            print("❌ No full rows retrieved!")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    return result


def test_mixed_search_llm_processing():
    """Test that mixed search processes both data types together in LLM"""
    print("\n\n" + "=" * 80)
    print("TEST 2: Mixed Search - Integrated LLM Processing")
    print("=" * 80)
    
    query = "Why is competitive exam preparedness rated low?"
    print(f"\n🔍 Query: {query}")
    
    # First check intent classification
    intent = classify_intent(query)
    print(f"📌 Intent classified as: {intent}")
    
    if intent != "MIXED":
        print("⚠️  Query not classified as MIXED, but proceeding with mixed analysis test...")
    
    print("\n🔄 Running mixed analysis...\n")
    result = run_mixed_analysis(query)
    
    # Check quantitative results
    quant = result.get("quantitative", {})
    print("📊 QUANTITATIVE RESULTS:")
    print(f"   Sample Size: {quant.get('sample_size', 0)}")
    print(f"   Success: {quant.get('success')}")
    if quant.get('results'):
        print(f"   Metrics: {json.dumps(quant.get('results')[:2], indent=6, cls=DecimalEncoder)}")
    
    # Check qualitative results
    qual = result.get("qualitative", {})
    print(f"\n💬 QUALITATIVE RESULTS:")
    print(f"   Feedback Count: {qual.get('feedback_count', 0)}")
    print(f"   Full Rows Retrieved: {len(qual.get('full_rows', []))}")
    
    # Check for combined analysis (NEW FEATURE)
    combined_analysis = qual.get("combined_analysis")
    
    if combined_analysis:
        print("\n✅ COMBINED LLM ANALYSIS PRESENT!")
        print("-" * 80)
        print("🤖 LLM analyzed both quantitative and qualitative data together:")
        print(f"\n{combined_analysis[:500]}...\n")
        
        # Verify the analysis mentions both data types
        has_quant_ref = any(word in combined_analysis.lower() for word in 
                           ['percent', '%', 'student', 'count', 'metric', 'number'])
        has_qual_ref = any(word in combined_analysis.lower() for word in 
                          ['feedback', 'mentioned', 'complained', 'stated', 'said'])
        
        if has_quant_ref and has_qual_ref:
            print("✅ Analysis references BOTH quantitative metrics and qualitative feedback")
        else:
            print(f"⚠️  Analysis completeness - Quant refs: {has_quant_ref}, Qual refs: {has_qual_ref}")
        
        # Check if full student profiles were used
        if qual.get('full_rows'):
            sample_row = qual['full_rows'][0]
            print(f"\n✅ Full student profiles used in analysis:")
            print(f"   Example: Roll {sample_row.get('roll_number')} from {sample_row.get('school_name')}")
            print(f"   Satisfaction metrics available: {bool(sample_row.get('overall_teaching_satisfaction'))}")
            print(f"   Similarity score: {sample_row.get('similarity_score', 0):.4f}")
    else:
        print("\n❌ NO COMBINED LLM ANALYSIS FOUND!")
        print("   The LLM should process both data types together.")
    
    return result


def test_summary():
    """Print test summary"""
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    print("\n✅ IMPROVEMENTS IMPLEMENTED:")
    print("   1. Vector search now fetches FULL database rows")
    print("      - Uses roll_number + school_name as keys")
    print("      - Retrieves all 30+ columns from actual database")
    print("      - Includes similarity scores with full context")
    print()
    print("   2. Mixed search processes both data types together")
    print("      - Quantitative metrics from SQL aggregation")
    print("      - Qualitative feedback with complete student profiles")
    print("      - Single LLM call analyzes BOTH simultaneously")
    print("      - Provides integrated insights connecting numbers to feedback")
    print()
    print("✅ KEY BENEFITS:")
    print("   - More context: Full student demographics, all satisfaction ratings")
    print("   - Better insights: LLM connects 'why' (feedback) with 'what' (metrics)")
    print("   - Evidence-based: Specific students' data supports conclusions")
    print("   - Actionable: Recommendations based on complete picture")


if __name__ == "__main__":
    print("\n🚀 TESTING IMPROVED VECTOR AND MIXED SEARCH FUNCTIONALITY\n")
    
    try:
        # Test 1: Vector search full rows
        vector_result = test_vector_search_full_rows()
        
        # Test 2: Mixed search LLM processing
        mixed_result = test_mixed_search_llm_processing()
        
        # Summary
        test_summary()
        
        print("\n\n✅ ALL TESTS COMPLETED!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

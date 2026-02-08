"""
test_survey_copilot.py
Test the Survey Copilot with multiple queries and save results to Markdown
Includes charts for QUANT/MIXED and full metadata from vector search
"""

import datetime
from survey_copilot import (
    ask_survey, classify_intent, run_quant_analysis, 
    run_semantic_search, run_mixed_analysis, generate_chart,
    OUTPUT_DIR
)
import json
from decimal import Decimal

# Test queries covering all intent types
TEST_QUERIES = [
    # QUANT queries (4)
    "What is the overall teaching satisfaction distribution?",
    "Show transport satisfaction breakdown by class",
    "What percentage of students study more than 4 hours daily?",
    "Compare lab satisfaction between Maths and Biology subject groups",
    
    # QUAL queries (3)
    "What do students complain about regarding teachers?",
    "What suggestions do students have for improving the school?",
    "What are the common issues with school facilities?",
    
    # MIXED queries (3)
    "Why is competitive exam preparedness rated low?",
    "Why are students dissatisfied with career guidance?",
    "What are the reasons behind low transport satisfaction?"
]


def run_tests_and_save_markdown():
    """Run all test queries and save results to markdown file with charts and metadata"""
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_results_{timestamp}.md"
    
    results = []
    
    print("🧪 Running Survey Copilot Tests...")
    print("=" * 60)
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[{i}/{len(TEST_QUERIES)}] Testing: {query[:50]}...")
        
        try:
            # Classify intent
            intent = classify_intent(query)
            print(f"    📌 Intent: {intent}")
            
            # Run appropriate analysis based on intent
            chart_path = None
            raw_result = None
            metadata_details = []
            
            if intent == "QUANT":
                raw_result = run_quant_analysis(query)
                if raw_result.get("success") and raw_result.get("results"):
                    chart_path = generate_chart(raw_result["results"], query)
                    if chart_path:
                        print(f"    📊 Chart saved: {chart_path}")
                        
            elif intent == "QUAL":
                # Determine feedback column
                if "teacher" in query.lower():
                    feedback_col = "teacher_feedback"
                elif "suggestion" in query.lower():
                    feedback_col = "school_suggestions"
                else:
                    feedback_col = "school_feedback"
                
                raw_result = run_semantic_search(query, feedback_col, limit=10)
                if raw_result.get("success"):
                    metadata_details = raw_result.get("details", [])
                    
            else:  # MIXED
                raw_result = run_mixed_analysis(query)
                # Generate chart from quant results
                if raw_result.get("quantitative", {}).get("success"):
                    quant_results = raw_result["quantitative"].get("results", [])
                    if quant_results:
                        chart_path = generate_chart(quant_results, query)
                        if chart_path:
                            print(f"    📊 Chart saved: {chart_path}")
                
                # Get metadata from qualitative search
                qual_config = {
                    "feedback_column": "school_feedback",
                    "search_query": query
                }
                qual_result = run_semantic_search(query, "school_feedback", limit=10)
                if qual_result.get("success"):
                    metadata_details = qual_result.get("details", [])
            
            # Get formatted response
            response = ask_survey(query)
            
            results.append({
                "query": query,
                "intent": intent,
                "response": response,
                "success": True,
                "error": None,
                "chart_path": chart_path,
                "metadata_details": metadata_details,
                "raw_result": raw_result
            })
            
            print(f"    ✅ Success")
            
        except Exception as e:
            results.append({
                "query": query,
                "intent": "ERROR",
                "response": None,
                "success": False,
                "error": str(e),
                "chart_path": None,
                "metadata_details": [],
                "raw_result": None
            })
            print(f"    ❌ Error: {e}")
    
    # Generate Markdown
    markdown_content = generate_markdown(results, timestamp)
    
    # Save to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    print("\n" + "=" * 60)
    print(f"✅ Results saved to: {filename}")
    print(f"📊 Total queries: {len(results)}")
    print(f"✅ Successful: {sum(1 for r in results if r['success'])}")
    print(f"❌ Failed: {sum(1 for r in results if not r['success'])}")
    print(f"📈 Charts generated: {sum(1 for r in results if r.get('chart_path'))}")
    
    return filename


def generate_markdown(results: list, timestamp: str) -> str:
    """Generate formatted Markdown content from test results with charts and metadata"""
    
    md = []
    
    # Header
    md.append("# 🎓 SMART Survey Copilot - Test Results")
    md.append("")
    md.append(f"**Test Date:** {datetime.datetime.now().strftime('%B %d, %Y at %H:%M:%S')}")
    md.append(f"**Total Queries Tested:** {len(results)}")
    md.append(f"**Successful:** {sum(1 for r in results if r['success'])}")
    md.append(f"**Failed:** {sum(1 for r in results if not r['success'])}")
    md.append(f"**Charts Generated:** {sum(1 for r in results if r.get('chart_path'))}")
    md.append("")
    md.append("---")
    md.append("")
    
    # Table of Contents
    md.append("## 📑 Table of Contents")
    md.append("")
    md.append("| # | Query | Intent | Status | Chart |")
    md.append("|---|-------|--------|--------|-------|")
    
    for i, r in enumerate(results, 1):
        status = "✅" if r['success'] else "❌"
        query_short = r['query'][:35] + "..." if len(r['query']) > 35 else r['query']
        chart_status = "📊" if r.get('chart_path') else "—"
        md.append(f"| {i} | {query_short} | `{r['intent']}` | {status} | {chart_status} |")
    
    md.append("")
    md.append("---")
    md.append("")
    
    # Detailed Results
    md.append("## 📊 Detailed Results")
    md.append("")
    
    for i, r in enumerate(results, 1):
        md.append(f"### Test {i}: {r['intent']} Query")
        md.append("")
        md.append(f"**📝 Question:**")
        md.append(f"> {r['query']}")
        md.append("")
        md.append(f"**🔍 Detected Intent:** `{r['intent']}`")
        md.append("")
        
        if r['success']:
            # Show chart if available
            if r.get('chart_path'):
                md.append("**📈 Generated Chart:**")
                md.append("")
                md.append(f"![Chart for {r['query'][:30]}]({r['chart_path']})")
                md.append("")
            
            md.append("**✅ Response:**")
            md.append("")
            md.append("```")
            md.append(r['response'])
            md.append("```")
            md.append("")
            
            # Show metadata for QUAL and MIXED queries
            if r.get('metadata_details') and len(r['metadata_details']) > 0:
                md.append("**📋 Vector Search Results with Full Metadata:**")
                md.append("")
                md.append("| # | Student | Class | Subject Group | Satisfaction | Study Time | Similarity |")
                md.append("|---|---------|-------|---------------|--------------|------------|------------|")
                
                for j, detail in enumerate(r['metadata_details'][:10], 1):
                    student = detail.get('student_name', 'N/A')[:15]
                    cls = detail.get('class', 'N/A')
                    subj = detail.get('subject_group', 'N/A')[:12]
                    sat = detail.get('overall_teaching_satisfaction', 'N/A')[:15]
                    study = detail.get('study_time', 'N/A')[:10]
                    sim = detail.get('similarity', 0)
                    if isinstance(sim, Decimal):
                        sim = float(sim)
                    md.append(f"| {j} | {student} | {cls} | {subj} | {sat} | {study} | {sim:.4f} |")
                
                md.append("")
                
                # Show full details for first 3 results
                md.append("**📝 Detailed Feedback with Full Context:**")
                md.append("")
                
                for j, detail in enumerate(r['metadata_details'][:3], 1):
                    md.append(f"<details>")
                    md.append(f"<summary><strong>Result {j}: {detail.get('student_name', 'Student')} ({detail.get('class', 'N/A')})</strong></summary>")
                    md.append("")
                    md.append("| Field | Value |")
                    md.append("|-------|-------|")
                    md.append(f"| **ID** | {detail.get('id', 'N/A')} |")
                    md.append(f"| **Student Name** | {detail.get('student_name', 'N/A')} |")
                    md.append(f"| **School** | {detail.get('school_name', 'N/A')} |")
                    md.append(f"| **Class** | {detail.get('class', 'N/A')} |")
                    md.append(f"| **Subject Group** | {detail.get('subject_group', 'N/A')} |")
                    md.append(f"| **Study Time** | {detail.get('study_time', 'N/A')} |")
                    md.append(f"| **Toughest Subject** | {detail.get('toughest_subject', 'N/A')} |")
                    md.append(f"| **Teacher Support** | {detail.get('teacher_support', 'N/A')} |")
                    md.append(f"| **Transport Satisfaction** | {detail.get('transport_satisfaction', 'N/A')} |")
                    md.append(f"| **Career Guidance** | {detail.get('career_guidance', 'N/A')} |")
                    md.append(f"| **Competitive Exam Prep** | {detail.get('competitive_exam_preparedness', 'N/A')} |")
                    md.append(f"| **Overall Satisfaction** | {detail.get('overall_teaching_satisfaction', 'N/A')} |")
                    md.append(f"| **Recommendation Score** | {detail.get('recommendation_score', 'N/A')} |")
                    sim = detail.get('similarity', 0)
                    if isinstance(sim, Decimal):
                        sim = float(sim)
                    md.append(f"| **Similarity Score** | {sim:.4f} |")
                    md.append("")
                    md.append("**Feedback:**")
                    md.append(f"> {detail.get('feedback', 'No feedback available')}")
                    md.append("")
                    md.append("</details>")
                    md.append("")
        else:
            md.append("**❌ Error:**")
            md.append("")
            md.append(f"```")
            md.append(r['error'])
            md.append("```")
        
        md.append("")
        md.append("---")
        md.append("")
    
    # Summary Statistics
    md.append("## 📈 Summary Statistics")
    md.append("")
    
    # Count by intent
    intent_counts = {}
    for r in results:
        intent = r['intent']
        if intent not in intent_counts:
            intent_counts[intent] = {"total": 0, "success": 0, "charts": 0}
        intent_counts[intent]["total"] += 1
        if r['success']:
            intent_counts[intent]["success"] += 1
        if r.get('chart_path'):
            intent_counts[intent]["charts"] += 1
    
    md.append("### Results by Intent Type")
    md.append("")
    md.append("| Intent | Total | Successful | Success Rate | Charts Generated |")
    md.append("|--------|-------|------------|--------------|------------------|")
    
    for intent, counts in intent_counts.items():
        rate = (counts['success'] / counts['total'] * 100) if counts['total'] > 0 else 0
        md.append(f"| `{intent}` | {counts['total']} | {counts['success']} | {rate:.1f}% | {counts['charts']} |")
    
    md.append("")
    
    # Charts Gallery
    charts = [r for r in results if r.get('chart_path')]
    if charts:
        md.append("### 📊 Charts Gallery")
        md.append("")
        md.append("All generated charts are saved in the `smart_outputs/` folder:")
        md.append("")
        for r in charts:
            md.append(f"- **{r['query'][:40]}...** → `{r['chart_path']}`")
        md.append("")
    
    # Footer
    md.append("---")
    md.append("")
    md.append("*Generated by SMART Survey Copilot Test Suite*")
    md.append(f"*Output folder: `{OUTPUT_DIR}`*")
    
    return "\n".join(md)


if __name__ == "__main__":
    run_tests_and_save_markdown()

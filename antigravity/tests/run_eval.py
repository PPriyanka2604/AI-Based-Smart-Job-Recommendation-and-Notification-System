import json, os, sys
sys.path.insert(0, '.')
from src.parser import ResumeParser
from src.rag_matcher import RAGMatcher
from src.safety_agent import SafetyAgent

def run_evaluation():
    # Load evaluation data
    with open('tests/eval_data.json', 'r') as f:
        data = json.load(f)
    
    parser = ResumeParser()
    # Initialize with mock-friendly settings if needed, but we'll try real ones first
    safety = SafetyAgent(use_llm=False) # Disable LLM for faster eval if not needed
    
    print("\n" + "="*50)
    print("📊 EVALUATING RESUME PARSER (ACCURACY)")
    print("="*50)
    
    p_results = []
    for r in data['resumes']:
        res = parser.parse_resume(r['text'], "test.txt")
        actual = res['total_experience_months']
        expected = r['expected_months']
        error = abs(actual - expected)
        p_results.append(error)
        print(f"Resume {r['id']} ({r['name']}): Expected {expected}m, Got {actual}m, Error: {error}m")
    
    avg_error = sum(p_results) / len(p_results)
    print(f"\n✅ Mean Absolute Error (MAE): {avg_error:.2f} months")
    
    print("\n" + "="*50)
    print("🛡️ EVALUATING SAFETY AGENT (PRECISION/RECALL)")
    print("="*50)
    
    tp, fp, fn, tn = 0, 0, 0, 0
    for j in data['jobs']:
        report = safety.analyze(j)
        is_labeled_scam = j.get('is_scam', False)
        is_detected_scam = report['trust_level'] == "Low"
        
        if is_labeled_scam and is_detected_scam: tp += 1
        elif not is_labeled_scam and is_detected_scam: fp += 1
        elif is_labeled_scam and not is_detected_scam: fn += 1
        else: tn += 1
        
        print(f"Job {j['id']} ({j['title']}): Labeled Scam={is_labeled_scam}, Detected Scam={is_detected_scam}")
        if is_detected_scam:
            print(f"   Flags: {report['heuristic_flags']}")

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    print(f"\n✅ Safety Precision: {precision*100:.1f}%")
    print(f"✅ Safety Recall: {recall*100:.1f}%")

    print("\n" + "="*50)
    print("📈 EVALUATING RAG MATCHER (RECALL@K)")
    print("="*50)
    print("(Note: This requires Ollama/Embeddings to be active)")
    
    try:
        matcher = RAGMatcher()
        matcher.create_index(data['jobs'])
        
        for r in data['resumes']:
            matches = matcher.match_jobs(r['text'], top_k=3)
            match_ids = [m['id'] for m in matches]
            labeled_relevant = r.get('id', 'NONE') # Map relevant jobs manually for this small test
            
            # Simple check: Does J1 show up for R1? J2 for R2?
            relevant_job_found = False
            for j_id in match_ids:
                # Find the job object
                job_obj = next((job for job in data['jobs'] if job['id'] == j_id), None)
                if job_obj and r['id'] in job_obj.get('is_relevant_to', []):
                    relevant_job_found = True
                    break
            
            print(f"Resume {r['id']} ({r['name']}): Matches Found {match_ids}, Relevant Found={relevant_job_found}")
    except Exception as e:
        print(f"❌ RAG Matcher evaluation failed: {e}")

if __name__ == "__main__":
    run_evaluation()

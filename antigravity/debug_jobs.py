from src.job_service import JobService
from src.rag_matcher import RAGMatcher
import requests
import re
import os
from dotenv import load_dotenv

load_dotenv()

def debug_search():
    service = JobService()
    matcher = RAGMatcher() # Now using Ollama
    headers = {"X-API-KEY": service.serper_key, "Content-Type": "application/json"}
    query = "Software Engineer"
    print(f"--- Debugging Search & Match for: {query} ---")
    
    # 1. Test Cleaned Query
    clean = service._clean_query(query)
    print(f"Cleaned Query: {clean}")
    
    # 2. Test Serper API with variations
    tests = [
        {"type": "jobs", "q": clean},
        {"type": "jobs", "q": f"hiring {clean}"},
        {"type": "search", "q": f"'{clean}' hiring India -in.linkedin.com -indeed.com"},
        {"type": "search", "q": f'"{clean}" hiring in India'}
    ]
    
    for t in tests:
        print(f"\n--- Testing {t['type']} endpoint | Q: '{t['q']}' ---")
        url = f"https://google.serper.dev/{t['type']}"
        payload = {"q": t['q'], "gl": "in", "hl": "en", "num": 10}
        
        try:
            resp = requests.post(url, headers=headers, json=payload)
            data = resp.json()
            results = data.get("jobs" if t['type'] == "jobs" else "organic", [])
            print(f"Results Count: {len(results)}")
            
            for i, item in enumerate(results[:10]):
                raw_title = item.get("title", "")
                raw_company = item.get("company", item.get("source", "Unknown"))
                
                # Use JobService extraction
                if raw_company.lower() in ["unknown", "n/a"]:
                    extracted = service._extract_company_from_title(raw_title)
                    if extracted:
                        raw_company = extracted

                job_data = {
                    "title": raw_title,
                    "company": {"display_name": raw_company},
                    "redirect_url": item.get("link"),
                    "description": item.get("description", item.get("snippet", ""))
                }
                valid = service._is_valid_job(job_data)
                status = "PASS" if valid else "FAIL"
                print(f"  [{i}] {status} | Co: {raw_company[:15]} | Title: {raw_title[:40]}")
                if not valid:
                    # Detailed reason
                    title_l = raw_title.lower()
                    comp_l = raw_company.lower()
                    link_l = (job_data.get("redirect_url") or "").lower()
                    if comp_l in ["unknown", "n/a"]: print(f"    -> Reason: Unknown Co")
                    elif re.search(r'\d+\s+.*jobs', title_l): print(f"    -> Reason: Number Jobs")
                    elif title_l.endswith(" jobs"): print(f"    -> Reason: Plural 'jobs'")
                    elif "search?" in link_l or "results?" in link_l: print(f"    -> Reason: Search Link")
                    elif any(p in title_l for p in ["jobs in", "browse jobs"]): print(f"    -> Reason: List Pattern")
                    else: print(f"    -> Reason: Other Filter")
        except Exception as e:
            print(f"Error in test: {e}")

    # 3. Test Apify
    print("\n--- Testing Apify Google Jobs Scraper ---")
    if not service.apify_client:
        print("Apify key missing")
    else:
        try:
            results = service.fetch_jobs_apify(query)
            print(f"Apify Results Count: {len(results)}")
        except Exception as e:
            print(f"Apify Error: {e}")

    # 4. Test Final Pipeline
    print("\n--- Testing End-to-End Pipeline (Fetch + Match) ---")
    try:
        jobs = service.fetch_jobs(query, source="serper")
        print(f"Jobs Fetched: {len(jobs)}")
        if jobs:
            matcher.create_index(jobs)
            matches = matcher.match_jobs("I am a software engineer with experience in Python and cloud.")
            print(f"Top 3 Matches found: {len(matches[:3])}")
            for m in matches[:3]:
                print(f"  - {m['title']} at {m['company']['display_name']} (Score: {m['match_score']:.2f})")
    except Exception as e:
        print(f"Pipeline Error: {e}")

if __name__ == "__main__":
    debug_search()

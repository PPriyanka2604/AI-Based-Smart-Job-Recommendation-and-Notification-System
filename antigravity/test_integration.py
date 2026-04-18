import sys, os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from src.job_service import JobService

svc = JobService()
print("Testing fetch_jobs for 'Software Engineer' (Entry-Level)...")
jobs = svc.fetch_jobs("Software Engineer", level="Entry-Level", location="India", num_results=30)

if isinstance(jobs, dict) and "error" in jobs:
    print(f"ERROR: {jobs['error']}")
else:
    from collections import Counter
    sources = Counter(j["_origin"] for j in jobs)
    print(f"\n✅ Total jobs: {len(jobs)}")
    print(f"By source:  {dict(sources)}")
    print(f"\nSample jobs:")
    for j in jobs[:5]:
        print(f"  [{j['_origin']}] {j['title']} @ {j['company']} — {j['location']}")

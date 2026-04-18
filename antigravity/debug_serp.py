import requests, os, json
from dotenv import load_dotenv
load_dotenv()

serp_key = os.getenv("SERPAPI_KEY", "")

r = requests.get(
    "https://serpapi.com/search",
    params={
        "engine":   "google_jobs",
        "q":        "software engineer entry level India",
        "location": "India",
        "gl":       "in",
        "hl":       "en",
        "api_key":  serp_key,
    },
    timeout=20
)

jobs = r.json().get("jobs_results", [])
print(f"Jobs returned: {len(jobs)}\n")

for i, j in enumerate(jobs[:3]):
    print(f"--- Job {i+1} ---")
    print(f"Title:   {j.get('title')}")
    print(f"Company: {j.get('company_name')}")
    print(f"Via:     {j.get('via')}")
    print(f"Share link: {j.get('share_link', 'NONE')}")
    print(f"Apply options ({len(j.get('apply_options', []))}):")
    for opt in j.get("apply_options", []):
        print(f"  - {opt.get('title', '?')} : {opt.get('link', 'no link')[:100]}")
    print()

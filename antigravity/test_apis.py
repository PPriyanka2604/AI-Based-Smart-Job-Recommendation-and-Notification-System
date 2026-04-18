import requests, os, sys
from dotenv import load_dotenv
load_dotenv()

app_id  = os.getenv("ADZUNA_APP_ID", "")
app_key = os.getenv("ADZUNA_APP_KEY", "")
serp_key = os.getenv("SERPAPI_KEY", "")

print(f"Adzuna ID : {app_id}")
print(f"Adzuna Key: {app_key[:8]}...")
print(f"SerpAPI   : {serp_key[:8]}...")
print()

# ── Test Adzuna ──
print("=== Adzuna Test ===")
try:
    r = requests.get(
        "https://api.adzuna.com/v1/api/jobs/in/search/1",
        params={
            "app_id": app_id, "app_key": app_key,
            "what": "software engineer",
            "results_per_page": 3,
            "content-type": "application/json"
        },
        timeout=10
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        results = data.get("results", [])
        print(f"Total available: {data.get('count', 0)}, Returned: {len(results)}")
        for j in results:
            print(f"  - {j['title']} @ {j['company']['display_name']}")
    else:
        print(f"Error body: {r.text[:300]}")
except Exception as e:
    print(f"Exception: {e}")

print()

# ── Test SerpAPI ──
print("=== SerpAPI Test ===")
try:
    r2 = requests.get(
        "https://serpapi.com/search",
        params={
            "engine": "google_jobs",
            "q": "software engineer India",
            "api_key": serp_key,
            "gl": "in",
            "hl": "en"
        },
        timeout=15
    )
    print(f"Status: {r2.status_code}")
    if r2.status_code == 200:
        jobs = r2.json().get("jobs_results", [])
        print(f"Jobs returned: {len(jobs)}")
        for j in jobs[:3]:
            print(f"  - {j['title']} @ {j['company_name']}")
    else:
        print(f"Error body: {r2.text[:300]}")
except Exception as e:
    print(f"Exception: {e}")

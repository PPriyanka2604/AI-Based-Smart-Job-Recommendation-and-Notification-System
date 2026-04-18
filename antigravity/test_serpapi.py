import requests, os
from dotenv import load_dotenv
load_dotenv()

serp_key = os.getenv("SERPAPI_KEY", "")
print(f"SerpAPI Key: {serp_key[:12]}...\n")

# Test 1: Simple call
print("=== Test 1: Basic SerpAPI call ===")
r = requests.get(
    "https://serpapi.com/search",
    params={
        "engine":   "google_jobs",
        "q":        "software engineer",
        "location": "India",
        "gl":       "in",
        "hl":       "en",
        "api_key":  serp_key,
    },
    timeout=20
)
print(f"Status: {r.status_code}")
data = r.json()
print(f"Keys in response: {list(data.keys())}")
jobs = data.get("jobs_results", [])
print(f"Jobs returned: {len(jobs)}")
if "error" in data:
    print(f"Error: {data['error']}")
if jobs:
    print(f"First job: {jobs[0]['title']} @ {jobs[0]['company_name']}")

# Test 2: Account info
print("\n=== Test 2: Account Status ===")
r2 = requests.get(
    "https://serpapi.com/account",
    params={"api_key": serp_key},
    timeout=10
)
print(f"Status: {r2.status_code}")
if r2.status_code == 200:
    acc = r2.json()
    print(f"Plan: {acc.get('plan_name')}")
    print(f"Searches left: {acc.get('searches_per_month', 'N/A')}")
    print(f"Total searches: {acc.get('total_searches_done', 'N/A')}")
    print(f"Account email: {acc.get('email', 'N/A')}")
else:
    print(r2.text[:200])

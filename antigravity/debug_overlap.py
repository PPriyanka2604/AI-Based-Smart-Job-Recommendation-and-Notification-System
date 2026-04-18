import sys, os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

import requests, re, time

adzuna_id  = os.getenv("ADZUNA_APP_ID", "")
adzuna_key = os.getenv("ADZUNA_APP_KEY", "")
serp_key   = os.getenv("SERPAPI_KEY", "")

def fingerprint(title, company):
    def norm(s):
        s = s.lower().strip()
        s = re.sub(r'\b(pvt|ltd|inc|llc|llp|corp|technologies|solutions|services|'
                   r'software|systems|india|private|limited|group|global|the|'
                   r'consulting|ventures|labs|studio|studios)\b', '', s)
        s = re.sub(r'\b(senior|sr|junior|jr|lead|principal|staff|associate|mid|entry|'
                   r'intern|internship|trainee|graduate|fresher|summer|winter)\b', '', s)
        return re.sub(r'[^a-z0-9]', '', s)
    return norm(title) + '|' + norm(company)

# Step 1: Get Adzuna links
az_links = set()
r = requests.get(
    "https://api.adzuna.com/v1/api/jobs/in/search/1",
    params={"app_id": adzuna_id, "app_key": adzuna_key, "what": "software engineer fresher", "results_per_page": 10},
    timeout=10
)
for item in r.json().get("results", []):
    link = item.get("redirect_url", "")
    if link:
        az_links.add(link.split("?")[0].rstrip("/").lower())

print(f"Adzuna seen_links count: {len(az_links)}")

# Step 2: See if SerpAPI links overlap
r2 = requests.get(
    "https://serpapi.com/search",
    params={"engine": "google_jobs", "q": "software engineer fresher", "location": "India", "gl": "in", "hl": "en", "api_key": serp_key},
    timeout=20
)
serp_jobs = r2.json().get("jobs_results", [])
print(f"SerpAPI jobs: {len(serp_jobs)}\n")

overlapping = 0
for j in serp_jobs:
    title = j.get("title", "")
    company = j.get("company_name", "")
    link = ""
    for opt in j.get("apply_options", []):
        ol = opt.get("link", "")
        if ol and "google.com" not in ol:
            link = ol
            break
    if not link:
        link = j.get("share_link", "")
    
    if link:
        norm = link.split("?")[0].rstrip("/").lower()
        if norm in az_links:
            overlapping += 1
            print(f"  OVERLAP: {title} — {norm[:60]}")
        else:
            print(f"  UNIQUE:  {title} — {norm[:60]}")
    else:
        print(f"  NO LINK: {title}")

print(f"\nOverlapping links: {overlapping}/{len(serp_jobs)}")

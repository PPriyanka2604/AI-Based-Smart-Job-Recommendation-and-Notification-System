import sys, os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

import requests, re, time

serp_key = os.getenv("SERPAPI_KEY", "")

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

# Simulate exactly what job_service does with SerpAPI
seen_links = set()   # empty — no Adzuna pre-fill
local_fps  = set()

results = []

queries = ["software engineer fresher", "software engineer internship", "software engineer entry level"]

for query in queries[:2]:
    print(f"\n=== Query: '{query}' ===")
    r = requests.get(
        "https://serpapi.com/search",
        params={
            "engine":   "google_jobs",
            "q":        query,
            "location": "India",
            "gl":       "in",
            "hl":       "en",
            "api_key":  serp_key,
        },
        timeout=20
    )
    jobs_raw = r.json().get("jobs_results", [])
    print(f"  Raw jobs: {len(jobs_raw)}")
    
    for item in jobs_raw:
        title   = (item.get("title") or "").strip()
        company = (item.get("company_name") or "").strip()
        if not title or not company:
            print(f"  ❌ skip: no title/company")
            continue
        
        link = ""
        for opt in item.get("apply_options", []):
            ol = opt.get("link", "")
            if ol and "google.com" not in ol:
                link = ol
                break
        if not link:
            link = item.get("share_link", "")
        
        if not link:
            print(f"  ❌ '{title}' @ {company} — no link")
            continue
        
        norm_link = link.split("?")[0].rstrip("/").lower()
        fp = fingerprint(title, company)
        
        if norm_link in seen_links:
            print(f"  ⚠️  '{title}' @ {company} — dup URL: {norm_link[:50]}")
            continue
        if fp in local_fps:
            print(f"  ⚠️  '{title}' @ {company} — dup FP: {fp}")
            continue
        
        print(f"  ✅ '{title}' @ {company}")
        local_fps.add(fp)
        seen_links.add(norm_link)
        results.append(title)

print(f"\n\nTotal accepted by SerpAPI logic: {len(results)}")

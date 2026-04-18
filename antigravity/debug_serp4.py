import sys, os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

import requests, re, time
from src.job_service import JobService, _serp_queries

svc = JobService()

# Simulate _fetch_serpapi with full verbose output
seen_fps   = set()   # empty — simulate after Adzuna
seen_links = set()   # empty — no overlap proven
local_fps  = set()
results    = []
target     = 60

role  = "Software Engineer"
level = "Entry-Level"
loc   = "India"

queries = _serp_queries(role, level)
print(f"SerpAPI queries to try ({len(queries)}): {queries[:4]}...\n")

for query in queries[:2]:   # just test first 2
    print(f"\n=== Query: '{query}' | results so far: {len(results)}/{target} ===")
    if len(results) >= target:
        print("  [SKIP] Already at target")
        break

    for start in [0, 10]:
        if len(results) >= target:
            break
        try:
            r = requests.get(
                svc.serpapi_url,
                params={"engine": "google_jobs", "q": query, "location": loc,
                        "gl": "in", "hl": "en", "start": str(start), "api_key": svc.serpapi_key},
                timeout=20,
            )
        except Exception as e:
            print(f"  Exception: {e}")
            break

        print(f"  start={start}: HTTP {r.status_code}")
        if r.status_code != 200:
            break

        jobs_raw = r.json().get("jobs_results", [])
        print(f"  Raw jobs: {len(jobs_raw)}")

        added = 0
        for item in jobs_raw:
            title   = (item.get("title") or "").strip()
            company = (item.get("company_name") or "").strip()
            if not title or not company:
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
                print(f"    SKIP no link: {title}")
                continue
            norm_link = link.split("?")[0].rstrip("/").lower()
            fp = svc._fingerprint(title, company)
            if norm_link in seen_links:
                print(f"    SKIP dup url: {title}")
                continue
            if fp in local_fps:
                print(f"    SKIP dup fp:  {title} | fp={fp}")
                continue
            local_fps.add(fp)
            seen_links.add(norm_link)
            results.append(title)
            added += 1

        print(f"  Added: {added}")

print(f"\n\nFinal count: {len(results)} jobs accepted")

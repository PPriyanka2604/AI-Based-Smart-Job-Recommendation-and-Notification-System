import requests, os
from dotenv import load_dotenv
load_dotenv()

serp_key = os.getenv("SERPAPI_KEY", "")

r = requests.get(
    "https://serpapi.com/search",
    params={
        "engine":   "google_jobs",
        "q":        "software engineer fresher India",
        "location": "India",
        "gl":       "in",
        "hl":       "en",
        "api_key":  serp_key,
    },
    timeout=20
)

jobs = r.json().get("jobs_results", [])
print(f"Jobs: {len(jobs)}\n")

accepted = 0
rejected = 0
for j in jobs:
    title   = j.get("title", "")
    company = j.get("company_name", "")
    share   = j.get("share_link", "")
    opts    = j.get("apply_options", [])
    
    # Simulate what job_service does
    link = ""
    for opt in opts:
        ol = opt.get("link", "")
        if ol and "google.com" not in ol:
            link = ol
            break
    if not link:
        link = share
    
    has_link = bool(link)
    is_google = "google.com" in link if link else False
    
    if has_link:
        accepted += 1
        print(f"  ✅ '{title}' @ {company}")
        print(f"      link: {link[:80]}")
    else:
        rejected += 1
        print(f"  ❌ '{title}' @ {company} — NO LINK")
        print(f"      share: {share[:80]}")
        print(f"      apply_opts: {[o.get('link','')[:60] for o in opts]}")

print(f"\n✅ Accepted: {accepted} | ❌ Rejected (no link): {rejected}")

import requests, os
from dotenv import load_dotenv
load_dotenv()

serp_key = os.getenv("SERPAPI_KEY", "")

queries = [
    "Software Engineer internship",
    "Software Engineer intern India",
    "software engineer fresher",
    "software engineer entry level",
    "software engineer",
]

for q in queries:
    r = requests.get(
        "https://serpapi.com/search",
        params={"engine": "google_jobs", "q": q, "location": "India",
                "gl": "in", "hl": "en", "api_key": serp_key},
        timeout=15
    )
    jobs = r.json().get("jobs_results", [])
    err  = r.json().get("error", "")
    print(f"[{r.status_code}] '{q}' -> {len(jobs)} jobs {'| ERR: '+err[:50] if err else ''}")

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.job_service import JobService

def test_jsearch():
    load_dotenv()
    
    key = os.getenv("JSEARCH_API_KEY")
    if not key or key == "your_jsearch_api_key_here":
        print("❌ Error: JSEARCH_API_KEY not set in .env")
        return

    print("🚀 Testing JSearch integration...")
    service = JobService()
    
    role = "Software Engineer"
    level = "Entry"
    
    print(f"🔍 Fetching jobs for: {role} ({level})...")
    jobs = service.fetch_jobs(role, level=level)
    
    print(f"✅ Success! Found {len(jobs)} jobs.")
    for i, job in enumerate(jobs):
        print(f"\n--- Job {i+1} ---")
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']['display_name']}")
        print(f"Location: {job['location']['display_name']}")
        print(f"Posted: {job.get('date_posted', 'N/A')}")
        print(f"URL: {job['redirect_url']}")

if __name__ == "__main__":
    test_jsearch()

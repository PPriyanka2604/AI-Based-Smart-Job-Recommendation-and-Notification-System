import requests
import os
import re
import time
from dotenv import load_dotenv

load_dotenv(override=True)


# ─────────────────────────────────────────────────────────────
# QUERY BUILDER
# ─────────────────────────────────────────────────────────────

def _adzuna_keywords(role, level):
    """Returns list of keyword strings for Adzuna 'what' param."""
    base = re.sub(r'[^a-zA-Z0-9\s]', '', role).strip()
    lvl = (level or "").lower()
    is_entry  = lvl in ("entry-level", "entry level", "fresher", "")
    is_junior = "junior" in lvl
    is_senior = any(x in lvl for x in ("senior", "lead", "principal", "staff"))

    if is_entry or is_junior:
        return [
            f"{base} fresher",
            f"{base} entry level",
            f"{base} junior",
            f"{base} trainee",
            f"{base} internship",
            f"{base} intern",
            f"{base} graduate",
            f"{base}",
        ]
    elif is_senior:
        return [
            f"senior {base}",
            f"lead {base}",
            f"principal {base}",
            f"{base}",
        ]
    else:
        return [
            f"{base}",
            f"{base} developer",
            f"{base} engineer",
        ]


def _serp_queries(role, level):
    """SerpAPI Google Jobs queries."""
    base = re.sub(r'[^a-zA-Z0-9\s]', '', role).strip()
    lvl  = (level or "").lower()
    is_entry  = lvl in ("entry-level", "entry level", "fresher", "")
    is_junior = "junior" in lvl
    is_senior = any(x in lvl for x in ("senior", "lead", "principal", "staff"))

    if is_entry or is_junior:
        return [
            f"{base} internship",
            f"{base} intern",
            f"{base} internship internshala",
            f"{base} internship unstop",
            f"{base} internship naukri",
            f"{base} freshers jobs",
            f"{base} entry level",
            f"{base} trainee",
            f"{base} junior",
            f"{base} fresher naukri",
            f"{base} fresher indeed",
            f"{base} graduate trainee",
        ]
    elif is_senior:
        return [
            f"senior {base}",
            f"lead {base}",
            f"senior {base} naukri",
            f"senior {base} linkedin",
            f"{base}",
        ]
    else:
        return [
            f"{base}",
            f"{base} developer",
            f"{base} naukri",
            f"{base} glassdoor",
            f"{base} indeed",
            f"{base} wellfound",
            f"{base} foundit",
            f"{base} hirist",
        ]


class JobService:
    def __init__(self):
        self.adzuna_app_id  = os.getenv("ADZUNA_APP_ID", "").strip()
        self.adzuna_app_key = os.getenv("ADZUNA_APP_KEY", "").strip()
        self.adzuna_url     = "https://api.adzuna.com/v1/api/jobs/in/search/{page}"

        self.serpapi_key = os.getenv("SERPAPI_KEY", "").strip()
        self.serpapi_url = "https://serpapi.com/search"

        self._cache     = {}
        self._cache_ttl = 300

    # ── Helpers ──────────────────────────────────────────────
    def _format_description(self, text):
        if not text:
            return ""
        # Remove HTML
        text = re.sub(r'<[^>]+>', '', text)
        sentences = [s.strip() for s in text.replace('\n', '. ').split('. ') if len(s.strip()) > 5]
        if not sentences:
            return text[:300]  # Fallback to raw text if sentences are too short
        return '. '.join(sentences[:10]) + ('.' if not sentences[0].endswith('.') else '')

    def _detect_source(self, via, apply_link):
        s = ((via or '') + ' ' + (apply_link or '')).lower()
        if 'linkedin'      in s: return 'LinkedIn'
        if 'indeed'        in s: return 'Indeed'
        if 'glassdoor'     in s: return 'Glassdoor'
        if 'wellfound'     in s: return 'Wellfound'
        if 'naukri'        in s: return 'Naukri'
        if 'foundit'       in s: return 'Foundit'
        if 'internshala'   in s: return 'Internshala'
        if 'monster'       in s: return 'Monster'
        if 'shine'         in s: return 'Shine'
        if 'ziprecruiter'  in s: return 'ZipRecruiter'
        if 'unstop'        in s: return 'Unstop'
        if 'hirist'        in s: return 'Hirist'
        if 'cutshort'      in s: return 'Cutshort'
        if 'freshersworld' in s: return 'FreshersWorld'
        if 'timesjobs'     in s: return 'TimesJobs'
        if 'simplyhired'   in s: return 'SimplyHired'
        if 'adzuna'        in s: return 'Adzuna'
        return 'Company Website'

    def _is_trusted(self, source):
        return source in {
            'LinkedIn', 'Indeed', 'Glassdoor', 'Wellfound', 'Naukri',
            'Foundit', 'ZipRecruiter', 'Internshala', 'Unstop',
            'Hirist', 'Cutshort', 'FreshersWorld', 'TimesJobs', 'Adzuna'
        }

    def _is_relevant_title(self, title, role):
        """
        Returns True if the job title overlaps meaningfully with the target role.
        Strips common suffixes and checks for keyword presence.
        """
        if not title or not role:
            return True  # don't filter if we can't check
        # Extract meaningful words from role (skip common words)
        stop = {'and', 'or', 'the', 'of', 'for', 'in', 'at', 'to', 'a'}
        role_words = {w.lower() for w in re.split(r'[\s/\-_]+', role) if len(w) > 2 and w.lower() not in stop}
        title_lower = title.lower()
        # A title is relevant if ANY role keyword appears in it, OR if it has
        # internship/trainee/fresher/junior words (for entry-level searches)
        seniority_ok = any(w in title_lower for w in ('intern', 'trainee', 'fresher', 'graduate', 'junior', 'entry'))
        role_match   = any(w in title_lower for w in role_words)
        return role_match or seniority_ok

    @staticmethod
    def _is_recent(date_str, max_days=30):
        """
        Returns True if the job was posted within max_days.
        Accepts ISO 8601 or relative strings like '3 days ago', '2 weeks ago'.
        If date cannot be parsed, returns True (don't filter).
        """
        if not date_str:
            return True  # no date = keep (can't know)
        date_str = str(date_str).strip().lower()
        # Relative: 'X days/weeks/months ago'
        m = re.match(r'(\d+)\s+(day|week|month)', date_str)
        if m:
            n, unit = int(m.group(1)), m.group(2)
            days = n if unit == 'day' else (n * 7 if unit == 'week' else n * 30)
            return days <= max_days
        # ISO datetime: '2026-01-15T10:30:00Z'
        try:
            from datetime import datetime, timezone
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                age = (datetime.now(timezone.utc) - dt).days
                return age <= max_days
        except Exception:
            pass
        return True  # unknown format — keep

    @staticmethod
    def _fingerprint(title, company):
        def norm(s):
            s = s.lower().strip()
            s = re.sub(r'\b(pvt|ltd|inc|llc|llp|corp|technologies|solutions|services|'
                       r'software|systems|india|private|limited|group|global|the|'
                       r'consulting|ventures|labs|studio|studios)\b', '', s)
            s = re.sub(r'\b(senior|sr|junior|jr|lead|principal|staff|associate|mid|entry|'
                       r'intern|internship|trainee|graduate|fresher|summer|winter)\b', '', s)
            return re.sub(r'[^a-z0-9]', '', s)
        return norm(title) + '|' + norm(company)

    # ── Adzuna ───────────────────────────────────────────────
    def _fetch_adzuna(self, role, level, location, seen_fps, seen_links, target=60):
        if not self.adzuna_app_id or not self.adzuna_app_key:
            print("[Adzuna] No credentials — skipping.")
            return [], None

        results = []

        for keyword in _adzuna_keywords(role, level):
            if len(results) >= target:
                break

            # Try last 7 days first, fall back to 30 days
            for max_days in [7, 30]:
                if len(results) >= target:
                    break
                keyword_results = 0

                for page in range(1, 5):
                    if len(results) >= target:
                        break
                    try:
                        r = requests.get(
                            self.adzuna_url.format(page=page),
                            params={
                                "app_id":           self.adzuna_app_id,
                                "app_key":          self.adzuna_app_key,
                                "what":             keyword,
                                "where":            location or "India",
                                "results_per_page": 20,
                                "max_days_old":     max_days,
                                "content-type":     "application/json",
                            },
                            timeout=20,
                        )
                    except Exception as e:
                        print(f"[Adzuna] Error ({keyword}): {e}")
                        break

                    if r.status_code == 401:
                        return results, "Invalid Adzuna credentials (401)."
                    if r.status_code == 429:
                        return results, "Adzuna rate-limit (429)."
                    if r.status_code != 200:
                        break

                    items = r.json().get("results", [])
                    if not items:
                        break

                    for item in items:
                        title   = (item.get("title") or "").strip()
                        company = (item.get("company", {}).get("display_name") or "").strip()
                        link    = (item.get("redirect_url") or "").strip()

                        if not title or not company or not link:
                            continue

                        # ── Relevance + recency gates ────────────────
                        if not self._is_relevant_title(title, role):
                            continue
                        date_created = item.get("created", "")
                        if not self._is_recent(date_created, max_days=max_days):
                            continue

                        norm_link = link.split("?")[0].rstrip("/").lower()
                        fp = self._fingerprint(title, company)
                        if fp in seen_fps or norm_link in seen_links:
                            continue

                        location_name = (item.get("location", {}).get("display_name") or location or "India")
                        source = self._detect_source("adzuna", link)

                        results.append({
                            "id":              str(item.get("id", "")),
                            "title":           title,
                            "company":         company,
                            "location":        location_name,
                            "description":     self._format_description(item.get("description", "")),
                            "apply_link":      link,
                            "source":          source,
                            "trusted":         self._is_trusted(source),
                            "date_posted":     item.get("created", ""),
                            "employment_type": item.get("contract_time", ""),
                            "is_remote":       False,
                            "_origin":         "adzuna",
                            "_label":          keyword,
                        })
                        seen_fps.add(fp)
                        seen_links.add(norm_link)
                        keyword_results += 1

                    time.sleep(0.3)

                if keyword_results > 0:
                    break  # got results with this date range, don't need wider

        print(f"[Adzuna] ✅  {len(results)} unique jobs.")
        return results, None

    # ── SerpAPI (Google Jobs) ─────────────────────────────────
    def _fetch_serpapi(self, role, level, location, seen_fps, seen_links, target=60):
        if not self.serpapi_key:
            print("[SerpAPI] No key — skipping.")
            return [], None

        loc       = location or "India"
        results   = []
        local_fps = set()

        for query in _serp_queries(role, level):
            if len(results) >= target:
                break

            # Fetch up to 2 pages using next_page_token (start is deprecated by Google)
            next_token = None
            for page_num in range(2):   # 2 pages × 10 = 20 per query
                if len(results) >= target:
                    break
                try:
                    params = {
                        "engine":   "google_jobs",
                        "q":        query,
                        "location": loc,
                        "gl":       "in",
                        "hl":       "en",
                        "api_key":  self.serpapi_key,
                    }
                    if next_token:
                        params["next_page_token"] = next_token

                    r = requests.get(self.serpapi_url, params=params, timeout=20)
                except Exception as e:
                    print(f"[SerpAPI] Error: {e}")
                    break

                if r.status_code == 401:
                    return results, "Invalid SerpAPI key (401)."
                if r.status_code == 429:
                    return results, "SerpAPI rate-limit — searches exhausted."
                if r.status_code != 200:
                    break

                data     = r.json()
                jobs_raw = data.get("jobs_results", [])
                if not jobs_raw:
                    break

                for item in jobs_raw:
                    title   = (item.get("title") or "").strip()
                    company = (item.get("company_name") or "").strip()
                    if not title or not company:
                        continue

                    # ── Relevance gate ────────────────────────────
                    if not self._is_relevant_title(title, role):
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
                        continue

                    norm_link = link.split("?")[0].rstrip("/").lower()
                    fp = self._fingerprint(title, company)

                    # Use local_fps for within-SerpAPI dedup; seen_links globally for URL dedup
                    if norm_link in seen_links or fp in local_fps:
                        continue

                    ext    = item.get("detected_extensions", {})
                    source = self._detect_source(item.get("via", ""), link)

                    results.append({
                        "id":              item.get("job_id", ""),
                        "title":           title,
                        "company":         company,
                        "location":        item.get("location", ""),
                        "description":     self._format_description(item.get("description", "")),
                        "apply_link":      link,
                        "source":          source,
                        "trusted":         self._is_trusted(source),
                        "date_posted":     ext.get("posted_at", ""),
                        "employment_type": ext.get("schedule_type", ""),
                        "is_remote":       ext.get("work_from_home", False),
                        "_origin":         "serpapi",
                        "_label":          query,
                    })
                    local_fps.add(fp)
                    seen_links.add(norm_link)

                # Get next page token for pagination
                pagination   = data.get("serpapi_pagination", {})
                next_token   = pagination.get("next_page_token")
                if not next_token:
                    break  # no more pages

                time.sleep(0.25)

            time.sleep(0.25)

        print(f"[SerpAPI] ✅  {len(results)} unique jobs.")
        return results, None

    # ── Round-robin diversity ─────────────────────────────────
    def _diversify(self, jobs, n):
        buckets = {}
        for j in jobs:
            buckets.setdefault(j["source"], []).append(j)
        out = []
        while len(out) < n:
            added = False
            for src in list(buckets):
                if buckets[src]:
                    out.append(buckets[src].pop(0))
                    added = True
                    if len(out) >= n:
                        break
            if not added:
                break
        return out

    # ── Main entry point ─────────────────────────────────────
    def fetch_jobs(self, role, level=None, location="India", num_results=100, source=None):
        load_dotenv(override=True)
        self.adzuna_app_id  = os.getenv("ADZUNA_APP_ID", "").strip()
        self.adzuna_app_key = os.getenv("ADZUNA_APP_KEY", "").strip()
        self.serpapi_key    = os.getenv("SERPAPI_KEY", "").strip()

        if not self.adzuna_app_id and not self.adzuna_app_key and not self.serpapi_key:
            return {"error": "No API keys found. Add ADZUNA_APP_ID + ADZUNA_APP_KEY and/or SERPAPI_KEY to .env."}

        cache_key = (role.lower().strip(), (level or "").lower().strip(),
                     (location or "").lower().strip(), num_results)
        now    = time.time()
        cached = self._cache.get(cache_key)
        if cached and (now - cached["time"] < self._cache_ttl):
            print(f"[JobService] Cache hit for '{role}' ({level}).")
            return cached["data"]

        seen_fps = set(); seen_links = set(); all_jobs = []; errors = []

        az_jobs, az_err = self._fetch_adzuna(
            role, level, location, seen_fps, seen_links, target=60)
        if az_err: errors.append(f"Adzuna: {az_err}")
        all_jobs.extend(az_jobs)

        sp_jobs, sp_err = self._fetch_serpapi(
            role, level, location, seen_fps, seen_links, target=60)
        if sp_err: errors.append(f"SerpAPI: {sp_err}")
        all_jobs.extend(sp_jobs)

        if not all_jobs:
            result = {"error": "No jobs found. " + (" | ".join(errors) if errors else
                      "Try a different role or location.")}
            self._cache[cache_key] = {"time": now, "data": result}
            return result

        final   = self._diversify(all_jobs, num_results)
        sources = {j["source"] for j in final}
        print(f"[JobService] ✅  {len(final)} jobs from {len(sources)} portals: "
              f"{', '.join(sorted(sources))}")
        self._cache[cache_key] = {"time": now, "data": final}
        return final

    def clear_cache(self):
        self._cache.clear()
        print("[JobService] Cache cleared.")
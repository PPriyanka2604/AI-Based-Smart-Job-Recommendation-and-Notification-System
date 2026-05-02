# 🚀 AI Smart Job Assistant

> An AI-powered job recommendation and resume enhancement platform built with Streamlit, Ollama, and real-time job APIs.

---

## 📌 Overview

**AI Smart Job Assistant** is a fully local, privacy-first career tool that:

- Parses your resume (PDF or DOCX) and extracts skills, experience, and seniority level
- Detects your target role automatically using a local LLM
- Fetches 100+ real job listings from multiple portals (Adzuna, SerpAPI/Google Jobs)
- Ranks jobs against your resume using RAG (vector similarity via Ollama embeddings)
- Scores each job using an AI match engine (skills overlap, seniority, domain fit)
- Flags fake/scam job postings with a multi-layer Safety Agent (heuristics + FAISS + LLM)
- Sends job alerts to your email and supports daily scheduled notifications

---

## 🖼️ Features at a Glance

| Feature | Details |
|---|---|
| 📄 Resume Parsing | PDF & DOCX support, 10-pattern experience extraction |
| 🎯 Role Detection | LLM-based target role identification |
| 📊 ATS Scoring | Resume improvement suggestions via local LLM |
| 🔍 Job Discovery | Adzuna + SerpAPI (Naukri, Internshala, Wellfound, Unstop, Glassdoor, LinkedIn, Indeed) |
| 🧠 RAG Matching | Embedding-based ranking with `nomic-embed-text` via Ollama |
| 🤖 AI Job Scoring | Per-job match score (0–100) with skill breakdown |
| 🛡️ Safety Agent | 3-layer fake job detection: heuristics → FAISS → LLM |
| 📧 Email Alerts | Beautiful HTML job alert emails via Gmail SMTP |
| ⏰ Daily Scheduler | Cron-based daily job alerts using APScheduler |
| 💾 Search History | SQLite-backed deduplication and history tracking |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Streamlit UI (app.py)              │
│          Tab 1: Resume  │  Tab 2: Jobs  │  Tab 3: History │
└───────────────┬──────────────────┬───────────────────┘
                │                  │
        ┌───────▼──────┐   ┌───────▼──────────────┐
        │ ResumeParser │   │      JobService       │
        │  (parser.py) │   │   (job_service.py)    │
        │              │   │  Adzuna + SerpAPI     │
        │ 10-pattern   │   │  dedup + diversify    │
        │ experience   │   └───────┬──────────────┘
        │ extraction   │           │
        └───────┬──────┘   ┌───────▼──────────────┐
                │           │     RAGMatcher        │
        ┌───────▼──────┐   │   (rag_matcher.py)    │
        │  LLMManager  │   │  nomic-embed-text     │
        │   (llm.py)   │   │  cosine similarity    │
        │  Ollama API  │   └───────────────────────┘
        │  gemma3/llama│
        └───────┬──────┘   ┌───────────────────────┐
                │           │     SafetyAgent        │
                │           │  (safety_agent.py)    │
                │           │  Heuristics+FAISS+LLM │
                │           └───────────────────────┘
                │
        ┌───────▼──────────────────────────────────┐
        │  Notifier (notifier.py) + DB (database.py)│
        │  Gmail SMTP + APScheduler + SQLite        │
        └───────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **LLM Backend:** [Ollama](https://ollama.com) (local) — `gemma3:1b`, `llama3`, `mistral`, `neural-chat`
- **Embeddings:** `nomic-embed-text` via Ollama, `all-MiniLM-L6-v2` via sentence-transformers (safety agent)
- **Vector Search:** FAISS (fake job detection), NumPy cosine similarity (RAG matching)
- **Job APIs:** Adzuna API, SerpAPI (Google Jobs engine)
- **Resume Parsing:** pdfminer.six, python-docx
- **Email:** smtplib + Gmail SMTP (App Password)
- **Scheduling:** APScheduler (CronTrigger)
- **Database:** SQLite via Python's built-in `sqlite3`

---

## ⚙️ Setup & Installation

### 1. Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/download) installed and running locally

### 2. Clone the Repository

```bash
git clone https://github.com/your-username/ai-smart-job-assistant.git
cd ai-smart-job-assistant
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Pull Required Ollama Models

```bash
# LLM (pick one — gemma3:1b is fastest)
ollama pull gemma3:1b
ollama pull llama3        # optional, more capable
ollama pull mistral       # optional

# Embedding model (required for RAG matching)
ollama pull nomic-embed-text
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
# ── Job APIs (at least one required) ──────────────────────────
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
SERPAPI_KEY=your_serpapi_key

# ── Email Notifications (optional) ────────────────────────────
SENDER_EMAIL=your_gmail_address@gmail.com
SENDER_PASSWORD=your_gmail_app_password
```

> **Note on Gmail:** You need a [Gmail App Password](https://support.google.com/accounts/answer/185833), not your regular Gmail password. Enable 2FA first, then generate an App Password under Google Account → Security.

### 6. Get Free API Keys

| API | Free Tier | Sign Up |
|---|---|---|
| **Adzuna** | 250 req/day | [adzuna.com/api](https://developer.adzuna.com/) |
| **SerpAPI** | 100 searches/month | [serpapi.com](https://serpapi.com/users/sign_up) |

### 7. Run the App

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📁 Project Structure

```
ai-smart-job-assistant/
├── app.py                  # Main Streamlit application
├── .env                    # API keys & credentials (not committed)
├── requirements.txt        # Python dependencies
│
├── src/
│   ├── parser.py           # Resume parser — PDF/DOCX + 10-pattern experience extractor
│   ├── llm.py              # LLM manager — Ollama API wrapper (role detect, ATS, scoring)
│   ├── job_service.py      # Job fetcher — Adzuna + SerpAPI with dedup & diversification
│   ├── rag_matcher.py      # RAG matcher — embedding-based job ranking
│   ├── safety_agent.py     # Safety agent — fake job detection (3 layers)
│   ├── notifier.py         # Email notifier — SMTP + HTML templates + daily scheduler
│   └── database.py         # SQLite manager — search history & deduplication
│
├── data/
│   └── jobs_history.db     # Auto-created SQLite database
│
└── debug/                  # Debugging & testing scripts
    ├── debug_jobs.py
    ├── debug_serp.py
    ├── debug_serp2.py
    ├── debug_serp3.py
    ├── debug_serp4.py
    ├── debug_overlap.py
    ├── debug_queries.py
    ├── test_apis.py
    ├── test_integration.py
    ├── test_serpapi.py
    ├── test_ollama_api.py
    └── verify_jsearch.py
```

---

## 🧩 Module Deep-Dives

### 📄 Resume Parser (`parser.py`)

Extracts structured data from PDF/DOCX resumes using rule-based logic — no LLM required for parsing.

**10 supported experience patterns:**
1. Numeric years — `3 years`
2. Decimal years — `2.5 years`
3. Text years — `two years`
4. Numeric months — `6 months`
5. Text months — `three months`
6. Month–Month ranges — `Jun 2023 – Aug 2023`
7. Year–Year ranges — `2022 – 2024`
8. Short year format — `2022–23`
9. Month–Present — `Jan 2024 – Present`
10. Single year with context — `Internship 2023`

**Experience → Seniority mapping:**

| Months | Level |
|---|---|
| 0 | Entry-Level |
| < 12 | Entry-Level |
| 12 – 35 | Junior |
| 36 – 71 | Mid-Level |
| 72+ | Senior |

---

### 🔍 Job Service (`job_service.py`)

Dual-source job fetcher with smart query generation, deduplication, and round-robin source diversification.

- **Adzuna:** Tries multiple keyword variants × date windows (7 days → 30 days fallback)
- **SerpAPI:** Uses platform-targeted queries (e.g. `"intern internshala"`, `"fresher naukri"`)
- **Deduplication:** Fingerprint-based (normalized title + company) + URL normalization
- **Diversification:** Round-robin across sources so no single portal dominates results
- **Caching:** In-memory 5-minute cache to avoid redundant API calls

---

### 🛡️ Safety Agent (`safety_agent.py`)

Three-layer pipeline to detect fake/scam job postings:

```
Layer 1 — Heuristics (regex, instant)
  → Payment requests, urgency tactics, phishing attempts,
    unrealistic salaries, WhatsApp-only channels, generic HR emails

Layer 2 — FAISS Vector Similarity (fast)
  → Compares job text against 32 known scam-phrase embeddings
  → Uses all-MiniLM-L6-v2 + cosine similarity (threshold: 0.50)

Layer 3 — LLM Behavioral Analysis (optional, ~2–5s)
  → Sends job snippet to local Ollama model
  → Returns trust_level + red_flags in structured JSON

Trust Score = 100 − heuristic_penalty − faiss_penalty − llm_penalty + source_bonus
```

| Score | Level | Verdict |
|---|---|---|
| ≥ 70 | High | ✅ Legitimate |
| 45–69 | Medium | ⚠️ Review Carefully |
| < 45 | Low | 🚨 Likely Scam |

---

### 📧 Notifier (`notifier.py`)

- Sends rich dark-themed HTML job alert emails via Gmail SMTP
- Supports retry logic (configurable, default 2 attempts)
- Daily cron scheduler via APScheduler
- Deduplicates alerts using the SQLite history database

---

## 🖥️ Usage Guide

### Step 1 — Upload Resume
Go to the **Resume Analysis** tab → upload a `.pdf` or `.docx` file.

The app will display:
- Extracted skills
- ATS score with suggestions
- Detected experience (years + seniority level)
- AI candidate profile analysis
- Auto-detected target role

### Step 2 — Find Jobs
Go to the **Job Discovery** tab → optionally change location → click **Find Jobs**.

Each job card shows:
- Source portal badge (color-coded)
- Remote / Internship / Trusted badges
- Safety Agent verdict with trust score
- AI match score (0–100%) with explanation
- Direct apply link

### Step 3 — Email Results (optional)
Enter your email in the field below the results and click **Send Jobs to Email** to receive a formatted HTML digest.

### Step 4 — Subscribe to Daily Alerts (optional)
In the sidebar, enter your email, set a preferred time, and click **Subscribe to Daily Alerts**.

---

## 🔧 Configuration Options (Sidebar)

| Setting | Description |
|---|---|
| **LLM Model** | Choose from `gemma3:1b` (fast), `llama3`, `mistral`, `neural-chat` |
| **Notification Email** | Email for job digests |
| **Fake-job detection** | Toggle heuristic + FAISS safety checks |
| **Deep LLM analysis** | Toggle LLM layer of safety agent (slower but deeper) |
| **Alert Time** | Hour / Minute / AM-PM for daily scheduled alerts |

---

## 🧪 Testing & Debugging

```bash
# Test API connectivity
python debug/test_apis.py

# Test Adzuna + SerpAPI integration end-to-end
python debug/test_integration.py

# Debug SerpAPI query output and link extraction
python debug/debug_serp.py
python debug/debug_serp2.py

# Check for Adzuna ↔ SerpAPI URL overlap
python debug/debug_overlap.py

# Test Ollama connection
python debug/test_ollama_api.py

# Verify SerpAPI account & search credits
python debug/test_serpapi.py
```

---

## ❓ Troubleshooting

| Issue | Fix |
|---|---|
| `Ollama connection error` | Make sure Ollama is running: `ollama serve` |
| `Model not found` | Run `ollama pull gemma3:1b` and `ollama pull nomic-embed-text` |
| `No jobs found` | Check `.env` has valid API keys; try a broader role or location |
| `Email not sent` | Use a Gmail App Password (not your regular password); check `SENDER_EMAIL` and `SENDER_PASSWORD` in `.env` |
| `Adzuna 401 error` | Verify `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` are correct |
| `SerpAPI 429 error` | Monthly search limit reached; upgrade plan or wait for reset |
| `Embeddings failed` | Ensure `nomic-embed-text` is pulled and Ollama is running |

---

## 🗺️ Roadmap

- [ ] Chrome Extension for one-click job saving
- [ ] Resume auto-tailoring per job description
- [ ] LinkedIn job scraping integration
- [ ] Multi-resume profile management
- [ ] Cover letter generation per job
- [ ] Interview question prep based on job description
- [ ] Job application tracker board (Kanban)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push and open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [Ollama](https://ollama.com) — local LLM inference
- [Adzuna API](https://developer.adzuna.com/) — job listings
- [SerpAPI](https://serpapi.com) — Google Jobs scraping
- [FAISS](https://github.com/facebookresearch/faiss) — vector similarity search
- [Sentence Transformers](https://www.sbert.net/) — embedding models
- [Streamlit](https://streamlit.io) — UI framework

---

<div align="center">
  Made with ❤️ for job seekers everywhere
</div>

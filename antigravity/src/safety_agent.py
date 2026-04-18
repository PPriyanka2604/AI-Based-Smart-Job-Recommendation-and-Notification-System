"""
🛡️ Safety Agent — Fake Job Detection
======================================
Performs multi-layer validation on job postings:
  1. Heuristic scam pattern detection (fast, regex-based)
  2. FAISS vector similarity against a scam-pattern knowledge base
  3. LLM behavioral analysis via Ollama (deep assessment)

Trust levels returned:
  ✅ High     – Legitimate looking, no red flags
  ⚠️ Medium   – Minor concerns, review before applying
  🚨 Low      – Multiple red flags, likely scam/suspicious
"""

import re
import json
import requests
import numpy as np
from typing import Optional

# ─── Lazy imports to avoid slow startup ──────────────────────
_embedder = None
_faiss_index = None
_faiss_patterns = []


# ═══════════════════════════════════════════════════════════════
#  SCAM KNOWLEDGE BASE  (FAISS vector store)
# ═══════════════════════════════════════════════════════════════

SCAM_PATTERNS = [
    # Payment / money requests
    "pay registration fee to get started",
    "send money western union to receive your kit",
    "deposit required before training begins",
    "pay upfront for work from home materials",
    "processing fee to receive offer letter",
    "invest money to earn high returns working from home",
    "pay for your own background check to proceed",
    "wire transfer required for equipment deposit",
    # Unrealistic offers
    "earn 50000 per week working from home with no experience",
    "no experience required earn lakhs per month",
    "work 2 hours a day earn full time salary",
    "guaranteed salary regardless of performance",
    "part time work from home unlimited earning potential",
    "make money fast no skills needed apply now",
    # Urgency & pressure tactics
    "limited slots available apply immediately",
    "offer expires today act now",
    "only 5 positions left confirm your seat now",
    "interview waived immediate joining required",
    "whatsapp your cv immediately to get hired today",
    # Credential phishing
    "send your aadhar pan and bank details to hr",
    "provide your bank account for salary setup before joining",
    "submit your personal documents to claim signing bonus",
    "share otp to verify your job application status",
    # Vague company / suspicious contact
    "contact hr on whatsapp for immediate selection",
    "no office address work entirely from home forever",
    "company registered last month hiring 1000 employees",
    "gmail yahoo email for company hr contact",
    "respond to this whatsapp number to get shortlisted",
    # Content quality
    "job description copied from multiple companies",
    "salary negotiable no benefits mentioned vague role",
    "zero day experience fresher salary 80000 per month",
    "no technical skills required for software developer role",
]


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def _get_faiss_index():
    global _faiss_index, _faiss_patterns
    if _faiss_index is None:
        import faiss
        embedder = _get_embedder()
        vecs = embedder.encode(SCAM_PATTERNS, convert_to_numpy=True, normalize_embeddings=True)
        dim = vecs.shape[1]
        index = faiss.IndexFlatIP(dim)   # inner-product on normalized = cosine similarity
        index.add(vecs.astype(np.float32))
        _faiss_index = index
        _faiss_patterns = SCAM_PATTERNS
    return _faiss_index


# ═══════════════════════════════════════════════════════════════
#  HEURISTIC CHECKS
# ═══════════════════════════════════════════════════════════════

_PAYMENT_PATTERNS = re.compile(
    r'\b(pay|fee|deposit|registration fee|send money|wire transfer|western union|'
    r'processing charge|upfront payment|invest|wallet)\b',
    re.I
)
_URGENCY_PATTERNS = re.compile(
    r'\b(apply immediately|act now|limited slots|today only|urgent hiring|'
    r'immediate joining|confirm seat|don.t miss|offer expires|last date today)\b',
    re.I
)
_PHISHING_PATTERNS = re.compile(
    r'\b(aadhar|pan card|bank account number|otp|share your password|'
    r'date of birth.*email|send documents to whatsapp)\b',
    re.I
)
_UNREALISTIC_SALARY = re.compile(
    r'\b(\d{4,6})\s*(per\s+hour|\/hr|per\s+week|\/week)\b.*\bno\s+experience\b|'
    r'\bearn\s+\d+ lakh\b.*\bfresher\b|\b(unlimited|guaranteed)\s+earning\b',
    re.I
)
_WHATSAPP_ONLY = re.compile(r'\bwhatsapp\b.{0,40}\b(apply|contact|send|cv|resume)\b', re.I)
_GENERIC_EMAIL  = re.compile(r'hr\s*@\s*(gmail|yahoo|hotmail|rediff)\.com', re.I)

def _heuristic_flags(text: str) -> list[str]:
    flags = []
    if _PAYMENT_PATTERNS.search(text):   flags.append("💸 Payment request detected")
    if _URGENCY_PATTERNS.search(text):   flags.append("⏰ Urgency/pressure tactic")
    if _PHISHING_PATTERNS.search(text):  flags.append("🎣 Personal data/credential request")
    if _UNREALISTIC_SALARY.search(text): flags.append("💰 Unrealistic salary / no-experience promise")
    if _WHATSAPP_ONLY.search(text):      flags.append("📱 WhatsApp-only application channel")
    if _GENERIC_EMAIL.search(text):      flags.append("📧 Generic email (gmail/yahoo) as company HR")
    return flags


# ═══════════════════════════════════════════════════════════════
#  FAISS SIMILARITY CHECK
# ═══════════════════════════════════════════════════════════════

def _faiss_scam_score(text: str, top_k: int = 3) -> tuple[float, list[str]]:
    """
    Returns (max_similarity_0_to_1, [matched_pattern_strings]).
    Similarity > 0.60 is suspicious.
    """
    try:
        import faiss
        index    = _get_faiss_index()
        embedder = _get_embedder()
        # Truncate to first 500 chars for speed
        vec = embedder.encode([text[:500]], convert_to_numpy=True, normalize_embeddings=True)
        scores, indices = index.search(vec.astype(np.float32), top_k)
        top_scores   = scores[0].tolist()
        top_patterns = [_faiss_patterns[i] for i in indices[0] if i >= 0]
        max_score    = max(top_scores) if top_scores else 0.0
        # Only return patterns that actually scored high
        matched = [p for p, s in zip(top_patterns, top_scores) if s > 0.50]
        return float(max_score), matched
    except Exception as e:
        print(f"[SafetyAgent] FAISS error: {e}")
        return 0.0, []


# ═══════════════════════════════════════════════════════════════
#  LLM BEHAVIORAL ANALYSIS
# ═══════════════════════════════════════════════════════════════

def _llm_analyze(title: str, company: str, description: str, ollama_model: str = "gemma3:1b") -> dict:
    """
    Send a concise prompt to Ollama and get a JSON trust assessment.
    Returns dict with keys: trust_level, reason, red_flags (list).
    """
    snippet = f"Title: {title}\nCompany: {company}\nDescription: {description[:600]}"
    prompt = (
        "You are a job scam detection expert. Analyze this job posting and respond ONLY in JSON.\n\n"
        f"{snippet}\n\n"
        "Return JSON with exactly these keys:\n"
        '{"trust_level":"High|Medium|Low","reason":"one sentence","red_flags":["flag1","flag2"]}\n'
        "If no red flags, return empty list. Be concise."
    )
    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model":  ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_ctx": 1024, "num_predict": 150, "temperature": 0.1},
            },
            timeout=30,
        )
        raw = r.json().get("response", "")
        # Extract JSON from response
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"[SafetyAgent] LLM error: {e}")
    return {"trust_level": "Medium", "reason": "Could not analyze.", "red_flags": []}


# ═══════════════════════════════════════════════════════════════
#  MAIN SAFETY AGENT CLASS
# ═══════════════════════════════════════════════════════════════

class SafetyAgent:
    """
    Comprehensive fake-job detection agent.

    Usage:
        agent  = SafetyAgent(ollama_model="gemma3:1b")
        report = agent.analyze(job)
        # report = {
        #   "trust_level": "High" | "Medium" | "Low",
        #   "trust_score": 0-100,
        #   "verdict":     "✅ Legitimate" | "⚠️ Suspicious" | "🚨 Likely Scam",
        #   "heuristic_flags": [...],
        #   "similar_scam_patterns": [...],
        #   "llm_reason": "...",
        #   "llm_red_flags": [...],
        # }
    """

    def __init__(self, ollama_model: str = "gemma3:1b", use_llm: bool = True):
        self.ollama_model = ollama_model
        self.use_llm      = use_llm

    def analyze(self, job: dict) -> dict:
        title       = job.get("title", "")
        company     = job.get("company", "")
        description = job.get("description", "")
        source      = job.get("source", "")
        apply_link  = job.get("apply_link", "")
        trusted     = job.get("trusted", False)

        full_text = f"{title} {company} {description} {apply_link}".lower()

        # ── Layer 1: Heuristic flags ─────────────────────────────
        h_flags = _heuristic_flags(full_text)
        h_score = max(0, 100 - len(h_flags) * 25)   # -25 pts per heuristic flag

        # ── Layer 2: FAISS scam similarity ──────────────────────
        faiss_sim, similar_patterns = _faiss_scam_score(full_text)
        # Convert similarity → penalty: 0.0→0pts, 0.6→20pts, 0.8→40pts, 1.0→60pts
        faiss_penalty = int(min(60, faiss_sim * 75))

        # ── Layer 3: Trusted source bonus ───────────────────────
        source_bonus = 15 if trusted else 0

        # ── Layer 4: LLM assessment ──────────────────────────────
        llm_result = {"trust_level": "Medium", "reason": "Not analyzed.", "red_flags": []}
        llm_penalty = 0
        if self.use_llm and description:
            llm_result  = _llm_analyze(title, company, description, self.ollama_model)
            llm_level   = llm_result.get("trust_level", "Medium")
            llm_flags   = llm_result.get("red_flags", [])
            llm_penalty = {"High": 0, "Medium": 10, "Low": 30}.get(llm_level, 10)
            llm_penalty += len(llm_flags) * 5

        # ── Composite trust score ────────────────────────────────
        raw_score   = h_score - faiss_penalty - llm_penalty + source_bonus
        trust_score = max(0, min(100, raw_score))

        # ── Trust level + verdict ────────────────────────────────
        if trust_score >= 70:
            trust_level = "High"
            verdict     = "✅ Legitimate"
        elif trust_score >= 45:
            trust_level = "Medium"
            verdict     = "⚠️ Review Carefully"
        else:
            trust_level = "Low"
            verdict     = "🚨 Likely Scam"

        return {
            "trust_level":            trust_level,
            "trust_score":            trust_score,
            "verdict":                verdict,
            "heuristic_flags":        h_flags,
            "similar_scam_patterns":  similar_patterns,
            "llm_reason":             llm_result.get("reason", ""),
            "llm_red_flags":          llm_result.get("red_flags", []),
            "faiss_similarity":       round(faiss_sim, 2),
        }

    def batch_analyze(self, jobs: list[dict]) -> list[dict]:
        """Analyze a list of jobs and return reports in the same order."""
        return [self.analyze(j) for j in jobs]

    @staticmethod
    def trust_badge_html(report: dict) -> str:
        """Returns an HTML badge to embed in Streamlit markdown."""
        level = report.get("trust_level", "Medium")
        score = report.get("trust_score", 50)
        color = {"High": "#2e7d32", "Medium": "#e65100", "Low": "#b71c1c"}.get(level, "#546e7a")
        icon  = {"High": "🛡️",      "Medium": "⚠️",      "Low": "🚨"}.get(level, "❓")
        verdict = report.get("verdict", "")
        return (
            f"<span style='background:{color};color:white;padding:3px 10px;"
            f"border-radius:12px;font-size:0.72rem;font-weight:bold'>"
            f"{icon} {verdict} ({score}/100)</span>"
        )

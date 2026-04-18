import streamlit as st
import os
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from src.parser import ResumeParser
from src.llm import LLMManager
from src.job_service import JobService
from src.rag_matcher import RAGMatcher
from src.database import DatabaseManager
from src.notifier import Notifier
from src.safety_agent import SafetyAgent
from dotenv import load_dotenv

load_dotenv(override=True)

st.set_page_config(page_title="AI Smart Job Assistant", page_icon="🚀", layout="wide")


def make_components(model_name):
    return {
        "parser":       ResumeParser(),
        "llm":          LLMManager(model=model_name),
        "job_service":  JobService(),
        "matcher":      RAGMatcher(),
        "db":           DatabaseManager(),
        "notifier":     Notifier(),
        "safety_agent": SafetyAgent(ollama_model=model_name, use_llm=False),
    }


# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")

    llm_model  = st.selectbox("LLM Model",
        ["llama3", "gemma3:1b", "mistral", "neural-chat"], index=1)
    user_email = st.text_input("📧 Notification Email")

    st.markdown("---")
    st.subheader("🔌 API Status")

    load_dotenv(override=True)
    az_ok = bool(os.getenv("ADZUNA_APP_ID", "").strip() and os.getenv("ADZUNA_APP_KEY", "").strip())
    sp_ok = bool(os.getenv("SERPAPI_KEY", "").strip())

    st.markdown(
        f"{'✅' if az_ok else '❌'} **Adzuna** — Direct job listings & company sites  \n"
        f"{'✅' if sp_ok else '❌'} **SerpAPI** — Internshala · Wellfound · Naukri · Unstop · Glassdoor"
    )
    if not az_ok and not sp_ok:
        st.error("Add ADZUNA_APP_ID + ADZUNA_APP_KEY and/or SERPAPI_KEY to your `.env` file.")

    st.markdown("---")
    st.subheader("🛡️ Safety Agent")
    use_safety     = st.toggle("Fake-job detection", value=True)
    use_llm_safety = st.toggle("Deep LLM analysis (slower)", value=False)

    st.markdown("---")
    st.subheader("📧 Job Alerts")
    alert_email  = st.text_input("Alert email", value=user_email, key="alert_email")
    col1, col2, col3 = st.columns(3)
    with col1:
        alert_hour   = st.number_input("Hour",   min_value=1, max_value=12, value=8, step=1)
    with col2:
        alert_minute = st.number_input("Minute", min_value=0, max_value=59, value=0, step=1)
    with col3:
        alert_ampm   = st.selectbox("AM/PM", ["AM", "PM"])

    hour_24 = (alert_hour if alert_hour != 12 else 0) if alert_ampm == "AM" \
              else (alert_hour + 12 if alert_hour != 12 else 12)

    detected_role  = st.session_state.get("detected_role")
    detected_level = st.session_state.get("parsed_data", {}).get("experience_level")

    if st.button("🔔 Subscribe to Daily Alerts"):
        if not alert_email:
            st.error("Enter your email.")
        elif not detected_role:
            st.error("Upload a resume first.")
        else:
            if "notifier" not in st.session_state:
                st.session_state.notifier = Notifier()
            if not st.session_state.get("alert_subscribed", False):
                st.session_state.notifier.start_daily_scheduler(
                    alert_email, detected_role, detected_level, hour_24, alert_minute)
                st.session_state.alert_subscribed = True
                st.success(f"Subscribed at {alert_hour}:{alert_minute:02d} {alert_ampm}.")
            else:
                st.info("Already subscribed.")

    if st.session_state.get("alert_subscribed", False):
        if st.button("❌ Unsubscribe"):
            st.session_state.notifier.stop_scheduler()
            st.session_state.alert_subscribed = False
            st.success("Unsubscribed.")


# ── Components ────────────────────────────────────────────────
if st.session_state.get("_llm_model") != llm_model or "components" not in st.session_state:
    st.session_state.components    = make_components(llm_model)
    st.session_state["_llm_model"] = llm_model
components = st.session_state.components


# ── Main UI ───────────────────────────────────────────────────
st.title("🚀 AI SMART JOB RECOMMENDATION AND NOTIFICATION SYSTEM")
st.markdown("Analyze your resume, discover matching roles, and manage your job alerts in one place.")

tabs = st.tabs(["📄 Resume Analysis", "🔍 Job Discovery", "📜 Search History"])


# ── TAB 1: RESUME ANALYSIS ────────────────────────────────────
with tabs[0]:
    uploaded_file = st.file_uploader("Choose a PDF or DOCX file", type=["pdf", "docx"])

    if uploaded_file:
        with st.spinner("Analyzing resume..."):
            parsed_data = components["parser"].parse_resume(
                uploaded_file, file_name=uploaded_file.name)
            st.session_state["parsed_data"] = parsed_data

            st.subheader("🛠️ Extracted Skills")
            st.write(components["llm"].extract_skills(parsed_data["text"]))

            st.subheader("📊 ATS Score & Suggestions")
            st.write(components["llm"].analyze_resume(parsed_data["text"]))

            st.markdown("### 🗂️ Experience Analysis")
            exp_level = parsed_data.get("experience_level", "Unknown")
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Detected Experience", parsed_data.get("experience_display","0 Months"))
            with c2:
                st.metric("Seniority Level", exp_level)

            badge_color = {
                "Entry-Level": "#1565c0", "Junior": "#2e7d32",
                "Mid-Level":   "#e65100", "Senior": "#6a1b9a",
            }.get(exp_level, "#37474f")
            st.markdown(
                f"<span style='background:{badge_color};color:white;padding:4px 16px;"
                f"border-radius:12px;font-weight:bold;font-size:0.9rem'>🎓 {exp_level}</span>",
                unsafe_allow_html=True)

            st.markdown(components["llm"].analyze_candidate_profile(
                parsed_data["text"],
                parsed_data.get("experience_level"),
                parsed_data.get("total_experience_years")))

            detected_role = components["llm"].detect_role_only(parsed_data["text"])
            st.session_state["detected_role"] = detected_role

            lvl_l = exp_level.lower()
            if "entry" in lvl_l or "fresher" in lvl_l:
                mode_hint = "🎓 Will fetch internships + fresher jobs + entry-level roles"
            elif "junior" in lvl_l:
                mode_hint = "💼 Will fetch junior + entry-level roles"
            elif "senior" in lvl_l or "lead" in lvl_l:
                mode_hint = "🏆 Will fetch senior + lead roles"
            else:
                mode_hint = "💼 Will fetch mid-level roles"

            st.info(f"🎯 **Target Role:** {detected_role}  |  {mode_hint}")


# ── TAB 2: JOB DISCOVERY ─────────────────────────────────────
with tabs[1]:
    st.header("🔍 Discover Relevant Jobs")

    query = st.session_state.get("detected_role")
    level = st.session_state.get("parsed_data", {}).get("experience_level")

    if not query:
        st.warning("📄 Upload and analyze your resume first.")
    else:
        lvl_l = (level or "").lower()
        if "entry" in lvl_l or "fresher" in lvl_l:
            hint = "🎓 Fetching internships + fresher jobs + entry-level from all platforms"
        elif "junior" in lvl_l:
            hint = "💼 Fetching junior + entry-level roles from all platforms"
        elif "senior" in lvl_l or "lead" in lvl_l:
            hint = "🏆 Fetching senior + lead roles from all platforms"
        else:
            hint = "💼 Fetching mid-level roles from all platforms"

        active = []
        if os.getenv("ADZUNA_APP_ID","").strip() and os.getenv("ADZUNA_APP_KEY","").strip():
            active.append("Adzuna (Direct company listings · Global jobs)")
        if os.getenv("SERPAPI_KEY","").strip():
            active.append("SerpAPI (Internshala · Wellfound · Naukri · Unstop · Google Jobs)")
        st.info(f"{hint}\n\n📡 **Sources:** {' + '.join(active)}" if active else hint)

    col_btn, col_loc = st.columns([1, 2])
    with col_btn:
        find_clicked = st.button("🔍 Find Jobs", disabled=not query)
    with col_loc:
        location = st.text_input("Location", value="India", label_visibility="collapsed")

    if find_clicked and query:
        progress_bar = st.progress(0, text="Starting job search...")

        with st.spinner(f"Fetching 100 {level or 'matching'} jobs for '{query}'..."):
            progress_bar.progress(20, text="Querying Adzuna (direct company listings)...")
            jobs = components["job_service"].fetch_jobs(
                role=query, level=level, location=location, num_results=100)
            progress_bar.progress(70, text="Querying SerpAPI (Internshala, Wellfound, Naukri)...")

        progress_bar.progress(90, text="Ranking by resume match...")

        if isinstance(jobs, dict) and "error" in jobs:
            st.error(jobs["error"])
            progress_bar.empty()
        elif not jobs:
            st.info("No jobs found. Try a broader role title.")
            progress_bar.empty()
        else:
            # RAG ranking
            components["matcher"].create_index(jobs)
            matches = components["matcher"].match_jobs(
                st.session_state["parsed_data"]["text"], top_k=len(jobs))
            display_jobs = matches if matches else jobs
            progress_bar.progress(100, text="Done!")

            st.success(f"✅ Found **{len(display_jobs)} unique** postings ranked by resume match!")

            # Source breakdown
            src_counts = Counter(j["source"] for j in display_jobs)
            pills = "  ".join(
                f"<span style='background:#1e3a4a;color:#80cbc4;padding:3px 10px;"
                f"border-radius:8px;font-size:0.75rem;font-weight:bold'>{s} ×{c}</span>"
                for s, c in src_counts.most_common()
            )
            st.markdown(f"**Portals ({len(src_counts)}):** {pills}", unsafe_allow_html=True)

            # Type breakdown (jobs vs internships)
            type_counts = Counter(
                "Internship" if "intern" in j.get("employment_type","").lower()
                             or "intern" in j.get("title","").lower()
                else "Job"
                for j in display_jobs
            )
            st.markdown(
                f"**Type:** 💼 Jobs: **{type_counts.get('Job',0)}**  "
                f"  🎓 Internships: **{type_counts.get('Internship',0)}**"
            )

            # 📧 Send jobs to email button
            email_col1, email_col2 = st.columns([2, 1])
            with email_col1:
                email_to = st.text_input(
                    "📧 Email results to",
                    value=user_email or "",
                    key="email_jobs_to",
                    label_visibility="collapsed",
                    placeholder="Enter email to receive these jobs",
                )
            with email_col2:
                if st.button("📧 Send Jobs to Email"):
                    if not email_to:
                        st.error("Enter an email address.")
                    elif not os.getenv("SENDER_PASSWORD", "").strip() or os.getenv("SENDER_PASSWORD", "").strip() == "your_gmail_app_password_here":
                        st.error("Set your Gmail App Password in `.env` as SENDER_PASSWORD to send emails.")
                    else:
                        from src.notifier import send_job_notification
                        with st.spinner("Sending email..."):
                            sent = send_job_notification(
                                receiver_email=email_to,
                                jobs=display_jobs[:20],  # Send top 20 matches
                                role=st.session_state.get("detected_role", ""),
                                level=st.session_state.get("parsed_data", {}).get("experience_level", ""),
                            )
                        if sent:
                            st.success(f"✅ Jobs emailed to {email_to}!")
                        else:
                            st.error("❌ Failed to send email. Check your SENDER_PASSWORD in .env.")

            st.divider()

            for i, job in enumerate(display_jobs):
                with st.container(border=True):
                    # AI match score
                    with st.spinner(f"Scoring {i+1}/{len(display_jobs)}..."):
                        match_str = components["llm"].semantic_job_score(
                            st.session_state["parsed_data"]["text"],
                            job.get("description", ""),
                            job.get("title", "")
                        )
                        match_data = {}
                        try:
                            # Robust JSON extraction
                            json_match = re.search(r'\{.*\}', match_str, re.DOTALL)
                            if not json_match: # Fallback for simpler models
                                json_match = re.search(r'\{.*\}', match_str, re.DOTALL)
                            
                            if json_match:
                                clean = json_match.group().strip()
                                match_data = json.loads(clean)
                        except:
                            pass
                        
                        score = match_data.get("match_score", 0)
                        # If score is still 0 but there's an explanation, it might be a valid 0
                        # but if everything is missing, it's likely a failure.

                    # 🛡️ Safety Agent check
                    safety_report = None
                    if use_safety:
                        components["safety_agent"].use_llm = use_llm_safety
                        safety_report = components["safety_agent"].analyze(job)

                    col1, col2 = st.columns([4, 1])
                    with col1:
                        # Badges
                        src_colors = {
                            "LinkedIn":     "#0077b5",
                            "Indeed":       "#003a9b",
                            "Glassdoor":    "#0caa41",
                            "Naukri":       "#ff7555",
                            "Internshala":  "#43a047",
                            "Wellfound":    "#555555",
                            "Unstop":       "#7c4dff",
                            "Adzuna":       "#546e7a",
                        }
                        src_color = src_colors.get(job.get("source",""), "#546e7a")
                        badges = f"<span style='background:{src_color};color:white;padding:2px 10px;border-radius:12px;font-size:0.72rem;font-weight:bold'>🔗 {job.get('source','')}</span>"
                        
                        if job.get("trusted"):
                            badges += " <span style='background:#2e7d32;color:white;padding:2px 8px;border-radius:12px;font-size:0.72rem'>✅ Trusted</span>"
                        
                        if safety_report:
                            badges += " " + SafetyAgent.trust_badge_html(safety_report)
                            
                        st.markdown(badges, unsafe_allow_html=True)
                        st.subheader(job.get("title", ""))
                        st.write(f"🏢 **{job.get('company','')}**")
                        st.write(f"📍 {job.get('location','Remote/Hybrid')}")
                        if job.get("apply_link"):
                            st.markdown(f"🔗 [Apply Now]({job['apply_link']})", unsafe_allow_html=True)

                    with col2:
                        st.metric("Match", f"{score}%")
                        if "detailed_explanation" in match_data:
                            with st.popover("🧠 Detailed Match Analysis"):
                                st.markdown(f"**Reasoning:**\n{match_data['detailed_explanation']}")
                                if "seniority_alignment" in match_data:
                                    st.write(f"📈 **Seniority:** {match_data['seniority_alignment']}")
                                if "domain_alignment" in match_data:
                                    st.write(f"🏢 **Domain:** {match_data['domain_alignment']}")
                        
                    # Expanded details
                    col_det1, col_det2 = st.columns([1, 1])
                    with col_det1:
                        if "key_matching_skills" in match_data and match_data["key_matching_skills"]:
                            with st.expander("🛠️ Skills Matched"):
                                st.write(", ".join(match_data["key_matching_skills"]))
                    with col_det2:
                        if "missing_skills" in match_data and match_data["missing_skills"]:
                            with st.expander("⚠️ Missing Skills (Gaps)"):
                                st.write(", ".join(match_data["missing_skills"]))
                                
                    if safety_report:
                        with st.expander(f"🛡️ Safety Analysis (Score: {safety_report['trust_score']}/100)"):
                            if safety_report.get("heuristic_flags"):
                                st.markdown("**Pattern Match Red Flags:**")
                                for fl in safety_report["heuristic_flags"]: st.markdown(f"- {fl}")
                            
                            if safety_report.get("llm_reason"):
                                st.info(f"**Safety Agent Logic:** {safety_report['llm_reason']}")
                            
                            if safety_report.get("llm_red_flags"):
                                st.warning("🤖 LLM Behavioral Risks:")
                                for fl in safety_report["llm_red_flags"]: st.markdown(f"- {fl}")
                            
                            if not safety_report.get("heuristic_flags") and not safety_report.get("llm_red_flags"):
                                st.success("🛡️ No scam patterns or behavioral risks detected.")
                    
                    st.markdown("<br>", unsafe_allow_html=True)

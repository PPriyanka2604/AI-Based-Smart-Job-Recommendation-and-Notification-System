"""
📧 SMTP Email Notification Module
===================================
Sends job alert emails to users when matching jobs are found.

Tech:  smtplib + Gmail SMTP (smtp.gmail.com:587) + App Password auth
Email: Beautiful HTML template with job cards
Extra: Retry logic, daily scheduler, logging, modular design

Integration:
    from src.notifier import Notifier, send_job_notification
    send_job_notification("user@gmail.com", jobs_list)
"""

import smtplib
import os
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# ── Optional: scheduler for daily alerts ─────────────────────
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    HAS_SCHEDULER = True
except ImportError:
    HAS_SCHEDULER = False

load_dotenv(override=True)

# ── Logging setup ────────────────────────────────────────────
logger = logging.getLogger("notifier")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# ═══════════════════════════════════════════════════════════════
#  HTML EMAIL TEMPLATE
# ═══════════════════════════════════════════════════════════════

def _build_html_email(jobs: list[dict], role: str = "", level: str = "") -> str:
    """
    Builds a beautiful HTML email body with job cards.
    Each job dict should have: title, company, apply_link, location (optional),
    source (optional), employment_type (optional).
    """
    now_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    role_str = f" for <strong>{role}</strong>" if role else ""
    level_str = f" ({level})" if level else ""

    # Build job rows
    job_rows = ""
    for i, job in enumerate(jobs, 1):
        title    = job.get("title", "Untitled")
        company  = job.get("company", "Unknown Company")
        link     = job.get("apply_link", "#")
        location = job.get("location", "")
        source   = job.get("source", "")
        emp_type = job.get("employment_type", "")

        # Source badge color
        src_colors = {
            "LinkedIn": "#0077b5", "Indeed": "#003a9b", "Glassdoor": "#0caa41",
            "Naukri": "#ff7555", "Internshala": "#43a047", "Wellfound": "#555",
            "Unstop": "#7c4dff", "Adzuna": "#546e7a",
        }
        src_color = src_colors.get(source, "#607d8b")

        loc_html = f"<span style='color:#90a4ae;font-size:13px'>📍 {location}</span>" if location else ""
        src_html = (
            f"<span style='background:{src_color};color:white;padding:2px 8px;"
            f"border-radius:10px;font-size:11px;font-weight:bold'>{source}</span>"
        ) if source else ""
        emp_html = (
            f"<span style='background:#263238;color:#b0bec5;padding:2px 8px;"
            f"border-radius:10px;font-size:11px'>{emp_type}</span>"
        ) if emp_type else ""

        job_rows += f"""
        <tr>
          <td style="padding:12px 16px;border-bottom:1px solid #263238">
            <div style="font-size:15px;font-weight:bold;color:#e0e0e0;margin-bottom:4px">
              {i}. {title}
            </div>
            <div style="font-size:13px;color:#90a4ae;margin-bottom:6px">
              🏢 {company} &nbsp; {loc_html}
            </div>
            <div style="margin-bottom:8px">
              {src_html} {emp_html}
            </div>
            <a href="{link}"
               style="display:inline-block;background:#4CAF50;color:white;padding:6px 18px;
                      border-radius:6px;text-decoration:none;font-size:13px;font-weight:bold">
              🔗 Apply Now
            </a>
          </td>
        </tr>"""

    html = f"""
    <html>
    <body style="margin:0;padding:0;background:#0e1117;font-family:'Segoe UI',Arial,sans-serif">
      <div style="max-width:600px;margin:20px auto;background:#1a1a2e;border-radius:12px;
                  border:1px solid #263238;overflow:hidden">

        <!-- Header -->
        <div style="background:linear-gradient(135deg,#1565c0,#4CAF50);
                    padding:24px 20px;text-align:center">
          <h1 style="color:white;margin:0;font-size:22px">🚀 New Job Alerts</h1>
          <p style="color:#e0f7fa;margin:6px 0 0;font-size:14px">
            Matching jobs{role_str}{level_str}
          </p>
        </div>

        <!-- Intro -->
        <div style="padding:16px 20px;color:#b0bec5;font-size:14px;border-bottom:1px solid #263238">
          Hi there! 👋<br><br>
          We found <strong style="color:#4CAF50">{len(jobs)} new job{'' if len(jobs)==1 else 's'}</strong>
          matching your profile. Here are your top recommendations:
        </div>

        <!-- Job List -->
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background:#0e1117">
          {job_rows}
        </table>

        <!-- Footer -->
        <div style="padding:16px 20px;text-align:center;color:#546e7a;font-size:12px;
                    border-top:1px solid #263238">
          Sent on {now_str}<br>
          <span style="color:#78909c">AI Smart Job Assistant</span> •
          <span style="color:#78909c">Powered by Adzuna + SerpAPI + Ollama</span><br><br>
          <span style="color:#455a64">
            To unsubscribe, disable alerts in the app sidebar.
          </span>
        </div>
      </div>
    </body>
    </html>"""
    return html


# ═══════════════════════════════════════════════════════════════
#  CORE EMAIL SENDING FUNCTION
# ═══════════════════════════════════════════════════════════════

def send_job_notification(
    receiver_email: str,
    jobs: list[dict],
    role: str = "",
    level: str = "",
    subject: str = "🚀 New Job Alerts Matching Your Skills",
    sender_email: str = None,
    sender_password: str = None,
    max_retries: int = 2,
) -> bool:
    """
    Send a job alert email to the user.

    Args:
        receiver_email : User's email address
        jobs           : List of job dicts with keys: title, company, apply_link
                         (optional: location, source, employment_type)
        role           : Target role (for personalization)
        level          : Experience level (for personalization)
        subject        : Email subject line
        sender_email   : Gmail address (falls back to SENDER_EMAIL env var)
        sender_password: Gmail App Password (falls back to SENDER_PASSWORD env var)
        max_retries    : Number of retry attempts if sending fails

    Returns:
        True if email was sent successfully, False otherwise.
    """
    # ── Resolve credentials from env if not provided ─────────
    sender_email    = sender_email    or os.getenv("SENDER_EMAIL", "")
    sender_password = sender_password or os.getenv("SENDER_PASSWORD", "")

    if not sender_email or not sender_password:
        logger.error("❌ Email credentials not configured. "
                     "Set SENDER_EMAIL and SENDER_PASSWORD in .env")
        return False

    if not receiver_email:
        logger.error("❌ No receiver email provided.")
        return False

    if not jobs:
        logger.info("📭 No jobs to send — skipping email.")
        return False

    # ── Build the email message ──────────────────────────────
    msg = MIMEMultipart("alternative")
    msg["From"]    = f"AI Smart Job Assistant <{sender_email}>"
    msg["To"]      = receiver_email
    msg["Subject"] = subject

    # Plain-text fallback for email clients that don't support HTML
    plain_body = f"New Job Alerts Matching Your Skills\n{'='*40}\n\n"
    for i, job in enumerate(jobs, 1):
        plain_body += (
            f"{i}. {job.get('title','Untitled')} at {job.get('company','Unknown')}\n"
            f"   Apply: {job.get('apply_link','#')}\n\n"
        )
    msg.attach(MIMEText(plain_body, "plain"))

    # HTML body (rich formatted)
    html_body = _build_html_email(jobs, role, level)
    msg.attach(MIMEText(html_body, "html"))

    # ── Send with retry logic ────────────────────────────────
    for attempt in range(1, max_retries + 1):
        try:
            # Connect to Gmail SMTP server with TLS
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
                server.ehlo()               # Identify ourselves to the server
                server.starttls()           # Upgrade connection to encrypted TLS
                server.ehlo()               # Re-identify after TLS
                server.login(sender_email, sender_password)  # Auth with App Password
                server.send_message(msg)    # Send the email

            logger.info(f"✅ Email sent to {receiver_email} ({len(jobs)} jobs)")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ Authentication failed. Check SENDER_PASSWORD "
                         f"(must be Gmail App Password, not regular password): {e}")
            return False  # Don't retry auth errors

        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"❌ Recipient refused ({receiver_email}): {e}")
            return False  # Don't retry invalid recipient

        except Exception as e:
            logger.warning(f"⚠️ Attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                wait = attempt * 3  # Exponential backoff: 3s, 6s
                logger.info(f"   Retrying in {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"❌ All {max_retries} attempts failed for {receiver_email}")
                return False

    return False


# ═══════════════════════════════════════════════════════════════
#  NOTIFIER CLASS (Streamlit integration + Daily Scheduler)
# ═══════════════════════════════════════════════════════════════

class Notifier:
    """
    Full notification service with:
    - One-shot email sending (send_job_notification)
    - Daily scheduled job alerts (start_daily_scheduler)
    - Automatic deduplication via DatabaseManager
    """

    def __init__(self):
        self.sender_email    = os.getenv("SENDER_EMAIL", "")
        self.sender_password = os.getenv("SENDER_PASSWORD", "")
        self._started        = False
        self._job_id         = None
        self._scheduler      = None

    def send_email(self, recipient_email: str, subject: str, body: str) -> bool:
        """Send a simple plain-text email (legacy interface)."""
        if not self.sender_email or not self.sender_password:
            logger.error("❌ Email credentials not configured.")
            return False

        msg = MIMEMultipart()
        msg["From"]    = self.sender_email
        msg["To"]      = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            logger.info(f"✅ Email sent to {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False

    def send_job_alert(self, receiver_email: str, jobs: list[dict],
                       role: str = "", level: str = "") -> bool:
        """Send a rich HTML job alert email using the reusable function."""
        return send_job_notification(
            receiver_email=receiver_email,
            jobs=jobs,
            role=role,
            level=level,
            sender_email=self.sender_email,
            sender_password=self.sender_password,
        )

    def check_for_new_jobs(self, user_email: str, role: str, level: str):
        """
        Fetch latest jobs, filter out duplicates, and email new ones.
        Called by the daily scheduler.
        """
        logger.info(f"🔍 [{user_email}] Checking for new jobs at {datetime.now()}...")

        from src.job_service import JobService
        from src.database import DatabaseManager

        job_service = JobService()
        db          = DatabaseManager()

        jobs = job_service.fetch_jobs(role, level=level)
        if isinstance(jobs, dict) and "error" in jobs:
            logger.error(f"❌ Error fetching jobs: {jobs['error']}")
            return

        logger.info(f"📦 Fetched {len(jobs)} jobs total.")

        # Filter out duplicates using job ID
        new_jobs = [job for job in jobs if not db.is_duplicate(job.get("id"))]
        logger.info(f"🆕 Found {len(new_jobs)} new jobs (not seen before).")

        if new_jobs:
            # Send the rich HTML email
            success = self.send_job_alert(user_email, new_jobs, role, level)
            if success:
                # Mark jobs as sent to avoid re-sending
                for job in new_jobs:
                    db.add_job_to_history(job)
                logger.info(f"✅ Sent {len(new_jobs)} new jobs to {user_email}")
            else:
                logger.error(f"❌ Failed to send alert to {user_email}")
        else:
            logger.info("📭 No new jobs to report.")

    def start_daily_scheduler(self, user_email: str, role: str, level: str,
                              hour: int, minute: int):
        """Start a background cron job that checks for new jobs daily."""
        if not HAS_SCHEDULER:
            logger.error("❌ apscheduler not installed. pip install apscheduler")
            return

        if self._started:
            logger.warning("⚠️ Scheduler already running.")
            return

        self._scheduler = BackgroundScheduler()
        trigger = CronTrigger(hour=hour, minute=minute)
        job = self._scheduler.add_job(
            self.check_for_new_jobs,
            trigger,
            args=[user_email, role, level],
            id=f"daily_{user_email}",
        )
        self._job_id = job.id
        self._scheduler.start()
        self._started = True
        logger.info(f"✅ Daily scheduler started for {user_email} at "
                    f"{hour:02d}:{minute:02d}. Current time: {datetime.now()}")

    def stop_scheduler(self):
        """Stop the daily scheduler."""
        if self._started and self._scheduler and self._job_id:
            self._scheduler.remove_job(self._job_id)
            self._scheduler.shutdown()
            self._started   = False
            self._job_id    = None
            self._scheduler = None
            logger.info("🛑 Scheduler stopped.")


# ═══════════════════════════════════════════════════════════════
#  EXAMPLE USAGE (run this file directly to test)
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Sample job data (same format as job_service.py returns)
    sample_jobs = [
        {
            "title":           "Software Engineer Intern",
            "company":         "Google",
            "apply_link":      "https://careers.google.com/jobs/123",
            "location":        "Bangalore, India",
            "source":          "LinkedIn",
            "employment_type": "Internship",
        },
        {
            "title":           "Junior Python Developer",
            "company":         "Infosys",
            "apply_link":      "https://naukri.com/job/456",
            "location":        "Hyderabad, India",
            "source":          "Naukri",
            "employment_type": "Full-time",
        },
        {
            "title":           "Software Developer Trainee",
            "company":         "TCS",
            "apply_link":      "https://internshala.com/internship/789",
            "location":        "Mumbai, India",
            "source":          "Internshala",
            "employment_type": "Internship",
        },
    ]

    # Quick test
    receiver = input("Enter your email address to test: ").strip()
    if receiver:
        result = send_job_notification(
            receiver_email=receiver,
            jobs=sample_jobs,
            role="Software Engineer",
            level="Entry-Level",
        )
        print(f"\nResult: {'✅ Sent!' if result else '❌ Failed'}")
    else:
        print("No email entered. Skipping test.")
        print("\nTo use programmatically:")
        print("  from src.notifier import send_job_notification")
        print("  send_job_notification('user@example.com', jobs)")
"""
🛡️ Realistic Product Design System
====================================
Professional, clean, and balanced interface for a high-end job portal.
Focuses on clarity, trust, and modern SaaS aesthetics.
"""

CSS_STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --primary: #10B981;
    --primary-light: #34D399;
    --background: #0B0E14;
    --surface: #151921;
    --surface-hover: #1C222D;
    --text-main: #F8FAFC;
    --text-muted: #94A3B8;
    --border: #2D3748;
    --border-bright: #3B82F6;
}

/* Global Animations */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideUp {
    from { transform: translateY(20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}

@keyframes gradientBG {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes pulseBorder {
    0% { border-color: var(--border); }
    50% { border-color: var(--primary); }
    100% { border-color: var(--border); }
}

/* Global Reset */
.main {
    background: linear-gradient(-45deg, #0B0E14, #151921, #0B0E14, #1E293B) !important;
    background-size: 400% 400% !important;
    animation: gradientBG 15s ease infinite !important;
    padding-top: 0 !important;
    animation: fadeIn 0.8s ease-out;
}

/* Dashboard Header Animation */
.dashboard-header {
    animation: slideUp 0.8s ease-out;
}

h1, h2, h3, h4, .stHeader {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: var(--text-main) !important;
    animation: fadeIn 1s ease-in;
}

p, span, div, .stMarkdown {
    font-family: 'Inter', sans-serif !important;
    color: var(--text-main);
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

/* Custom Job Card - SaaS Style */
.job-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    animation: slideUp 0.6s ease-out;
}

.job-card:hover {
    border-color: var(--border-bright);
    background: var(--surface-hover);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    transform: translateY(-5px) scale(1.01);
}

.job-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.company-name {
    color: var(--primary);
    font-size: 0.875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.job-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-main);
    margin: 2px 0;
}

.job-location {
    font-size: 0.85rem;
    color: var(--text-muted);
}

.job-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
}

.badge-group {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.badge {
    font-size: 0.75rem;
    font-weight: 500;
    padding: 2px 10px;
    border-radius: 6px;
    border: 1px solid transparent;
}

.badge-ai { background: rgba(59, 130, 246, 0.1); color: #60A5FA; border-color: rgba(59, 130, 246, 0.2); }
.badge-safety { background: rgba(16, 185, 129, 0.1); color: #34D399; border-color: rgba(16, 185, 129, 0.2); }
.badge-warn { background: rgba(245, 158, 11, 0.1); color: #FBBF24; border-color: rgba(245, 158, 11, 0.2); }

.apply-button {
    background: #3B82F6;
    color: white !important;
    font-weight: 600;
    font-size: 0.875rem;
    padding: 8px 16px;
    border-radius: 8px;
    text-decoration: none !important;
    transition: background 0.2s;
}

.apply-button:hover {
    background: #2563EB;
}

/* Dashboard Metrics */
[data-testid="stMetricValue"] {
    color: var(--primary) !important;
    font-family: 'Inter', sans-serif !important;
}

/* Hide Streamlit components */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

</style>
"""

def job_card_html(job, score, safety_report):
    """Generates a professional, realistic job card HTML."""
    title    = job.get("title", "Untitled Role")
    company  = job.get("company", "Unknown Company")
    location = job.get("location", "Remote / Hybrid")
    source   = job.get("source", "Portal")
    link     = job.get("apply_link", "#")
    
    # Safety Logic
    trust_score = safety_report.get("trust_score", 50) if safety_report else 50
    verdict     = safety_report.get("verdict", "Medium") if safety_report else "Untested"
    safety_class = "badge-safety" if trust_score >= 70 else ("badge-warn" if trust_score >= 45 else "badge-warn") # Simplification for clean UI
    
    return f"""
    <div class="job-card">
        <div class="job-header">
            <div>
                <span class="company-name">{company}</span>
                <h3 class="job-title">{title}</h3>
                <span class="job-location">📍 {location}</span>
            </div>
            <div style="text-align: right">
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 2px;">MATCH SCORE</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #3B82F6">{score}%</div>
            </div>
        </div>
        
        <div class="badge-group">
            <span class="badge" style="background: #2D3748; color: #A0AEC0;">{source}</span>
            <span class="badge badge-ai">🤖 AI Verified</span>
            <span class="badge {safety_class}">🛡️ {verdict}</span>
        </div>

        <div class="job-footer">
            <span style="font-size: 0.8rem; color: var(--text-muted);">Posted {job.get('date_posted', 'Just now')}</span>
            <a href="{link}" target="_blank" class="apply-button">Apply Now</a>
        </div>
    </div>
    """

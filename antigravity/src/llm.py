import re
import requests


class LLMManager:
    def __init__(self, model="llama3"):
        self.model = model
        self.base_url = "http://localhost:11434/api"

    def get_completion(self, prompt):
        try:
            url = f"{self.base_url}/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0,
                    "seed": 42,
                    "num_ctx": 2048,    # cap context window for speed
                    "num_predict": 512  # cap max output tokens
                }
            }
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                return response.json().get('response', '')
            return f"Error: Ollama returned status {response.status_code}"
        except Exception as e:
            return f"Error connecting to Ollama API: {str(e)}"

    # ----------------------------
    # ROLE DETECTION ONLY (with normalisation)
    # ----------------------------
    def detect_role_only(self, resume_text):
        # Normalise text: collapse multiple newlines, strip leading/trailing spaces
        text = re.sub(r'\n\s*\n', '\n\n', resume_text.strip())
        text = text[:2000]   # keep within token limit

        prompt = f"""
You are an expert resume analyst. Based on the entire resume below, identify the single most appropriate job title that the candidate is targeting. Consider their skills, work experience, projects, education, professional summary, and any certifications. Return ONLY the job title . – no explanations, no extra words.
Give only one job title.
Resume:
{text}
"""
        response = self.get_completion(prompt).strip()
        # Clean up quotes and stray punctuation
        response = re.sub(r'^["\']+|["\']+$', '', response)  # remove quotes
        response = response.strip('.').strip()
        return response

    # ----------------------------
    # ATS SCORE
    # ----------------------------
    def analyze_resume(self, resume_text):
        prompt = f"""Analyze the resume and provide:
1. ATS Score (0-100)
2. Up to 3 improvement suggestions.

Format:
Score: [score]
Suggestions:
- [suggestion 1]
- [suggestion 2]

Resume (first 1500 chars):
{resume_text[:1500]}
"""
        return self.get_completion(prompt)

    # ----------------------------
    # SKILL EXTRACTION
    # ----------------------------
    def extract_skills(self, resume_text):
        prompt = f"""Extract all technical and professional skills from the resume.
Return ONLY comma-separated skill names.

Resume (first 1500 chars):
{resume_text[:1500]}
"""
        return self.get_completion(prompt)

    # ----------------------------
    # CANDIDATE PROFILE ANALYSIS
    # ----------------------------
    def analyze_candidate_profile(
        self,
        resume_text,
        detected_experience_level,
        detected_years
    ):
        prompt = f"""
You are analyzing a candidate profile.

IMPORTANT:
Experience has already been calculated using rule-based logic.
You MUST NOT change it.

Detected Experience:
- Years: {detected_years}
- Level: {detected_experience_level}

Your task:
1. Identify the MOST LIKELY Target Role.
2. Identify the Role Family (IT, AI/ML, Finance, etc.)
3. Provide concise reasoning.

Return EXACT format:

### 🎯 Candidate Profile Analysis
- **Target Role:** [Title]
- **Experience Level:** {detected_experience_level}
- **Role Family:** [Family]

**Detailed Reasoning:**
[Short reasoning]

Resume:
{resume_text[:2000]}
"""
        return self.get_completion(prompt)

    # ----------------------------
    # SEMANTIC JOB SCORING
    # ----------------------------
    def semantic_job_score(self, resume_text, job_description, detected_role):
        # Focus on the most relevant parts of the resume and job
        res = str(resume_text)[:2000]
        desc = str(job_description)[:2000]
        
        prompt = f"""
You are a high-precision ATS (Applicant Tracking System) Matching Engine. 
Your goal is to provide a RIGOROUS and UNBIASED match between a resume and a job description.

Candidate Target Role: {detected_role}
Resume Snippet:
{res}

Job Description Snippet:
{desc}

INSTRUCTIONS:
1. MATCH SCORE (0-100): Be extremely critical. 
   - 90+ means near-perfect skill match and seniority alignment.
   - 70-89 means strong match but with clear gaps in high-priority skills.
   - 40-69 means partial match only.
   - <40 means significant mismatch.
   - AVOID CLUMPING SCORES (e.g., don't give everyone 95%). Use the full range.

2. DETAILED ANALYSIS: Provide 3-5 sentences of deep reasoning. Justify the score using specific evidence from both the resume and the job text.

3. SKILL GAP ANALYSIS:
   - Identify 'key_matching_skills' (present in both).
   - Identify 'missing_skills' (required by job but missing from resume).

4. Return ONLY a valid JSON object.

RESPONSE FORMAT:
{{
    "match_score": integer,
    "detailed_explanation": "...",
    "key_matching_skills": ["skill1", "skill2"],
    "missing_skills": ["skillA", "skillB"],
    "seniority_alignment": "Aligned / Overqualified / Underqualified",
    "domain_alignment": "High / Medium / Low"
}}
"""
        return self.get_completion(prompt)


if __name__ == "__main__":
    llm = LLMManager()
    print("LLMManager initialized (deterministic mode).")
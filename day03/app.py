import json
import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional

load_dotenv()


# ---------------------------------------------------------------------------
# Pydantic model
# ---------------------------------------------------------------------------

class JobPosting(BaseModel):
    role: str
    company: Optional[str] = None
    location: Optional[str] = None
    remote_ok: Optional[bool] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    experience_years: Optional[str] = None
    employment_type: Optional[str] = None
    required_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    company_description: Optional[str] = None


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a job posting parser. Extract structured information from the job posting text provided by the user.
Return ONLY raw JSON — no markdown, no code fences, no explanation.
The JSON must match this schema exactly:
{
  "role": "string (required)",
  "company": "string or null",
  "location": "string or null",
  "remote_ok": "boolean or null",
  "salary_min": "integer or null",
  "salary_max": "integer or null",
  "salary_currency": "string or null (e.g. USD)",
  "experience_years": "string or null (e.g. '5+ years')",
  "employment_type": "string or null (e.g. Full-Time)",
  "required_skills": ["list of strings"],
  "nice_to_have_skills": ["list of strings"],
  "responsibilities": ["list of strings"],
  "benefits": ["list of strings"],
  "company_description": "string or null"
}"""


# ---------------------------------------------------------------------------
# Sample job posting
# ---------------------------------------------------------------------------

SAMPLE_JOB = """Senior Backend Engineer — Remote
Company: Acme Corp | Location: Remote (US) | Full-Time | $140k–$175k

About Acme Corp: Fast-growing SaaS building developer tools used by 50,000+ teams.

Responsibilities:
- Build scalable REST APIs with FastAPI
- Own microservice architecture
- Mentor junior engineers

Required Skills: Python, FastAPI, PostgreSQL, Docker
Nice-to-Have: Kafka, Kubernetes, Redis

Experience: 5+ years backend engineering
Benefits: Unlimited PTO, $2k learning budget, full health/dental/vision, equity"""


# ---------------------------------------------------------------------------
# Extraction function
# ---------------------------------------------------------------------------

def extract_job(api_key: str, job_text: str) -> tuple[Optional[JobPosting], str, str]:
    """Returns (job, error, raw_json)."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT,
        )
        response = model.generate_content(job_text)
        raw_json = response.text.strip()

        # Strip accidental markdown code fences if the model adds them
        if raw_json.startswith("```"):
            raw_json = raw_json.split("```")[1]
            if raw_json.startswith("json"):
                raw_json = raw_json[4:]
            raw_json = raw_json.strip()

        data = json.loads(raw_json)
        job = JobPosting(**data)
        return job, "", raw_json
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}", ""
    except Exception as e:
        return None, f"Unexpected error: {e}", ""


# ---------------------------------------------------------------------------
# Streamlit app
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Job Posting Parser", page_icon="📋", layout="wide")
st.title("📋 Job Posting Parser")
st.caption("Paste a job posting and let Gemini extract structured data from it.")

# Session state
if "job_text" not in st.session_state:
    st.session_state.job_text = ""

left, right = st.columns([1, 1])

# ------------------------------------------------------------------
# Left column — inputs
# ------------------------------------------------------------------
with left:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        st.warning("GEMINI_API_KEY is not set. Add it to your .env file.")

    # Flush any pending value set by Load Sample / Clear
    if "pending_job_text" in st.session_state:
        st.session_state.job_text = st.session_state.pop("pending_job_text")

    job_text = st.text_area(
        "Job Posting Text",
        height=350,
        placeholder="Paste a job posting here…",
        key="job_text",
    )

    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("Load Sample", use_container_width=True):
            st.session_state.pending_job_text = SAMPLE_JOB
            st.rerun()
    with col_btn2:
        if st.button("Clear", use_container_width=True):
            st.session_state.pending_job_text = ""
            st.rerun()
    with col_btn3:
        extract_clicked = st.button(
            "Extract →",
            use_container_width=True,
            type="primary",
            disabled=not (api_key and job_text),
        )

# ------------------------------------------------------------------
# Right column — results
# ------------------------------------------------------------------
with right:
    if extract_clicked:
        with st.spinner("Calling Gemini…"):
            job, error, raw_json = extract_job(api_key, job_text)

        if error:
            st.error(error)
        else:
            # Headline metrics
            c1, c2, c3 = st.columns(3)
            c1.metric("Role", job.role)
            c2.metric("Company", job.company or "N/A")
            c3.metric("Location", job.location or "N/A")
            st.divider()

            # Tabs
            t1, t2, t3, t4 = st.tabs(["Overview", "Skills", "Details", "Raw JSON"])

            with t1:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Type:** {job.employment_type or 'N/A'}")
                    st.markdown(f"**Remote:** {'Yes' if job.remote_ok else 'No' if job.remote_ok is False else 'N/A'}")
                    st.markdown(f"**Experience:** {job.experience_years or 'N/A'}")
                with col_b:
                    salary = f"{job.salary_currency or ''} {job.salary_min or '?'} – {job.salary_max or '?'}".strip()
                    st.markdown(f"**Salary:** {salary if job.salary_min else 'N/A'}")
                if job.company_description:
                    st.info(job.company_description)

            with t2:
                if job.required_skills:
                    st.markdown("**Required:**")
                    st.markdown(" ".join(f"`{s}`" for s in job.required_skills))
                if job.nice_to_have_skills:
                    st.markdown("**Nice-to-Have:**")
                    st.markdown(" ".join(f"`{s}`" for s in job.nice_to_have_skills))

            with t3:
                if job.responsibilities:
                    with st.expander("Responsibilities", expanded=True):
                        for r in job.responsibilities:
                            st.markdown(f"- {r}")
                if job.benefits:
                    with st.expander("Benefits"):
                        for b in job.benefits:
                            st.markdown(f"- {b}")

            with t4:
                st.code(raw_json, language="json")
    else:
        st.info("Paste a job posting (or load the sample), then click **Extract →**.")

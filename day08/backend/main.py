import os
import json
import re
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="CodeShield API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

client = OpenAI(
    base_url=f"{OLLAMA_BASE_URL}/v1",
    api_key="ollama",
)


class AuditRequest(BaseModel):
    code: str
    language: str = "python"
    model: str = OLLAMA_MODEL
    checks: List[str] = [
        "injection",
        "auth",
        "crypto",
        "secrets",
        "xss",
        "insecure_deps",
    ]

    @field_validator('model')
    @classmethod
    def default_model(cls, v):
        return v.strip() or OLLAMA_MODEL


class Issue(BaseModel):
    severity: str  # critical, high, medium, low, info
    category: str
    title: str
    description: str
    line_number: Optional[int] = None
    recommendation: str
    cwe_id: Optional[str] = None


class AuditResponse(BaseModel):
    score: int  # 0-100
    summary: str
    issues: List[Issue]
    model_used: str
    language: str


CHECK_DESCRIPTIONS = {
    "injection": "SQL injection, command injection, LDAP injection, and other injection flaws",
    "auth": "Authentication and authorization weaknesses, broken access control",
    "crypto": "Cryptographic failures, weak algorithms, insecure random number generation",
    "secrets": "Hardcoded secrets, API keys, passwords, and sensitive credentials",
    "xss": "Cross-site scripting vulnerabilities, unsafe HTML rendering",
    "insecure_deps": "Use of known-vulnerable libraries or insecure imports",
}


def build_prompt(code: str, language: str, checks: List[str]) -> str:
    check_list = "\n".join(
        f"- {CHECK_DESCRIPTIONS.get(c, c)}" for c in checks
    )

    return f"""You are CodeShield, an expert security auditor. Analyze the following {language} code for security vulnerabilities.

Focus on these security checks:
{check_list}

Code to analyze:
```{language}
{code}
```

Respond ONLY with valid JSON (no markdown fences, no extra text) in this exact format:
{{
  "score": <integer 0-100, where 100 is perfectly secure>,
  "summary": "<brief 1-2 sentence summary of findings>",
  "issues": [
    {{
      "severity": "<critical|high|medium|low|info>",
      "category": "<category name>",
      "title": "<short issue title>",
      "description": "<detailed description of the vulnerability>",
      "line_number": <line number or null>,
      "recommendation": "<specific fix recommendation>",
      "cwe_id": "<CWE-XXX or null>"
    }}
  ]
}}

If no issues are found, return an empty issues array and a score of 100.
Severity guidelines:
- critical: Immediate exploitation possible, data breach risk
- high: Significant vulnerability, likely exploitable
- medium: Vulnerability exists but harder to exploit
- low: Minor issue, best practice violation
- info: Informational finding, no direct security impact"""


def extract_json(text: str) -> str:
    """Strip markdown fences and extract raw JSON from model output."""
    text = text.strip()

    # Remove ```json ... ``` or ``` ... ``` fences
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(fence_pattern, text)
    if match:
        return match.group(1).strip()

    # Try to find JSON object directly
    json_pattern = r"\{[\s\S]*\}"
    match = re.search(json_pattern, text)
    if match:
        return match.group(0)

    return text


@app.post("/audit", response_model=AuditResponse)
async def audit_code(request: AuditRequest):
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    prompt = build_prompt(request.code, request.language, request.checks)

    try:
        response = client.chat.completions.create(
            model=request.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a security auditor. Always respond with valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
        )

        raw_output = response.choices[0].message.content
        if not raw_output:
            raise HTTPException(
                status_code=500,
                detail="Model returned an empty response. Try again.",
            )
        clean_json = extract_json(raw_output)

        try:
            data = json.loads(clean_json)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Model returned invalid JSON: {str(e)}. Raw output: {raw_output[:500]}",
            )

        return AuditResponse(
            score=data.get("score", 50),
            summary=data.get("summary", "Analysis complete."),
            issues=[Issue(**issue) for issue in data.get("issues", [])],
            model_used=request.model,
            language=request.language,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to Ollama. Is it running? Error: {str(e)}",
        )


@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client_http:
            resp = await client_http.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                return {"status": "ok", "ollama": "connected"}
    except Exception:
        pass
    return {"status": "degraded", "ollama": "unreachable"}


@app.get("/models")
async def list_models():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client_http:
            resp = await client_http.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                return {"models": models}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot reach Ollama: {str(e)}",
        )

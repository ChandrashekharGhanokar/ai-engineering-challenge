# Day 08 — CodeShield: AI-Powered Code Security Auditor

## What it is

CodeShield is a local AI tool that analyzes code snippets for security vulnerabilities. Paste your code into the browser UI, and the FastAPI backend sends it to a locally-running Ollama LLM (qwen2.5:7b) which returns a structured security audit — no data leaves your machine.

## Tech Stack

- FastAPI (Python backend)
- Ollama (local LLM — qwen2.5:7b)
- openai Python SDK v1.x (OpenAI-compatible client for Ollama)
- Vanilla HTML/CSS/JS (frontend, single file)

## Project Structure

```
day08/
  backend/   → FastAPI server (main.py, requirements.txt, .env.example)
  frontend/  → index.html (self-contained UI, no build step)
```

## Prerequisites

- Python 3.10+
- Ollama installed and running (https://ollama.com)
- qwen2.5:7b model pulled: `ollama pull qwen2.5:7b`

## Setup & Run

### Backend

```bash
cd day08/backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env            # edit if needed
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

Open `frontend/index.html` in any browser (no server needed).
Or serve with: `python -m http.server 3000` (from `day08/frontend/`)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/audit` | Analyze code for security issues |
| GET | `/health` | Check Ollama connection |
| GET | `/models` | List available Ollama models |

## Security Checks

- Injection (SQL, command, LDAP, etc.)
- Authentication & Authorization flaws
- Cryptography issues (weak algorithms, improper use)
- Hardcoded Secrets (API keys, passwords, tokens)
- Cross-Site Scripting (XSS)
- Insecure Dependencies

## Notes / Fixes Applied

- Pinned `openai<2.0.0` to avoid breaking changes in v2 SDK
- Added None-guard on model response to return a clean 500 instead of crashing

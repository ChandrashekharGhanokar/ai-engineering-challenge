# AI Engineering Challenge

Daily hands-on projects building AI Engineering fundamentals from scratch.

## Structure

| Day | Topic | Description |
|-----|-------|-------------|
| [day01](./day01/) | LLM Basics | Multi-turn CLI chatbot with GPT-4o-mini |
| [day02](./day02/) | LLM Judge | Prompt comparison with an LLM-as-judge evaluator |
| [day03](./day03/) | Structured Output | Streamlit job posting parser with Gemini 2.5 Flash + Pydantic |
| [day04](./day04/) | Local RAG | PDF Q&A bot with Ollama + FAISS (fully local) |
| [day05](./day05/) | Finance Assistant | Tool-calling agent with Streamlit UI — stocks, exchange rates, compound interest |
| [day06](./day06/) | Embeddings | Semantic similarity search with nomic-embed-text + Ollama  |
| [day07](./day07/) | Research Agent | Autonomous deep research agent with Ollama tool-calling, Tavily search, and Jina Reader |
| [day08](./day08/) | CodeShield | AI-powered code security auditor — FastAPI + Ollama (local LLM), detects injection, XSS, secrets, and more |
| [day09](./day09/) | Prompt Injection Defender | CLI tool that classifies prompt injection risk with a guard LLM, then shows side-by-side protected vs unprotected responses — fully local via Ollama |
| [day10](./day10/clarity/) | XAI Classifier | Explainable AI text classifier — LLM assigns scores and signals, Python computes Shannon entropy, margin, and calibration — fully local via Ollama |
| [day11](./day11/) | AI Tutor | Interactive AI tutor chatbot — teaches AI concepts from beginner to advanced via Llama 3.3 70B (HF Inference API) + Streamlit |
| [day12](./day12/) | PR Reviewer Agent | AI-powered GitHub PR reviewer — analyzes code diffs, detects bugs/security/performance issues, and generates structured review feedback using local LLM (Qwen2.5 7B via Ollama) |
## Getting started

Each day is a self-contained project with its own `README.md`, `requirements.txt`, and source code. Navigate into a day's folder and follow its setup instructions.

```bash
cd day01
python -m venv venv && source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env  # then add your OPENAI_API_KEY
python chat.py

# day03 and day05 use Streamlit:
# streamlit run day03/app.py
# streamlit run day05/app.py
```

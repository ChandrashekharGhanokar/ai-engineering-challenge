---
title: AI Tutor — Learn Artificial Intelligence
emoji: 🎓
colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: 1.35.0
app_file: app.py
pinned: true
license: mit
short_description: Your personal AI tutor — learn AI from basics to advanced
---

# 🎓 AI Tutor — Learn Artificial Intelligence

Your personal AI learning companion. Ask anything about Artificial Intelligence — from the very basics to advanced topics. I'll teach you step by step, at your own pace.

## What I can teach
- 🌱 Beginner: What is AI/ML/DL, how chatbots work, neural networks, AI ethics
- ⚡ Intermediate: LLMs, Transformers, Prompt Engineering, RAG, Embeddings
- 🔥 Advanced: AI Agents, Model Architectures, Building AI Products, AI Safety

## Special Commands
- `quiz me` — test yourself on any topic
- `roadmap` — get a personalized learning path
- `ELI5` — re-explain anything in simple terms
- `give me a project` — hands-on project ideas
- `resources` — free courses, papers, and tools

## Tech Stack
- Frontend: Streamlit
- Model: meta-llama/Llama-3.3-70B-Instruct (free via HF Inference API)
- Hosting: Hugging Face Spaces (free)

## Setup

```bash
pip install -r requirements.txt
```

Set your Hugging Face token in `.env`:
```
HF_TOKEN=your_token_here
```

## Run

```bash
python -m streamlit run app.py
```

---
Part of the 30-Day AI Engineering Challenge

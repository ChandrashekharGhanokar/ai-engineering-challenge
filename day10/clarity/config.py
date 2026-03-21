# config.py — clarity configuration

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_API_URL  = f"{OLLAMA_BASE_URL}/api/chat"

AVAILABLE_MODELS = [
    "llama3.2",
    "llama3.2:1b",
    "qwen2.5:7b",
    "qwen2.5:3b",
    "qwen2.5",
]

DEFAULT_MODEL = "llama3.2"

CLASSIFIER_SYSTEM_PROMPT = """You are an explainable AI text classifier.

Given a text and a list of classification labels, you must:
1. Assign a confidence score (0-100) to EVERY label. Scores must sum to exactly 100.
2. Write a short 1-sentence reasoning for each label's score.
3. Identify 3-5 key signals (words, phrases, or linguistic features) from the text that drove your decision.

Respond ONLY with valid raw JSON — no markdown, no code fences, no explanation outside JSON.

Use this exact structure:
{
  "winner": "<label>",
  "scores": [
    {"label": "<label>", "score": <0-100>, "reasoning": "<one sentence>"},
    ...
  ],
  "signals": [
    {"icon": "<one emoji>", "text": "<signal description>"},
    ...
  ]
}"""

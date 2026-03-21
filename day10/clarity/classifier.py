# classifier.py — calls Ollama and parses XAI response

import json
import math
import sys
import urllib.request
import urllib.error
from typing import List, Dict, Any

from config import OLLAMA_API_URL, CLASSIFIER_SYSTEM_PROMPT


def call_ollama(model: str, system: str, user: str) -> str:
    """Send a request to the local Ollama API and return the response text."""
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user}
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["message"]["content"].strip()
    except urllib.error.URLError as e:
        print(f"\n  ✗ Cannot reach Ollama at {OLLAMA_API_URL}")
        print(f"    Make sure Ollama is running: ollama serve")
        print(f"    And the model is pulled:     ollama pull {model}\n")
        sys.exit(1)


def compute_uncertainty(scores: List[Dict]) -> Dict:
    """Compute entropy, margin, calibration from scores using real math."""
    n = len(scores)
    probs = [s["score"] / 100.0 for s in scores]

    # Shannon entropy normalized to 0-100
    h = -sum(p * math.log2(p) for p in probs if p > 0)
    h_max = math.log2(n) if n > 1 else 1
    entropy = round((h / h_max) * 100)

    # Margin = gap between top two scores
    sorted_scores = sorted([s["score"] for s in scores], reverse=True)
    margin = sorted_scores[0] - sorted_scores[1] if n > 1 else sorted_scores[0]

    # Calibration derived from entropy + margin thresholds
    if entropy < 25 and margin > 40:
        calibration = "very confident"
        summary = f"Model is very confident — entropy {entropy}/100 is low and the margin of {margin} pts is large."
    elif entropy < 50 and margin > 20:
        calibration = "confident"
        summary = f"Model is confident — entropy {entropy}/100 is moderate and the {margin}-pt margin shows a clear winner."
    elif entropy < 70:
        calibration = "uncertain"
        summary = f"Model is uncertain — entropy {entropy}/100 shows spread across labels; margin of {margin} pts is narrow."
    else:
        calibration = "very uncertain"
        summary = f"Model is very uncertain — entropy {entropy}/100 is high and the {margin}-pt margin is too small to be confident."

    return {
        "entropy":     entropy,
        "margin":      margin,
        "calibration": calibration,
        "summary":     summary,
    }


def parse_response(raw: str) -> Dict[str, Any]:
    """Extract and validate JSON from model response."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end   = cleaned.rfind("}") + 1
        if start != -1 and end > start:
            data = json.loads(cleaned[start:end])
        else:
            raise ValueError(f"Could not parse JSON from model response:\n{raw[:300]}")

    required = ["winner", "scores", "signals"]
    for key in required:
        if key not in data:
            raise ValueError(f"Missing key '{key}' in model response")

    # Normalize scores to sum to 100 (model sometimes drifts)
    total = sum(s["score"] for s in data["scores"])
    if total != 100 and total > 0:
        for s in data["scores"]:
            s["score"] = round(s["score"] * 100 / total)

    data["scores"].sort(key=lambda x: x["score"], reverse=True)
    data["uncertainty"] = compute_uncertainty(data["scores"])

    return data


def classify(text: str, labels: List[str], model: str, no_color: bool = False) -> Dict[str, Any]:
    """Run the full XAI classification pipeline."""
    from display import color, spinner_start, spinner_stop

    labels_str = ", ".join(f'"{l}"' for l in labels)
    user_prompt = f'Text: "{text}"\nLabels: [{labels_str}]\n\nClassify and explain.'

    sp = spinner_start(f"  Classifying with {model}...", no_color)
    try:
        raw = call_ollama(model, CLASSIFIER_SYSTEM_PROMPT, user_prompt)
        result = parse_response(raw)
    except (ValueError, KeyError) as e:
        spinner_stop(sp)
        print(f"\n  ✗ Parse error: {e}\n")
        sys.exit(1)
    finally:
        spinner_stop(sp)

    result["input_text"] = text
    result["labels"]     = labels
    result["model"]      = model

    return result

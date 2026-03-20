import json
import re
import ollama
from prompts import GUARD_SYSTEM_PROMPT

_GUARD_SCHEMA = {
    "type": "object",
    "properties": {
        "risk":       {"type": "string", "enum": ["low", "medium", "high"]},
        "type":       {"type": "string", "enum": ["none", "instruction_override",
                        "persona_switch", "prompt_extraction",
                        "jailbreak", "social_engineering"]},
        "confidence": {"type": "number"},
        "reason":     {"type": "string"},
    },
    "required": ["risk", "type", "confidence", "reason"],
}


def analyze_input_with_system(user_message: str, model: str) -> dict:
    """
    Calls Ollama with the guard system prompt to classify the user message.
    Returns a dict with keys: risk, type, confidence, reason.
    Falls back to regex extraction if JSON parsing fails.
    """
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": GUARD_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            format=_GUARD_SCHEMA,
        )
        msg = response.message if hasattr(response, "message") else response["message"]
        content = (msg.content if hasattr(msg, "content") else msg["content"]).strip()

        # Try direct JSON parse
        try:
            result = json.loads(content)
            return _normalize(result)
        except json.JSONDecodeError:
            pass

        # Regex fallback: extract first {...} block
        match = re.search(r"\{.*?\}", content, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
                return _normalize(result)
            except json.JSONDecodeError:
                pass

        # Last resort: parse individual fields with regex
        return _regex_extract(content)

    except Exception as e:
        return {
            "risk": "unknown",
            "type": "none",
            "confidence": 0.0,
            "reason": f"Guard error: {e}",
        }


def _normalize(data: dict) -> dict:
    """Ensure all expected keys exist with sane defaults."""
    return {
        "risk": str(data.get("risk", "unknown")).lower(),
        "type": str(data.get("type", "none")).lower(),
        "confidence": float(data.get("confidence", 0.0)),
        "reason": str(data.get("reason", "No reason provided.")),
    }


def _regex_extract(text: str) -> dict:
    """Best-effort field extraction when JSON is malformed."""
    risk_match = re.search(r'"risk"\s*:\s*"(\w+)"', text)
    type_match = re.search(r'"type"\s*:\s*"([\w_]+)"', text)
    conf_match = re.search(r'"confidence"\s*:\s*([0-9.]+)', text)
    reason_match = re.search(r'"reason"\s*:\s*"([^"]+)"', text)

    return {
        "risk": risk_match.group(1).lower() if risk_match else "unknown",
        "type": type_match.group(1).lower() if type_match else "none",
        "confidence": float(conf_match.group(1)) if conf_match else 0.0,
        "reason": reason_match.group(1) if reason_match else "Could not parse guard response.",
    }

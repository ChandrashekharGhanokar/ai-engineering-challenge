import ollama
from prompts import UNPROTECTED_SYSTEM_PROMPT, PROTECTED_SYSTEM_PROMPT


def get_unprotected_response(user_message: str, model: str) -> str:
    """
    Calls Ollama with the naive (unprotected) system prompt.
    """
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": UNPROTECTED_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
        msg = response.message if hasattr(response, "message") else response["message"]
        return (msg.content if hasattr(msg, "content") else msg["content"]).strip()
    except Exception as e:
        return f"[Error getting unprotected response: {e}]"


def get_protected_response(user_message: str, model: str, guard_result: dict) -> str:
    """
    Calls Ollama with the hardened system prompt.
    If the guard flagged a medium/high risk, prepends a security alert to the user message
    so the protected assistant is aware of the classification.
    """
    risk = guard_result.get("risk", "low")
    inject_alert = risk in ("medium", "high")

    if inject_alert:
        alert = (
            f"[SECURITY ALERT — Guard classified this input as '{risk}' risk "
            f"({guard_result.get('type', 'unknown')} | "
            f"confidence {guard_result.get('confidence', 0.0):.0%}): "
            f"{guard_result.get('reason', '')}]\n\n"
        )
        augmented_message = alert + user_message
    else:
        augmented_message = user_message

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": PROTECTED_SYSTEM_PROMPT},
                {"role": "user", "content": augmented_message},
            ],
        )
        msg = response.message if hasattr(response, "message") else response["message"]
        return (msg.content if hasattr(msg, "content") else msg["content"]).strip()
    except Exception as e:
        return f"[Error getting protected response: {e}]"

import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import ollama

from guard import analyze_input_with_system
from responder import get_protected_response, get_unprotected_response
from utils import (
    console,
    print_banner,
    print_error,
    print_examples,
    print_guard_result,
    print_loading,
    print_model_info,
    print_responses,
    print_separator,
)


# ---------------------------------------------------------------------------
# Startup checks
# ---------------------------------------------------------------------------

def check_ollama_running() -> bool:
    """Return True if the Ollama server is reachable."""
    try:
        ollama.list()
        return True
    except Exception:
        return False


def check_model_available(model: str) -> bool:
    """Return True if *model* is already pulled locally."""
    try:
        response = ollama.list()
        # New SDK (≥0.2): ListResponse object with .models list of Model objects
        models_list = getattr(response, "models", None)
        if models_list is None:
            # Old SDK: plain dict
            models_list = response.get("models", [])
        names = []
        for m in models_list:
            name = (
                getattr(m, "model", None)       # new SDK: Model.model
                or getattr(m, "name", None)     # possible alias
                or (m.get("name") if isinstance(m, dict) else None)  # old SDK dict
                or ""
            )
            if name:
                names.append(name)
        # Allow partial match: "llama3.2" matches "llama3.2:latest"
        return any(model in name for name in names)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def analyze(user_message: str, model: str) -> None:
    print_separator()
    print_loading("Running guard classifier…")

    guard_result = analyze_input_with_system(user_message, model)
    print_guard_result(guard_result)

    print_loading("Fetching responses (parallel)…")

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(get_unprotected_response, user_message, model): "unprotected",
            executor.submit(get_protected_response, user_message, model, guard_result): "protected",
        }
        results = {}
        for future in as_completed(futures):
            key = futures[future]
            results[key] = future.result()

    print_responses(results["unprotected"], results["protected"])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Day 09 — Prompt Injection Defender (local Ollama)"
    )
    parser.add_argument(
        "--model",
        default="llama3.2",
        help="Ollama model to use (default: llama3.2)",
    )
    args = parser.parse_args()
    model: str = args.model

    print_banner()

    # Check Ollama
    if not check_ollama_running():
        print_error(
            "Ollama is not running. Start it with: [bold]ollama serve[/bold]"
        )
        sys.exit(1)

    # Check model
    if not check_model_available(model):
        print_error(
            f"Model '[bold]{model}[/bold]' is not available locally.\n"
            f"Pull it with: [bold]ollama pull {model}[/bold]"
        )
        sys.exit(1)

    print_model_info(model)
    console.print(
        "Type your message to test prompt injection detection.\n"
        "Commands: [bold]examples[/bold] · [bold]clear[/bold] · [bold]exit[/bold]\n"
    )

    while True:
        try:
            user_input = console.input("[bold cyan]>[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not user_input:
            continue

        lower = user_input.lower()

        if lower in ("exit", "quit"):
            console.print("[dim]Goodbye.[/dim]")
            break

        if lower == "examples":
            print_examples()
            continue

        if lower == "clear":
            os.system("cls" if sys.platform == "win32" else "clear")
            print_banner()
            print_model_info(model)
            continue

        analyze(user_input, model)


if __name__ == "__main__":
    main()

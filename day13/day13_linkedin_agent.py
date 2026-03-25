"""
Day 13 — LinkedIn Post Writer Agent
Challenge: AI Engineering fundamentals, one build at a time.

What this teaches:
- Conversational agent pattern (multi-turn, stateful)
- Structured information gathering via agent questions
- Prompt chaining: gather → structure → generate
- Running LLMs locally with Ollama (no API key needed)

Models supported:
- llama3.2      (fast, good quality)
- qwen2.5:7b    (stronger reasoning, better JSON)

Run:
    pip install ollama rich
    ollama pull llama3.2        # or: ollama pull qwen2.5:7b
    python day13_linkedin_agent.py
"""

import ollama
import json
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich import box
from rich.table import Table

console = Console()

# ── Model config ───────────────────────────────────────────────────────────────
# Switch between models here. qwen2.5:7b is better at structured JSON output.
# llama3.2 is faster for the cleanup step.

FAST_MODEL  = "llama3.2"      # used for answer cleanup (light task)
SMART_MODEL = "qwen2.5:7b"   # used for post generation (heavy task)

# ── Questions the agent will ask (in order) ───────────────────────────────────

QUESTIONS = [
    {
        "key": "topic",
        "question": "What did you build or learn today?",
        "hint": "Be specific — a tool, concept, technique, or insight."
    },
    {
        "key": "audience",
        "question": "Who is your target audience?",
        "hint": "e.g. developers, founders, AI engineers, students, product managers"
    },
    {
        "key": "takeaway",
        "question": "What's the one key takeaway you want readers to leave with?",
        "hint": "The single most important thing they should understand."
    },
    {
        "key": "story",
        "question": "Any personal story, struggle, or 'aha moment' from this?",
        "hint": "Even a small one. This makes posts human. Type 'skip' if none."
    },
    {
        "key": "cta",
        "question": "What's your call to action?",
        "hint": "e.g. follow for daily builds, share if useful, drop a comment, try it yourself"
    },
]

HOOK_STYLES = {
    "bold_claim": {
        "label": "Bold Claim",
        "description": "Starts with a strong, slightly controversial statement",
    },
    "story": {
        "label": "Story Hook",
        "description": "Opens with a personal moment or struggle",
    },
    "curiosity": {
        "label": "Curiosity Gap",
        "description": "Teases the insight without giving it away",
    }
}

# ── Rich display helpers ───────────────────────────────────────────────────────

def print_banner():
    console.print()
    console.print(Panel.fit(
        "[bold cyan]LinkedIn Post Writer Agent[/bold cyan]\n"
        f"[dim]Conversational · 3 Hook Variations · Ollama ({SMART_MODEL})[/dim]",
        border_style="cyan",
        padding=(0, 2),
    ))
    console.print("[dim]I'll ask you 5 quick questions, then write 3 LinkedIn post variations for you.[/dim]")
    console.print()

def print_question(number: int, total: int, question: str, hint: str):
    console.print(Rule(f"[dim]Question {number} of {total}[/dim]"))
    console.print(f"\n[bold white]{question}[/bold white]")
    console.print(f"[dim italic]{hint}[/dim italic]\n")

def print_thinking(model: str):
    console.print()
    console.print(f"[dim]✦ generating with {model}...[/dim]")
    console.print()

def print_post_variation(hook_key: str, content: str, index: int):
    style = HOOK_STYLES[hook_key]
    colors = ["cyan", "magenta", "yellow"]
    color = colors[index % len(colors)]
    console.print(Panel(
        content,
        title=f"[bold {color}]Variation {index + 1} — {style['label']}[/bold {color}]",
        subtitle=f"[dim]{style['description']}[/dim]",
        border_style=color,
        padding=(1, 2),
    ))
    console.print()

def print_summary_table(context: dict):
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column("key", style="dim", width=16)
    table.add_column("val", style="white")
    labels = {
        "topic":    "Built / Learned",
        "audience": "Audience",
        "takeaway": "Key Takeaway",
        "story":    "Story / Struggle",
        "cta":      "Call to Action",
    }
    for k, v in context.items():
        table.add_row(labels.get(k, k), v)
    console.print(Panel(table, title="[dim]your inputs[/dim]", border_style="dim", padding=(0, 1)))
    console.print()

def print_tips():
    console.print(Rule("[dim]posting tips[/dim]"))
    tips = [
        "Post between 8-10am on Tue/Wed/Thu for max reach",
        "The first 2 lines determine if anyone reads the rest — test hooks",
        "Reply to every comment in the first hour (algorithm boost)",
        "Tag people only if they're genuinely part of the story",
    ]
    for tip in tips:
        console.print(f"[dim]  · {tip}[/dim]")
    console.print()

# ── Ollama helpers ─────────────────────────────────────────────────────────────

def chat(model: str, system: str, user: str) -> str:
    """Simple wrapper around ollama.chat — returns the assistant text."""
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ]
    )
    return response["message"]["content"].strip()

def parse_json_response(raw: str) -> dict:
    """Strip markdown fences and parse JSON from model output."""
    if "```" in raw:
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

# ── Conversational gathering ───────────────────────────────────────────────────

def gather_context() -> dict:
    """Ask questions one at a time, use fast model to lightly clean answers."""
    context = {}

    for i, q in enumerate(QUESTIONS):
        print_question(i + 1, len(QUESTIONS), q["question"], q["hint"])

        raw = console.input("[bold cyan]you>[/bold cyan] ").strip()

        if not raw:
            raw = "Not specified"

        # Skip story if user opts out
        if q["key"] == "story" and raw.lower() in ("skip", "none", "no", "-"):
            context[q["key"]] = "No personal story"
            console.print("[dim]→ skipped[/dim]\n")
            continue

        # Light cleanup with fast model — preserves voice, removes typos
        cleaned = chat(
            model=FAST_MODEL,
            system=(
                "You clean up user answers for a LinkedIn post context form. "
                "Keep it concise (1-2 sentences). Preserve the user's voice exactly. "
                "No added fluff. Return only the cleaned answer, nothing else."
            ),
            user=f"Question: {q['question']}\nAnswer: {raw}"
        )
        context[q["key"]] = cleaned
        console.print("[dim]→ got it[/dim]\n")

    return context

# ── Post generation ────────────────────────────────────────────────────────────

def generate_posts(context: dict) -> dict:
    """Generate 3 LinkedIn post variations using the smart model."""

    system_prompt = """You are an expert LinkedIn ghostwriter for the AI/tech space.

Your posts are:
- Authentic and conversational, not corporate
- Heavy on white space (short paragraphs, frequent line breaks)
- Specific and concrete, never generic
- Emotionally resonant but credible

Format rules:
- Hook (first line) must stop the scroll
- 150-300 words per post
- Line break between every 1-2 sentences
- End with the call to action
- Max 3 hashtags, only if truly relevant
- No em-dashes, no buzzwords like "game-changer" or "leverage"

IMPORTANT: Return ONLY valid JSON. No explanation, no markdown fences."""

    user_prompt = f"""Write 3 LinkedIn post variations using this context:

Topic: {context['topic']}
Audience: {context['audience']}
Key takeaway: {context['takeaway']}
Personal story: {context['story']}
Call to action: {context['cta']}

Hook styles:
1. bold_claim — open with a strong, slightly provocative statement that challenges a belief
2. story — open with a personal moment or real struggle from today
3. curiosity — tease the insight without revealing it in the first line

Return exactly this JSON (no extra text, no markdown):
{{
  "bold_claim": "<full post>",
  "story": "<full post>",
  "curiosity": "<full post>"
}}"""

    print_thinking(SMART_MODEL)
    raw = chat(model=SMART_MODEL, system=system_prompt, user=user_prompt)

    try:
        return parse_json_response(raw)
    except json.JSONDecodeError:
        # Fallback: extract JSON object from anywhere in the response
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(raw[start:end])
        raise

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print_banner()

    # Quick Ollama availability check
    try:
        ollama.list()
    except Exception:
        console.print("[red]✗ Ollama is not running. Start it with: ollama serve[/red]")
        return

    try:
        # Step 1: Gather context conversationally
        context = gather_context()

        # Step 2: Show summary of what we captured
        console.print()
        print_summary_table(context)

        # Step 3: Generate 3 post variations
        posts = generate_posts(context)

        # Step 4: Display each variation
        console.print(Rule("[bold white]Your LinkedIn Posts[/bold white]"))
        console.print()

        for i, (hook_key, content) in enumerate(posts.items()):
            print_post_variation(hook_key, content, i)

        # Step 5: Posting tips
        print_tips()

        console.print("[dim]Copy your favourite, tweak it, and post. Good luck![/dim]\n")

    except KeyboardInterrupt:
        console.print("\n[dim]cancelled.[/dim]")
    except json.JSONDecodeError:
        console.print("[red]✗ Model returned invalid JSON.[/red]")
        console.print(f"[dim]Tip: qwen2.5:7b handles JSON better. Switch SMART_MODEL at the top of the file.[/dim]")
    except ollama.ResponseError as e:
        console.print(f"[red]✗ Ollama error: {e}[/red]")
        console.print(f"[dim]Make sure the model is pulled: ollama pull {SMART_MODEL}[/dim]")

if __name__ == "__main__":
    main()

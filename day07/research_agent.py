"""
Day 7 — Deep Research Agent
Autonomous research agent using Ollama tool-calling (qwen2.5:7b).
No API key required. Optional: set TAVILY_API_KEY for real web search.
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

import httpx
import ollama
from dotenv import load_dotenv

# Load .env from the repo root (one level up from this file's directory)
load_dotenv(Path(__file__).parent.parent / ".env")

# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": (
                "Search the web for information on a query. "
                "Returns a list of results with titles, URLs, and snippets."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_page_content",
            "description": (
                "Fetch and read the full text content of a web page. "
                "Use this to read articles, reports, or pages in detail."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL of the page to read",
                    }
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish_research",
            "description": (
                "Call this when research is complete. "
                "Provide a comprehensive markdown report as the final answer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "report": {
                        "type": "string",
                        "description": "The final markdown research report",
                    }
                },
                "required": ["report"],
            },
        },
    },
]

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def search_web(query: str) -> list[dict]:
    """Search the web using Tavily API."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return [{"error": "TAVILY_API_KEY is not set. Add it to your .env file."}]
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        response = client.search(query, max_results=5)
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
            }
            for r in response.get("results", [])
        ]
    except Exception as e:
        return [{"error": f"Tavily search failed: {e}"}]


def get_page_content(url: str) -> str:
    """Fetch page content via Jina Reader (no API key needed)."""
    jina_url = f"https://r.jina.ai/{url}"
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            response = client.get(jina_url, headers={"Accept": "text/plain"})
            response.raise_for_status()
            content = response.text
            # Truncate to avoid flooding the context window
            if len(content) > 4000:
                content = content[:4000] + "\n\n[... content truncated ...]"
            return content
    except Exception as e:
        return f"Error fetching page: {e}"


def run_tool(name: str, args: dict) -> str:
    """Dispatch tool call and return JSON string result."""
    if name == "search_web":
        result = search_web(**args)
    elif name == "get_page_content":
        result = get_page_content(**args)
    elif name == "finish_research":
        # The report itself is the result — caller handles it specially
        return args.get("report", "")
    else:
        result = {"error": f"Unknown tool: {name}"}
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Agent logic
# ---------------------------------------------------------------------------

def build_system_prompt(topic: str) -> str:
    today = date.today().isoformat()
    return f"""You are an expert research assistant. Today's date is {today}.

Your task is to thoroughly research the following topic and produce a comprehensive markdown report:

**Topic:** {topic}

## Research process
1. Start with 1–2 broad searches to understand the landscape.
2. Use `get_page_content` on 1–2 promising URLs to gather detailed evidence.
3. Call `finish_research` once you have gathered useful information — typically after 3–5 tool calls total.

If a page fetch returns an error or 404, use the search snippets you already have and proceed to write the report. Prioritize writing a good report over exhaustive searching.

## Report format
The final report must include:
- An executive summary
- Key findings with evidence and citations (URL links)
- Current trends and developments
- Challenges and limitations
- Future outlook
- References section with URLs

Be thorough, factual, and cite your sources."""


def run_research_agent(topic: str, model: str = "qwen2.5:7b") -> str:
    """Run the agentic research loop. Returns the final report."""
    print(f"\n{'='*60}")
    print(f"  Research Agent starting")
    print(f"  Topic : {topic}")
    print(f"  Model : {model}")
    print(f"{'='*60}\n")

    messages = [
        {"role": "system", "content": build_system_prompt(topic)},
        {"role": "user", "content": f"Please research this topic thoroughly: {topic}"},
    ]

    iteration = 0
    max_iterations = 20  # safety limit

    while iteration < max_iterations:
        iteration += 1
        print(f"[Iteration {iteration}] Calling {model}...")

        if iteration == 3:
            print("  [nudge] Injecting wrap-up message at iteration 3")
            messages.append({
                "role": "user",
                "content": "You have done enough research. Please call finish_research now with your report.",
            })

        response = ollama.chat(
            model=model,
            messages=messages,
            tools=TOOLS,
        )

        assistant_message = response["message"]
        messages.append(assistant_message)

        tool_calls = assistant_message.get("tool_calls") or []

        if not tool_calls:
            # No tool calls — check if there's a plain text response
            content = assistant_message.get("content", "")
            if content:
                print("\n[Agent finished without calling finish_research]")
                return content
            # Empty response — nudge the model to write the report now
            print("  [nudge] Empty response — asking model to write report")
            messages.append({
                "role": "user",
                "content": (
                    "You have not called any tool. Based on all the research you have gathered so far, "
                    "please call finish_research now with a comprehensive markdown report."
                ),
            })
            continue

        for tool_call in tool_calls:
            fn = tool_call["function"]
            name = fn["name"]
            args = fn.get("arguments", {})
            if isinstance(args, str):
                args = json.loads(args)

            print(f"  -> Tool: {name}({list(args.keys())})")

            if name == "finish_research":
                report = args.get("report", "")
                print("\n[Agent called finish_research — research complete]\n")
                return report

            # Execute tool and feed result back
            result = run_tool(name, args)
            print(f"     Result: {result[:120].replace(chr(10), ' ')}{'...' if len(result) > 120 else ''}")

            messages.append({
                "role": "tool",
                "content": result,
            })

    print("[Max iterations reached]")
    return "Research incomplete — max iterations reached."


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_and_save(report: str, topic: str) -> str:
    """Print the report and save it to a markdown file."""
    print("\n" + "="*60)
    print("FINAL RESEARCH REPORT")
    print("="*60)
    print(report)

    # Build a safe filename
    safe_topic = topic.replace(" ", "_")[:40]
    filename = f"research_{safe_topic}.md"
    filepath = os.path.join(os.path.dirname(__file__), filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Research Report: {topic}\n\n")
        f.write(report)

    print(f"\n[Report saved to {filepath}]")
    return filepath


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

DEFAULT_TOPIC = "impact of AI agents on software engineering"

if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_TOPIC

    # Verify Ollama is reachable
    try:
        ollama.list()
    except Exception:
        print("ERROR: Cannot reach Ollama. Make sure it is running:")
        print("  ollama serve")
        sys.exit(1)

    report = run_research_agent(topic)
    print_and_save(report, topic)

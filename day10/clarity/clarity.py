#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════╗
║           clarity — XAI Classifier        ║
║   Explainable text classification with    ║
║   local Ollama models (llama3.2 / qwen)   ║
╚═══════════════════════════════════════════╝
"""

import argparse
import sys
from classifier import classify
from display import print_results, print_banner
from config import AVAILABLE_MODELS, DEFAULT_MODEL


def parse_args():
    parser = argparse.ArgumentParser(
        prog="clarity",
        description="Explainable AI text classifier using local Ollama models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python clarity.py -t "I love this product!" -l positive negative neutral
  python clarity.py -t "The stock market crashed." -l business sports politics tech -m qwen2.5:7b
  python clarity.py --interactive
  python clarity.py --demo
        """
    )
    parser.add_argument("-t", "--text", type=str, help="Text to classify")
    parser.add_argument("-l", "--labels", nargs="+", help="Classification labels")
    parser.add_argument(
        "-m", "--model",
        default=DEFAULT_MODEL,
        choices=AVAILABLE_MODELS,
        help=f"Ollama model to use (default: {DEFAULT_MODEL})"
    )
    parser.add_argument("-i", "--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--demo", action="store_true", help="Run with demo examples")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    return parser.parse_args()


def run_interactive(model: str, no_color: bool):
    from display import clear, color
    clear()
    print_banner()
    print(color("\n  Interactive Mode — type 'quit' to exit\n", "cyan", no_color))

    while True:
        try:
            text = input(color("  ✏  Text: ", "yellow", no_color)).strip()
            if text.lower() in ("quit", "exit", "q"):
                print(color("\n  Goodbye!\n", "cyan", no_color))
                break
            if not text:
                continue

            raw_labels = input(color("  🏷  Labels (comma or space separated): ", "yellow", no_color)).strip()
            labels = [l.strip() for l in raw_labels.replace(",", " ").split() if l.strip()]

            if len(labels) < 2:
                print(color("  ⚠  Need at least 2 labels.\n", "red", no_color))
                continue

            print()
            result = classify(text, labels, model, no_color)
            print_results(result, no_color)

        except KeyboardInterrupt:
            print(color("\n\n  Interrupted. Goodbye!\n", "cyan", no_color))
            break


def run_demo(model: str, no_color: bool):
    from display import color
    DEMOS = [
        {
            "text": "I waited 45 minutes and the food was cold when it arrived. Never ordering again.",
            "labels": ["positive", "negative", "neutral", "mixed"]
        },
        {
            "text": "The central bank raised interest rates by 25 basis points amid inflation concerns.",
            "labels": ["politics", "economics", "technology", "sports"]
        },
        {
            "text": "You people are absolutely clueless about how the real world works.",
            "labels": ["toxic", "offensive", "borderline", "neutral"]
        }
    ]

    print_banner()
    print(color("\n  Running demo examples...\n", "cyan", no_color))

    for i, demo in enumerate(DEMOS, 1):
        print(color(f"  ── Demo {i}/{len(DEMOS)} ─────────────────────────────", "cyan", no_color))
        result = classify(demo["text"], demo["labels"], model, no_color)
        print_results(result, no_color)
        if i < len(DEMOS):
            input(color("\n  Press Enter for next demo...\n", "yellow", no_color))


def main():
    args = parse_args()

    if args.interactive:
        run_interactive(args.model, args.no_color)
        return

    if args.demo:
        run_demo(args.model, args.no_color)
        return

    if not args.text or not args.labels:
        print("Error: --text and --labels are required (or use --interactive / --demo)")
        print("Run with --help for usage.")
        sys.exit(1)

    if len(args.labels) < 2:
        print("Error: Provide at least 2 labels.")
        sys.exit(1)

    print_banner()
    result = classify(args.text, args.labels, args.model, args.no_color)
    print_results(result, args.no_color)


if __name__ == "__main__":
    main()

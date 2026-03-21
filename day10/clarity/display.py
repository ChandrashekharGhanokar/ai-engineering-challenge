# display.py — rich terminal rendering for clarity

import os
import sys
import time
import threading
from typing import Dict, Any, Optional

COLORS = {
    "red":     "\033[91m",
    "green":   "\033[92m",
    "yellow":  "\033[93m",
    "blue":    "\033[94m",
    "magenta": "\033[95m",
    "cyan":    "\033[96m",
    "white":   "\033[97m",
    "bold":    "\033[1m",
    "dim":     "\033[2m",
    "reset":   "\033[0m",
}

LABEL_COLORS = ["red", "blue", "green", "magenta", "yellow", "cyan", "white"]

CALIBRATION_COLORS = {
    "very confident": "green",
    "confident":      "blue",
    "uncertain":      "yellow",
    "very uncertain": "red",
}


def color(text: str, col: str, disabled: bool = False) -> str:
    if disabled:
        return text
    code = COLORS.get(col, "")
    reset = COLORS["reset"]
    return f"{code}{text}{reset}"


def bold(text: str, disabled: bool = False) -> str:
    return color(text, "bold", disabled)


def dim(text: str, disabled: bool = False) -> str:
    return color(text, "dim", disabled)


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def get_terminal_width() -> int:
    try:
        return os.get_terminal_size().columns
    except:
        return 80


class Spinner:
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str, no_color: bool):
        self.message  = message
        self.no_color = no_color
        self.running  = False
        self.thread   = None

    def _spin(self):
        i = 0
        while self.running:
            frame = self.FRAMES[i % len(self.FRAMES)]
            c_frame = color(frame, "cyan", self.no_color)
            sys.stdout.write(f"\r{c_frame} {self.message}")
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        sys.stdout.write("\r" + " " * (len(self.message) + 4) + "\r")
        sys.stdout.flush()


def spinner_start(message: str, no_color: bool) -> Spinner:
    sp = Spinner(message, no_color)
    sp.start()
    return sp


def spinner_stop(sp: Optional[Spinner]):
    if sp:
        sp.stop()


def print_banner(no_color: bool = False):
    banner = [
        "",
        "  ██████╗██╗      █████╗ ██████╗ ██╗████████╗██╗   ██╗",
        "  ██╔════╝██║     ██╔══██╗██╔══██╗██║╚══██╔══╝╚██╗ ██╔╝",
        "  ██║     ██║     ███████║██████╔╝██║   ██║    ╚████╔╝ ",
        "  ██║     ██║     ██╔══██║██╔══██╗██║   ██║     ╚██╔╝  ",
        "  ╚██████╗███████╗██║  ██║██║  ██║██║   ██║      ██║   ",
        "   ╚═════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝   ╚═╝      ╚═╝   ",
        "",
        "  Explainable AI Text Classifier · powered by Ollama",
        "",
    ]
    for line in banner:
        if "██" in line:
            print(color(line, "cyan", no_color))
        elif "Explainable" in line:
            print(color(line, "dim", no_color))
        else:
            print(line)


def render_bar(value: int, width: int = 30, col: str = "green", no_color: bool = False) -> str:
    filled = int(width * value / 100)
    empty  = width - filled
    bar    = color("█" * filled, col, no_color) + color("░" * empty, "dim", no_color)
    return f"[{bar}]"


def render_mini_bar(value: int, width: int = 20, col: str = "cyan", no_color: bool = False) -> str:
    filled = int(width * value / 100)
    empty  = width - filled
    bar    = color("▓" * filled, col, no_color) + color("░" * empty, "dim", no_color)
    return f"{bar}"


def print_results(result: Dict[str, Any], no_color: bool = False):
    w = min(get_terminal_width(), 90)
    sep = color("─" * w, "dim", no_color)

    scores      = result["scores"]
    winner      = scores[0]
    uncertainty = result["uncertainty"]
    signals     = result.get("signals", [])
    model       = result.get("model", "unknown")
    text        = result.get("input_text", "")
    labels      = result.get("labels", [])

    label_color_map = {l: LABEL_COLORS[i % len(LABEL_COLORS)] for i, l in enumerate(labels)}

    print()
    print(sep)

    print(f"  {bold('INPUT', no_color)}")
    words = text.split()
    line, lines = [], []
    for w_ in words:
        if sum(len(x) + 1 for x in line) + len(w_) > w - 6:
            lines.append(" ".join(line))
            line = [w_]
        else:
            line.append(w_)
    if line:
        lines.append(" ".join(line))
    for ln in lines:
        print(f"  {color(ln, 'white', no_color)}")

    print()
    print(f"  {dim('model: ' + model, no_color)}")
    print(sep)

    wcol = label_color_map.get(winner["label"], "green")
    print()
    print(f"  {bold('TOP CLASSIFICATION', no_color)}")
    print()
    print(f"  {color('▶  ' + winner['label'].upper(), wcol, no_color)}  "
          f"{bold(str(winner['score']) + '%', no_color)}")
    print()
    print(f"  {dim(winner['reasoning'], no_color)}")
    print()
    print(sep)

    print()
    print(f"  {bold('LABEL SCORES', no_color)}")
    print()

    bar_w = min(28, w - 40)
    for s in scores:
        lcol = label_color_map.get(s["label"], "cyan")
        pct_str = f"{s['score']:3d}%"
        bar = render_bar(s["score"], bar_w, lcol, no_color)
        label_str = color(f"{s['label']:<16}", lcol, no_color)
        print(f"  {label_str} {bar} {bold(pct_str, no_color)}")
        print(f"  {' ' * 16}  {dim(s['reasoning'], no_color)}")
        print()

    print(sep)

    print()
    print(f"  {bold('UNCERTAINTY ANALYSIS', no_color)}")
    print()

    entropy_col = "green" if uncertainty["entropy"] < 35 else ("yellow" if uncertainty["entropy"] < 65 else "red")
    margin_col  = "green" if uncertainty["margin"]  > 35 else ("yellow" if uncertainty["margin"]  > 15 else "red")
    cal_col     = CALIBRATION_COLORS.get(uncertainty["calibration"], "cyan")

    e_bar = render_mini_bar(uncertainty["entropy"], 24, entropy_col, no_color)
    print(f"  {bold('Entropy', no_color)}     {e_bar} {color(str(uncertainty['entropy']) + '/100', entropy_col, no_color)}")
    e_interp = (
        "Low — model is concentrated on one label"   if uncertainty["entropy"] < 35 else
        "Moderate — some spread across labels"       if uncertainty["entropy"] < 65 else
        "High — confidence spread widely, uncertain"
    )
    print(f"  {dim('             ' + e_interp, no_color)}")
    print()

    m_bar = render_mini_bar(min(uncertainty["margin"], 100), 24, margin_col, no_color)
    print(f"  {bold('Margin', no_color)}      {m_bar} {color(str(uncertainty['margin']) + ' pts', margin_col, no_color)}")
    m_interp = (
        "Large gap — clear winner over runner-up"     if uncertainty["margin"] > 35 else
        "Moderate gap — reasonably clear decision"    if uncertainty["margin"] > 15 else
        "Narrow gap — close call, treat with caution"
    )
    print(f"  {dim('             ' + m_interp, no_color)}")
    print()

    cal_str = color(uncertainty["calibration"].upper(), cal_col, no_color)
    print(f"  {bold('Calibration', no_color)} {cal_str}")
    print(f"  {dim('             ' + uncertainty['summary'], no_color)}")
    print()
    print(sep)

    if signals:
        print()
        print(f"  {bold('KEY SIGNALS', no_color)}")
        print()
        for sig in signals:
            icon = sig.get("icon", "•")
            txt  = sig.get("text", "")
            print(f"  {icon}  {txt}")
        print()
        print(sep)

    print()

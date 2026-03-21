# clarity 🔍
### Explainable AI Text Classifier — CLI Tool

> *"Not just what the model thinks — but how sure it is, and why."*

## Prerequisites

1. Install Ollama: https://ollama.com
2. Pull a model:
   ```bash
   ollama pull llama3.2
   # or
   ollama pull qwen2.5:7b
   ```
3. Start Ollama:
   ```bash
   ollama serve
   ```

## Usage

```bash
# Single classification
python clarity.py -t "I love this product!" -l positive negative neutral

# Choose model
python clarity.py -t "The Fed raised rates." -l politics economics sports -m qwen2.5:7b

# Interactive loop
python clarity.py --interactive

# 3 built-in demos
python clarity.py --demo

# No color (for piping or saving to file)
python clarity.py -t "some text" -l label1 label2 --no-color
```

## How It Works

clarity splits the work between the LLM and Python math:

| Task | Who does it |
|------|------------|
| Understand the text | LLM (llama3.2 / qwen2.5) |
| Assign confidence scores per label | LLM |
| Identify key linguistic signals | LLM |
| Compute entropy | Python — Shannon entropy formula |
| Compute margin | Python — exact subtraction |
| Derive calibration tier | Python — threshold rules |
| Generate summary | Python — template string |

**Why split?** The LLM is good at language; math should never be left to a language model.

## XAI Metrics

| Metric | Range | How computed |
|--------|-------|--------------|
| Entropy | 0–100 | Shannon entropy of score distribution, normalized to 0–100. 0 = all weight on one label, 100 = perfectly uniform |
| Margin | 0–100 pts | `score[#1] − score[#2]` — exact subtraction. Small = close call |
| Calibration | tier | Derived from entropy + margin thresholds: `very confident / confident / uncertain / very uncertain` |

### Entropy formula
```
p_i     = score_i / 100
H       = -Σ (p_i × log₂(p_i))   # Shannon entropy in bits
H_max   = log₂(n)                 # maximum entropy for n labels
entropy = round((H / H_max) × 100)
```

### Calibration thresholds
```
entropy < 25 and margin > 40  →  very confident
entropy < 50 and margin > 20  →  confident
entropy < 70                  →  uncertain
else                          →  very uncertain
```

## Architecture

```
clarity/
├── clarity.py     # CLI entrypoint — argument parsing, modes (single/interactive/demo)
├── classifier.py  # Ollama API call, JSON parsing, math-based uncertainty computation
├── display.py     # ANSI terminal rendering — colors, progress bars, spinner, banner
├── config.py      # Models list, API URL, system prompt
└── README.md
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.8+ (zero pip dependencies — stdlib only) |
| AI Runtime | Ollama (local, private — no internet required) |
| Models | llama3.2 · qwen2.5:7b (and variants) |
| API | Ollama REST via `urllib` |
| XAI Math | `math` module — Shannon entropy, threshold calibration |
| UI | ANSI terminal — colors, Unicode bars, spinner |

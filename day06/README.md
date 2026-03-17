# Day 6 — Embeddings & Similarity Search

> Part of the **30-Day AI Engineering Challenge**

A fully offline semantic similarity search app built as a single HTML file. No build step, no frameworks — just vanilla JS talking to a local Ollama instance.

## What it does

- Loads a configurable corpus of sentences
- Embeds the query + all corpus sentences via `nomic-embed-text` (768-dim vectors)
- Computes cosine similarity in-browser
- Ranks results and colour-codes by similarity score
- Shows a 512-cell vector heatmap for each result (hover for dimension values)

## Prerequisites

- [Ollama](https://ollama.com/) installed
- `nomic-embed-text` model pulled

## Setup

```bash
# 1. Pull the model (first time only)
ollama pull nomic-embed-text

# 2. Start Ollama with CORS enabled
set OLLAMA_ORIGINS=* && ollama serve

# 3. Start the app
cd day6-embeddings
npm start
# → http://localhost:3000
```

On macOS/Linux use `export OLLAMA_ORIGINS=*` instead of `set`.

## Usage

1. Open `http://localhost:3000` — the status bar should turn green
2. Edit corpus sentences (add / delete / modify inline)
3. Type a query in the text area
4. Click **Run similarity search**
5. Results appear ranked by cosine similarity with vector heatmaps

## Scoring guide

| Score | Colour | Meaning |
|-------|--------|---------|
| ≥ 0.75 | Green | Strong semantic match |
| ≥ 0.50 | Amber | Related / topically similar |
| < 0.50 | Gray  | Weak or unrelated |

## API used

```
POST http://localhost:11434/api/embed
{
  "model": "nomic-embed-text",
  "input": ["sentence one", "sentence two", ...]
}
→ { "embeddings": [[float, ...], ...] }
```

## Key concepts

- **Embeddings** — dense vector representations of text where semantic similarity ≈ geometric proximity
- **Cosine similarity** — `dot(a, b) / (|a| × |b|)` — measures the angle between two vectors, ignoring magnitude
- **768 dimensions** — the size of each `nomic-embed-text` vector
- **Vector DB** — in production you'd store pre-computed vectors in pgvector, Qdrant, or Weaviate for fast ANN search

## Common issues

| Problem | Fix |
|---------|-----|
| Status bar stays red | Start Ollama: `ollama serve` |
| CORS error in console | Use `set OLLAMA_ORIGINS=* && ollama serve` |
| "model not found" | `ollama pull nomic-embed-text` |
| Slow first search | Model is loading — subsequent searches are faster |

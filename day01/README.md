# Day 01 — LLM Basics

A multi-turn CLI chatbot powered by GPT-4o-mini via the OpenAI API.

## What it does

- Maintains full conversation history across turns so the model remembers context
- Accepts user messages from stdin and prints the assistant's reply
- Type `quit` to exit cleanly

## Setup

1. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # macOS/Linux
   source venv/bin/activate
   # Windows
   venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your API key**

   Copy `.env.example` to `.env` and fill in your key:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env`:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Run the chatbot**
   ```bash
   python chat.py
   ```

## Key concepts learned

- First API call to GPT-4o-mini
- Multi-turn conversation via `messages` history
- `temperature` and `max_tokens` parameters
- Loading secrets with `python-dotenv`

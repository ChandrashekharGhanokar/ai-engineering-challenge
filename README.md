# AI Engineering Challenge

Daily hands-on projects building AI Engineering fundamentals from scratch.

## Structure

| Day | Topic | Description |
|-----|-------|-------------|
| [day01](./day01/) | LLM Basics | Multi-turn CLI chatbot with GPT-4o-mini |
| [day02](./day02/) | LLM Judge | Prompt comparison with an LLM-as-judge evaluator |

## Getting started

Each day is a self-contained project with its own `README.md`, `requirements.txt`, and source code. Navigate into a day's folder and follow its setup instructions.

```bash
cd day01
python -m venv venv && source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env  # then add your OPENAI_API_KEY
python chat.py
```

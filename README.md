# AI Engineering Challenge

Daily hands-on projects building AI Engineering fundamentals from scratch.

## Structure

| Day | Topic | Description |
|-----|-------|-------------|
| [day01](./day01/) | LLM Basics | Multi-turn CLI chatbot with GPT-4o-mini |
| [day02](./day02/) | LLM Judge | Prompt comparison with an LLM-as-judge evaluator |
| [day03](./day03/) | Structured Output | Streamlit job posting parser with Gemini 2.5 Flash + Pydantic |
| [day04](./day04/) | Local RAG | PDF Q&A bot with Ollama + FAISS (fully local) |
| [day05](./day05/) | Finance Assistant | Tool-calling agent with Streamlit UI — stocks, exchange rates, compound interest |
| [day06](./day06/) | Embeddings | Semantic similarity search with nomic-embed-text + Ollama  |
| [day07](./day07/) | Research Agent | Autonomous deep research agent with Ollama tool-calling, Tavily search, and Jina Reader |

## Getting started

Each day is a self-contained project with its own `README.md`, `requirements.txt`, and source code. Navigate into a day's folder and follow its setup instructions.

```bash
cd day01
python -m venv venv && source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env  # then add your OPENAI_API_KEY
python chat.py

# day03 and day05 use Streamlit:
# streamlit run day03/app.py
# streamlit run day05/app.py
```

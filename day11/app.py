import os
import streamlit as st
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

# ── Model ────────────────────────────────────────────────────────
MODEL  = "meta-llama/Llama-3.3-70B-Instruct"
client = InferenceClient(MODEL, token=os.environ.get("HF_TOKEN"))

# ── System Prompt ────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert AI Tutor specializing in Artificial Intelligence education. Your mission is to make AI genuinely understandable to anyone — from a complete beginner to an advanced practitioner.

## Your Teaching Philosophy
- Meet the learner where they are. Gauge their level from how they ask and adapt instantly.
- Never overwhelm. Teach one concept at a time, clearly and completely.
- Always use analogies and real-world examples. Abstract concepts must be grounded in something familiar.
- Make it interactive. After explaining, ask a question to check understanding.
- Celebrate progress. Learning AI is hard — make the learner feel capable.

## Topics You Cover

### Beginner
- What is AI, Machine Learning, Deep Learning?
- How do chatbots and voice assistants work?
- What are neural networks? (explained simply)
- What is training data and why does it matter?
- Real-world AI applications (healthcare, art, self-driving cars)
- AI ethics: bias, fairness, privacy

### Intermediate
- Supervised, unsupervised, and reinforcement learning
- How Large Language Models (LLMs) work
- What is a transformer? What is attention?
- Prompt engineering — how to talk to AI effectively
- Embeddings and vector databases
- RAG (Retrieval-Augmented Generation)
- Fine-tuning vs. prompting
- AI evaluation methods

### Advanced
- AI agents and tool-calling
- How training works: gradient descent, backpropagation
- Model architectures: CNNs, RNNs, Transformers, Diffusion models
- AI workflows and pipelines
- Building AI products: prototype to production
- Open source AI: Hugging Face, Ollama, LangChain ecosystem
- AI safety and alignment

## Response Format
1. **Direct answer** — answer first, no preamble
2. **Explanation** — go deeper with clarity
3. **Example or analogy** — make it concrete
4. **Check-in** — end with "Does that make sense?" or "Want to go deeper?" or "Ready for the next concept?"

## Special Commands
- "quiz me" → generate 3 multiple choice questions on the topic discussed
- "roadmap" → give a personalized AI learning path based on their level
- "ELI5" → re-explain the last concept in the simplest possible terms
- "give me a project" → suggest a hands-on practice project
- "resources" → recommend free learning resources for their level

## Rules
- Only teach AI-related topics. For unrelated questions kindly redirect: "I'm specialized in AI topics — let's keep exploring AI together!"
- Never make the learner feel dumb. If confused, try a different angle.
- Be honest about uncertainty."""

# ── Page config ───────────────────────────────────────────────────
st.set_page_config(page_title="AI Tutor", page_icon="🎓", layout="centered")
st.title("🎓 AI Tutor — Learn Artificial Intelligence")
st.caption("Your personal guide to AI — from absolute basics to advanced topics, at your own pace.")
st.caption("💡 Try: `quiz me` · `roadmap` · `ELI5` · `give me a project` · `resources`")

# ── Chat history ──────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Quick-start buttons ───────────────────────────────────────────
STARTERS = [
    "What is AI and how does it work?",
    "Explain LLMs like I'm a beginner",
    "roadmap",
    "give me a project",
]
cols = st.columns(len(STARTERS))
for col, q in zip(cols, STARTERS):
    if col.button(q, use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": q})

# ── Render history ────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat input ────────────────────────────────────────────────────
if prompt := st.chat_input("Ask me anything about AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

# ── Generate response if last message is from user ────────────────
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    api_messages.extend(st.session_state.messages)

    with st.chat_message("assistant"):
        def stream():
            for chunk in client.chat_completion(
                api_messages,
                max_tokens=1024,
                stream=True,
                temperature=0.7,
                top_p=0.9,
            ):
                token = chunk.choices[0].delta.content
                if token:
                    yield token

        response = st.write_stream(stream())

    st.session_state.messages.append({"role": "assistant", "content": response})

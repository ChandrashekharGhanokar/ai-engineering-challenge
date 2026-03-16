import json
import streamlit as st
from openai import OpenAI
from tools import TOOLS, run_tool

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Finance Assistant", layout="wide")

# ── Ollama client ─────────────────────────────────────────────────────────────
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
MODEL = "llama3.2"

SYSTEM_PROMPT = """You are a helpful finance assistant. You have access to tools that can:
- Look up real-time stock prices (use get_stock_price)
- Get current exchange rates between currencies (use get_exchange_rate)
- Calculate compound interest for investments (use calculate_compound_interest)

Always use the appropriate tool when the user asks about stocks, currencies, or investment calculations.
Present financial data clearly and provide brief helpful context with your answers."""

# ── Session state init ────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

if "tool_calls_log" not in st.session_state:
    st.session_state.tool_calls_log = []

if "chat_display" not in st.session_state:
    # Stores (role, content, tool_info_list) tuples for rendering
    st.session_state.chat_display = []

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Finance Assistant")
    st.caption("Powered by Ollama + Tool Calling")
    st.divider()

    st.subheader("Tool Activity")
    if st.session_state.tool_calls_log:
        for entry in reversed(st.session_state.tool_calls_log):
            with st.expander(f"🔧 {entry['tool']}", expanded=False):
                st.json(entry["args"])
                st.caption("Result:")
                try:
                    st.json(json.loads(entry["result"]))
                except Exception:
                    st.text(entry["result"])
    else:
        st.caption("No tools used yet.")

    st.divider()
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.session_state.tool_calls_log = []
        st.session_state.chat_display = []
        st.rerun()

# ── Main area ─────────────────────────────────────────────────────────────────
st.title("Finance Assistant")

# Suggested prompts
st.markdown("**Try asking:**")
cols = st.columns(4)
suggestions = [
    "What is the current price of TSLA?",
    "Convert 1000 USD to INR",
    "What is TCS.NS price in USD?",
    "If I invest $5000 at 8% for 10 years?",
]
prompt_clicked = None
for col, suggestion in zip(cols, suggestions):
    with col:
        if st.button(suggestion, use_container_width=True):
            prompt_clicked = suggestion

st.divider()

# Render chat history
for role, content, tool_infos in st.session_state.chat_display:
    with st.chat_message(role):
        if tool_infos:
            for ti in tool_infos:
                with st.expander(f"🔧 Tool called: {ti['tool']}"):
                    st.markdown("**Arguments:**")
                    st.json(ti["args"])
                    st.markdown("**Result:**")
                    try:
                        st.json(json.loads(ti["result"]))
                    except Exception:
                        st.text(ti["result"])
        if content:
            st.markdown(content)

# ── Agent loop ────────────────────────────────────────────────────────────────
def run_agent(user_input: str):
    # Add user message to history and display
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.chat_display.append(("user", user_input, []))

    with st.chat_message("user"):
        st.markdown(user_input)

    # Agentic loop
    with st.chat_message("assistant"):
        tool_infos_this_turn = []
        tool_placeholder = st.empty()
        final_content = ""

        while True:
            response = client.chat.completions.create(
                model=MODEL,
                messages=st.session_state.messages,
                tools=TOOLS,
                tool_choice="auto",
            )

            msg = response.choices[0].message

            if msg.tool_calls:
                # Process each tool call
                tool_calls_data = []
                for tc in msg.tool_calls:
                    tool_name = tc.function.name
                    tool_args = json.loads(tc.function.arguments)

                    # Show inline expander
                    with st.expander(f"🔧 Tool called: {tool_name}", expanded=True):
                        st.markdown("**Arguments:**")
                        st.json(tool_args)

                        with st.spinner(f"Running {tool_name}..."):
                            result = run_tool(tool_name, tool_args)

                        st.markdown("**Result:**")
                        try:
                            st.json(json.loads(result))
                        except Exception:
                            st.text(result)

                    # Log it
                    log_entry = {"tool": tool_name, "args": tool_args, "result": result}
                    tool_infos_this_turn.append(log_entry)
                    st.session_state.tool_calls_log.append(log_entry)

                    tool_calls_data.append({
                        "id": tc.id,
                        "name": tool_name,
                        "args": tool_args,
                        "result": result,
                    })

                # Append assistant tool-call message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": json.dumps(tc["args"]),
                            },
                        }
                        for tc in tool_calls_data
                    ],
                })

                # Append tool results
                for tc in tool_calls_data:
                    st.session_state.messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": tc["result"],
                    })

            else:
                # Final text answer
                final_content = msg.content or ""
                st.markdown(final_content)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_content,
                })
                st.session_state.chat_display.append(
                    ("assistant", final_content, tool_infos_this_turn)
                )
                break


# ── Handle input ──────────────────────────────────────────────────────────────
user_query = st.chat_input("Ask about stocks, currencies, or investments...")

if prompt_clicked:
    run_agent(prompt_clicked)
elif user_query:
    run_agent(user_query)

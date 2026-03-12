from openai import OpenAI
import os
from dotenv import load_dotenv


load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

TASK = "Explain what a large language model is in 2-3 sentences."

PROMPT_A = [
    {"role": "system", "content": "You are a helpful AI assistant."},
    {"role": "user", "content": TASK}
]

PROMPT_B = [
    {"role": "system", "content": "You are a technical expert explaining concepts to a software engineer. Be precise and use correct terminology."},
    {"role": "user", "content": TASK}
]


def get_response(messages):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=512,
        messages=messages
    )
    return response.choices[0].message.content


response_a = get_response(PROMPT_A)
response_b = get_response(PROMPT_B)

print("=== Response A (generic system prompt) ===")
print(response_a)
print()
print("=== Response B (expert system prompt) ===")
print(response_b)
print()

judge_messages = [
    {
        "role": "system",
        "content": (
            "You are an impartial judge evaluating two AI responses to the same task. "
            "Assess clarity, accuracy, and usefulness. "
            "Reply in this exact format:\n"
            "Winner: A or B\n"
            "Reason: <one sentence>"
        )
    },
    {
        "role": "user",
        "content": (
            f"Task: {TASK}\n\n"
            f"Response A:\n{response_a}\n\n"
            f"Response B:\n{response_b}"
        )
    }
]

verdict = get_response(judge_messages)

print("=== Judge's Verdict ===")
print(verdict)

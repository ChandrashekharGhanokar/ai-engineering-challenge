from openai import OpenAI
import os
from dotenv import load_dotenv


load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


conversation_history = [
    {"role": "system", "content": "You are a helpful AI assistant."}
]

print("Chat with GPT-4o-mini (type 'quit' to exit)\n")

while True:
    user_input = input("You: ")

    if user_input.lower() == "quit":
        break

    conversation_history.append({
        "role": "user",
        "content": user_input
    })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1024,
        messages=conversation_history
    )

    assistant_reply = response.choices[0].message.content

    conversation_history.append({
        "role": "assistant",
        "content": assistant_reply
    })

    print(f"\nGPT: {assistant_reply}\n")

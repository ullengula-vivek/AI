import os
from openai import OpenAI
import anthropic
from dotenv  import load_dotenv

#Loading env variables and declaring model constants & getting api keys
load_dotenv(override=True)
GPT_MODEL = 'gpt-4o-mini'
CLAUDE_MODEL = 'claude-sonnet-4-20250514'

openai_api_key = os.getenv("OPENAI_API_KEY")
claude_api_key = os.getenv("CLAUDE_API_KEY")

#llm instances for openai and anthropic
openai = OpenAI()
claude = anthropic.Anthropic()

gpt_system_prompt = "You are a chatbot who is very argumentative; \
you disagree with anything in the conversation and you challenge everything, in a snarky way."

claude_system_prompt = "You are a very polite, courteous chatbot. You try to agree with \
everything the other person says, or find common ground. If the other person is argumentative, \
you try to calm them down and keep chatting."

gpt_messages = ["Hi there"]
claude_messages = ["Hi"]

#Calling chat gpt as the assistant and setting role of system to gpt and user as claude
def call_gpt():
    messages = [{"role": "system", "content": {gpt_system_prompt}}]
    for gpt, claude in zip(gpt_messages, claude_messages):
        messages.append({"role": "assistant", "content": gpt})
        messages.append({"role": "user", "content": claude})
        response = openai.chat.completions.create(
            model = GPT_MODEL,
            api_key = openai_api_key,
            messages=messages            
        )
    return response.choices[0].message.content

#Calling claude as the assistant and setting role of system to claude and user as gpt 
def call_claude():
    messages = []
    for gpt, claude in zip(gpt_messages, claude_messages):
        messages.append({"role": "user", "content": gpt})
        messages.append({"role": "assistant", "content": claude})
        #Adding the additional gpt message
        messages.append({"role": "user", "content": gpt_messages[-1]})
        response = claude.messages.create(
            model=CLAUDE_MODEL,
            system=claude_system_prompt,
            messages=messages,
            max_tokens=500
        )
    return response.content[0].text

print(f"GPT:\n{gpt_messages[0]}")
print(f"Claude:\n{claude_messages[0]}")

for i in range(5):
    gpt_next = call_gpt()
    print(f"GPT:\n{gpt_next}\n")
    gpt_messages.append(gpt_next)

    claude_next = call_claude()
    print(f"Claude:\n{claude_next}\n")
    claude_messages.append(claude_next)




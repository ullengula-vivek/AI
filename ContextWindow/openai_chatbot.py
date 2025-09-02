import os
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

#Loading the env variables
load_dotenv(override=True)

#Getting the model and api key from env
GPT_MODEL = os.getenv("GPT_MODEL") 
openai_api_key = os.getenv("OPENAI_API_KEY")

#Creating an instance of openai
openai = OpenAI()

#Defining the system prompt
system_prompt = "You are StrideBot, a friendly and knowledgeable shoe store assistant. Greet customers warmly, ask about their needs, and help them find the right shoes for any occasion (casual, formal, athletic, kids, etc.). Provide style suggestions, sizing guidance, and info on store policies. Be conversational, supportive, and professional. If unsure, suggest asking an in-store associate. Do not invent prices or promotions."

#Creating a chat function with history and the current message
def chat(message, history):
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "system", "content": message}]

    stream = openai.chat.completions.create(
        model=GPT_MODEL,
        messages=messages,
        stream=True
    )

    response = ""
    for chunk in stream:
        response += chunk.choices[0].delta.content or ''
        yield response


#Gradio code
gr.ChatInterface(fn=chat, type="messages").launch()
import os
import json
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

model = os.getenv("GPT_MODEL")
openai_api_key = os.getenv("OPENAI_API_KEY")

openai = OpenAI()

system_prompt = (
    "You are a helpful assistant for flightAI. "
    "You provide information about flights and their prices. "
    "Give precise and short answers. "
    "If you don't know the answer, just say so."
)

# Tools data
ticket_prices = {
    "london": "₹58,000",
    "paris": "₹62,000",
    "tokyo": "₹75,000",
    "new york": "₹70,000",
    "dubai": "₹22,000",
    "singapore": "₹28,000"
}

dates_available = {
    "london": {"price": "₹58,000", "dates": ["2025-10-05 01:35", "2025-10-06 14:25", "2025-10-07 07:00"]},
    "paris": {"price": "₹62,000", "dates": ["2025-10-10 02:00", "2025-10-12 15:30", "2025-10-15 20:00"]},
    "tokyo": {"price": "₹75,000", "dates": ["2025-10-08 05:00", "2025-10-11 11:15", "2025-10-14 22:45"]},
    "new york": {"price": "₹70,000", "dates": ["2025-10-03 03:50", "2025-10-07 17:20", "2025-10-09 23:10"]},
    "dubai": {"price": "₹22,000", "dates": ["2025-10-05 06:30", "2025-10-06 13:00", "2025-10-08 19:45"]},
    "singapore": {"price": "₹28,000", "dates": ["2025-10-04 08:15", "2025-10-06 14:50", "2025-10-09 21:00"]}
}

# Functions
def get_ticket_price(destination_city):
    print(f"Tool get_ticket_price called for {destination_city}")
    city = destination_city.lower()
    return ticket_prices.get(city, "Unknown")

def get_available_dandt(destination_city):
    print(f"Tool get_available_dandt called for {destination_city}")
    city = destination_city.lower()
    return dates_available.get(city, "NA")

# Tool definitions
price_function = {
    "name": "get_ticket_price",
    "description": "Get the price of a return ticket to the destination city.",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to travel to"
            }
        },
        "required": ["destination_city"]
    }
}

date_function = {
    "name": "get_available_dandt",
    "description": "Get the available dates for the destination city.",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city for which the customer wants to know the available dates"
            }
        },
        "required": ["destination_city"]
    }
}

tools = [
    {"type": "function", "function": price_function},
    {"type": "function", "function": date_function}
]

# Tool call handler
def handle_tool_call(message):
    tool_call = message.tool_calls[0]
    func_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    city = arguments.get("destination_city")

    if func_name == "get_ticket_price":
        result = get_ticket_price(city)
        content = {"destination_city": city, "price": result}
    elif func_name == "get_available_dandt":
        result = get_available_dandt(city)
        content = {"destination_city": city, "dates_info": result}
    else:
        content = {"error": "Unknown tool"}

    return {
        "role": "tool",
        "content": json.dumps(content),
        "tool_call_id": tool_call.id
    }

# Chat handler
def chat(message, history):
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]

    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools
    )

    reply = response.choices[0].message

    if reply.tool_calls:
        tool_response = handle_tool_call(reply)
        messages.append(reply)
        messages.append(tool_response)

        final_response = openai.chat.completions.create(
            model=model,
            messages=messages
        )
        return final_response.choices[0].message.content
    else:
        return reply.content

# Launch Gradio
gr.ChatInterface(fn=chat, type="messages").launch()

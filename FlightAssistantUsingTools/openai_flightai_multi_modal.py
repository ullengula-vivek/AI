import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

#Image gen imports
import base64
from PIL import Image
from io import BytesIO

load_dotenv(override=True)

model = os.getenv("GPT_MODEL")
openai_api_key = os.getenv("OPENAI_API_KEY")

openai = OpenAI()

system_message = "You are a helpful assistant for an Airline called FlightAI. "
system_message += "Give short, courteous answers, no more than 1 sentence. "
system_message += "Always be accurate. If you don't know the answer, say so."

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

def get_ticket_price(destination_city):
    print(f"Tool get_ticket_price is called for {destination_city}")
    city = destination_city.lower()
    return ticket_prices.get(city, "Unknown")

def get_available_dates(destination_city):
    print(f"Tool get_available_dates is called for {destination_city}")
    city = destination_city.lower()
    return dates_available.get(city, "NA")
"""
def book_ticket(destination_city, choosen_date_time):
    print(f"Tool book_ticket is called for {destination_city} - {choosen_date}")
    city = destination_city.lower()
    date = dates_available.get(choosen_date_time)
    if  date:
"""

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
    "name": "get_available_dates",
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

def handle_tool_call(tool_response_message):
    tool_call = tool_response_message.tool_calls[0]
    func_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    city = arguments.get("destination_city")
    #date = arguments.get("choosen_date")

    if func_name == "get_ticket_price":
        result = get_ticket_price(city)
        content = {"destination_city": city, "price": result}
    elif func_name == "get_available_dates":
        result = get_available_dates(city)
        content = {"destination_city": city, "dates_info": result}
    else:
        content = {"error": "Unknown tool"}

    response = {
        "role": "tool",
        "content": json.dumps(content),
        "tool_call_id": tool_call.id
    }

    return response, city

def artist(city):
    image_response = openai.images.generate(
        model="dall-e-3",
        prompt=f"An image representing a vacation in {city}, showing tourist spots and everything unique about {city}, in a simple art style",
        size = "1024x1024",
        n=1,
        response_format="b64_json"
    )

    image_base64 = image_response.data[0].b64_json
    image_data = base64.b64decode(image_base64)
    return Image.open(BytesIO(image_data))
    

def chat( history):
    messages = [{"role": "system", "content": system_message}] + history

    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools
    )

    image = None

    if response.choices[0].message.tool_calls:
        message = response.choices[0].message
        tool_response, city = handle_tool_call(message)
        messages.append(message)
        messages.append(tool_response)
        image = artist(city)

        response = openai.chat.completions.create(
            model=model,
            messages=messages
        )
    
    reply = response.choices[0].message.content
    
    history += [{"role": "assistant", "content": reply}]
    
    return history, image

#Gradio 

with gr.Blocks() as ui:
    with gr.Row():
        chatbot = gr.Chatbot(height=500, type="messages")
        image_output = gr.Image(height=500)
    with gr.Row():
        entry = gr.Textbox(label="Chat with our AI Assistant:")
    with gr.Row():
        clear = gr.ClearButton()

    def do_entry(message, history):
        history += [{"role":"user", "content":message}]
        return "", history

    entry.submit(do_entry, inputs=[entry, chatbot], outputs=[entry, chatbot]).then(
        chat, inputs=chatbot, outputs=[chatbot, image_output]
    )
    clear.click(lambda: None, inputs=None, outputs=chatbot, queue=False)

ui.launch(inbrowser=True)
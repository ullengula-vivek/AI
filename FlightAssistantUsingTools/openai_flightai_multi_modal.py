import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

# Image gen imports
import base64
from PIL import Image
from io import BytesIO
from datetime import datetime

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

# ✅ Normalize date format
def format_dates(dates_list):
    formatted = []
    for d in dates_list:
        try:
            dt = datetime.strptime(d, "%Y-%m-%d %H:%M")
            formatted.append(dt.strftime("%Y-%m-%d %H:%M"))
        except ValueError:
            continue
    return formatted

for city, info in dates_available.items():
    dates_available[city]["dates"] = format_dates(info["dates"])

# ---------------- TOOLS ---------------- #

def get_ticket_price(destination_city):
    print(f"Tool get_ticket_price is called for {destination_city}")
    city = destination_city.lower()
    return ticket_prices.get(city, "Unknown")

def get_available_dates(destination_city):
    print(f"Tool get_available_dates is called for {destination_city}")
    city = destination_city.lower()
    available = dates_available.get(city, None)

    if not available:
        return {"status": "failed", "message": "No flights found"}

    return {
        "status": "success",
        "city": city,
        "price": available["price"],
        "available_slots": available["dates"]
    }

def book_ticket(destination_city, chosen_date_time):
    print(f"Tool book_ticket is called for {destination_city} - {chosen_date_time}")
    city = destination_city.lower()
    available = dates_available.get(city, None)

    if not available:
        return {"status": "failed", "message": f"No flights found for {city}"}

    if chosen_date_time not in available["dates"]:
        return {
            "status": "failed",
            "message": f"Invalid slot. Available options are: {available['dates']}"
        }

    ticket_text = f"""
--- FlightAI Ticket Confirmation ---
Destination: {city.title()}
Date & Time: {chosen_date_time}
Price: {available['price']}
Status: Confirmed
"""

    with open("ticket.txt", "w", encoding="utf-8") as f:
        f.write(ticket_text)

    return {
        "status": "success",
        "message": "Ticket booked successfully",
        "city": city,
        "date": chosen_date_time
    }

# ---------------- TOOL DEFINITIONS ---------------- #

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

ticket_function = {
    "name": "book_ticket",
    "description": "Book a ticket for a given city and date.",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {"type": "string", "description": "The city to book a ticket for"},
            "chosen_date_time": {"type": "string", "description": "The exact date/time to book (YYYY-MM-DD HH:MM)"}
        },
        "required": ["destination_city", "chosen_date_time"]
    }
}

tools = [
    {"type": "function", "function": price_function},
    {"type": "function", "function": date_function},
    {"type": "function", "function": ticket_function}
]

# ---------------- TOOL HANDLER ---------------- #

def handle_tool_call(tool_call):
    func_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)

    if func_name == "get_ticket_price":
        city = arguments.get("destination_city")
        result = get_ticket_price(city)
        content = {"destination_city": city, "price": result}

    elif func_name == "get_available_dates":    
        city = arguments.get("destination_city")
        result = get_available_dates(city)
        content = result

    elif func_name == "book_ticket":
        city = arguments.get("destination_city")
        date = arguments.get("chosen_date_time")
        result = book_ticket(city, date)
        content = result

    else:
        content = {"error": "Unknown tool"}

    return {
        "role": "tool",
        "content": json.dumps(content),
        "tool_call_id": tool_call.id
    }, content

# ---------------- IMAGE GENERATION ---------------- #

def artist(city):
    image_response = openai.images.generate(
        model="dall-e-3",
        prompt=f"An image representing a vacation in {city}, showing tourist spots and everything unique about {city}, in a simple art style",
        size="1024x1024",
        n=1,
        response_format="b64_json"
    )

    image_base64 = image_response.data[0].b64_json
    image_data = base64.b64decode(image_base64)
    return Image.open(BytesIO(image_data))

# ---------------- CHAT LOGIC ---------------- #

def chat(history):
    messages = [{"role": "system", "content": system_message}] + history

    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools
    )

    image = None
    tool_outputs = []

    while response.choices[0].message.tool_calls is not None:
        tool_calls = response.choices[0].message.tool_calls
        print("DEBUG: Tool calls found:", tool_calls)

        messages.append(response.choices[0].message)

        for tool_call in tool_calls:
            tool_response, content = handle_tool_call(tool_call)
            messages.append(tool_response)
            tool_outputs.append(content)

            # ✅ Image generation only after confirmed booking
            if content.get("status") == "success" and tool_call.function.name == "book_ticket":
                city = content.get("city")
                image = artist(city)

        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools
        )

    reply = response.choices[0].message.content
    history += [{"role": "assistant", "content": reply}]

    return history, image

# ---------------- GRADIO UI ---------------- #

with gr.Blocks() as ui:
    with gr.Row():
        chatbot = gr.Chatbot(height=500, type="messages")
        image_output = gr.Image(height=500)
    with gr.Row():
        entry = gr.Textbox(label="Chat with our AI Assistant:")
    with gr.Row():
        clear = gr.ClearButton()

    def do_entry(message, history):
        history += [{"role": "user", "content": message}]
        return "", history

    entry.submit(do_entry, inputs=[entry, chatbot], outputs=[entry, chatbot]).then(
        chat, inputs=chatbot, outputs=[chatbot, image_output]
    )
    clear.click(lambda: None, inputs=None, outputs=chatbot, queue=False)

ui.launch(inbrowser=True)

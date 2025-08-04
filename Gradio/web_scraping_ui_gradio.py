import os, requests
from openai import OpenAI
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import gradio as gr

#Loading env variables and getting api key
load_dotenv(override=True)
api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("GPT_MODEL")

#Calling an instance of openai
openai = OpenAI()

#Scraping the website
class Website:
    url: str
    text: str
    title: str
    def __init__(self, url):
        self.url = url
        response = requests.get(url)
        self.body = response.content
        soup = BeautifulSoup(self.body, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator="\n", strip=True)
        else:
            self.text = ""

    def get_all_contents(self):
        return f"Webpage Title:\n{self.title}\nWebpage Contents:\n{self.text}\n\n"
    
system_prompt = "You are an assistant that analyzes the contents of a company website landing page \
and creates a short brochure about the company for prospective customers, investors and recruits. Respond in markdown."
    
#Let's create a call that streams back results
def stream_gpt(user_prompt):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    response = openai.chat.completions.create(
        model=MODEL,
        messages=messages,
        stream=True
    )
    result = ""
    for chunk in response:
        result += chunk.choices[0].delta.content or ""
        yield result

#Using this function we will call the stream function
def stream_brochure(company_name, url, tone="normal"):
    yield ""
    user_prompt = f"Please generate a company brochure for {company_name} and keep your tone {tone}\. Here is their landing page:\n"
    user_prompt += Website(url).get_all_contents()
    result = stream_gpt(user_prompt)
    yield from result

view = gr.Interface(
    fn=stream_brochure,
    inputs=[
        gr.Textbox(label="Company name:"),
        gr.Textbox(label="Landing page URL including http:// or https://"),
        gr.Textbox(label="Tone:")],
    outputs=[gr.Markdown(label="Brochure:")],
    flagging_mode="never"
)
view.launch()




import os, requests
from openai import OpenAI
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from IPython.display import Markdown, display

#Getting the OpenAI api key from the env file using dotenv's load env method
load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

#Creating an instance of Openai
openai = OpenAI()

headers = {
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

class Website:
    def __init__(self, url):
        self.url = url
        response = requests.get(url,headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        self.text = soup.body.get_text(separator="\n", strip=True)


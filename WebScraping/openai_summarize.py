import os, requests
from openai import OpenAI
from dotenv import load_dotenv
from bs4 import BeautifulSoup

#Getting the OpenAI api key from the env file using dotenv's load env method
load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

#Creating an instance of Openai
openai = OpenAI()

headers = {
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

#Using beautiful soup to scrape the website and getting the title adn text from the website
class Website:
    def __init__(self, url):
        self.url = url
        response = requests.get(url,headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        self.text = soup.body.get_text(separator="\n", strip=True)

#Declaring the prompts for the messages
system_prompt = "You are an assistant that analyzes the contents of a website \
and provides a short summary, ignoring text that might be navigation related. \
Respond in markdown."

def user_prompt_for(website):
    user_prompt = f"You are looking at a website titled {website.title}"
    user_prompt += "\nThe contents of this website is as follows; \
please provide a short summary of this website in markdown. \
If it includes news or announcements, then summarize these too.\n\n"
    user_prompt += website.text
    return user_prompt

#Adding the messages together according to the roles
def messages_for(website):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_for(website)}
    ]

def summarize(url):
    website = Website(url)
    response = openai.chat.completions.create(
        model = "gpt-4o-mini",
        messages= messages_for(website)
    )
    return response.choices[0].message.content

def display_summary(url):
    summary = summarize(url)
    print(summary)

if __name__ == "__main__":
    display_summary("https://cnn.com")
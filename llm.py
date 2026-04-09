from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def get_response(prompt):
    response = client.chat.completions.create(
        model="openai/gpt-3.5-turbo",  # free model
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
print("API KEY:", os.getenv("OPENAI_API_KEY"))
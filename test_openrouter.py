import requests
import json
import os
from dotenv import load_dotenv

load_dotenv('/home/system76-01/Desktop/aiis here/backend/.env')
api_key = os.getenv('OPENROUTER_API_KEY')

print(f"Using API Key: {api_key[:10]}...")

try:
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
        },
        data=json.dumps({
            "model": "deepseek/deepseek-r1:free",
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        }),
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

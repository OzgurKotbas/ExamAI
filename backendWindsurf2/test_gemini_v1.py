import asyncio
import httpx
import os
import sys

# Load .env
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

async def test_gemini():
    url = f"https://generativelanguage.googleapis.com/v1/models/{GEMINI_MODEL}:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    data = {
        "contents": [{
            "parts": [{
                "text": "Hello, are you working correctly?"
            }]
        }],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 100
        }
    }
    
    print(f"Testing Gemini API at {url}...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=data, headers=headers)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                print("Gemini API connection successful!")
                print(response.json()["candidates"][0]["content"]["parts"][0]["text"])
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Exception: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_gemini())

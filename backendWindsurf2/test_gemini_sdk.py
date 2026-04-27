import asyncio
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

async def test_sdk():
    print(f"Testing Gemini SDK with model: {GEMINI_MODEL}")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        response = await model.generate_content_async("Hello, are you working correctly?")
        
        print(f"Response received:")
        print(response.text)
        print("\nSuccess! SDK connection is working.")
        
    except Exception as e:
        print(f"Error during SDK test: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_sdk())

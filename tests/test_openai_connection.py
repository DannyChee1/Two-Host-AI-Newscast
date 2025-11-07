"""
Quick test to verify OpenAI API connection with v0.28.1
"""

import os
from dotenv import load_dotenv
import openai

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    print("ERROR: OPENAI_API_KEY not found in .env file")
    exit(1)

print(f"API Key loaded: {api_key[:20]}... (length: {len(api_key)})")
print(f"OpenAI version: {openai.__version__}")

openai.api_key = api_key

print("\nTesting basic API call...")

try:
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Always respond with valid JSON."},
            {"role": "user", "content": 'Please respond with this exact JSON: {"status": "ok", "message": "API is working"}'}
        ],
        temperature=0.3,
        max_tokens=100
    )
    
    print("[OK] API call successful!")
    print(f"Response type: {type(response)}")
    print(f"Response keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}")
    
    content = response['choices'][0]['message']['content']
    print(f"\nReceived content ({len(content)} chars):")
    print(content)
    print("\n[OK] OpenAI API is working correctly!")
    
except openai.error.AuthenticationError:
    print("[FAIL] Authentication failed - check your API key")
except openai.error.RateLimitError:
    print("[FAIL] Rate limit exceeded")
except openai.error.InvalidRequestError as e:
    print(f"[FAIL] Invalid request: {e}")
except Exception as e:
    print(f"[FAIL] Error: {type(e).__name__}: {e}")


from datetime import datetime
from dotenv import load_dotenv

import httpx
import os

load_dotenv()

def generate_batch_id(prefix: str = "batch") -> str:
    now = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]  # Millisecond precision
    return f"{prefix}_{now}"




def get_gemini_response(prompt: str):
    try:
        GEMINI_API_KEY = os.getenv("GEMINI-API-KEY", None)
        headers = {
            "X-goog-api-key": f"{GEMINI_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }

        response = httpx.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            headers=headers,
            json=data,
            timeout=20
        )
        response.raise_for_status()
        return response.json()['candidates'][0]['content']['parts'][0]['text']

    except Exception as e:
        return f"[Gemini error] {str(e)}"
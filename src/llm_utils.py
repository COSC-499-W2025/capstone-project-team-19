import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_summary(prompt: str, model: str = "llama-3.1-8b-instant") -> str:
    """
    Generate a short, clean summary using Groq LLM.
    Returns plain text or a fallback string if the request fails.
    """
    try:
        completion = _client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You write clear, concise professional summaries."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.25,
            max_tokens=300,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[LLM ERROR] Groq summary failed: {e}")
        return "[Summary unavailable due to API error]"

"""test_llm.py - send one message to Gemini and print the reply.

It tries several models in order. If one is busy (503) or not available,
it waits a little and moves on to the next one.

Run with:  python test_llm.py
"""
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("GEMINI_API_KEY not found. Check your .env file.")

# Models from your list_models.py output, best choice first.
MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]

client = genai.Client(api_key=api_key)


def ask(prompt, tries_per_model=2, wait_seconds=5):
    """Send the prompt, trying each model in turn. Returns (model, text)."""
    for model in MODELS:
        for attempt in range(1, tries_per_model + 1):
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                return model, response.text
            except errors.APIError as e:
                print(f"{model} (try {attempt}): error {e.code}")
                if e.code in (429, 500, 503) and attempt < tries_per_model:
                    time.sleep(wait_seconds)  # busy: wait, then retry
                else:
                    break  # not available: move to the next model
    raise SystemExit("All models failed. Wait a few minutes and run again.")


model_used, text = ask("Say hello to Narmadha in one short, friendly sentence.")
print(f"\nModel used: {model_used}")
print(text)

"""llm.py - sends meeting notes to Gemini and gets back validated tasks.

Run a quick test with:  python llm.py
"""
import os
import time
from typing import List, Literal, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

load_dotenv()
_api_key = os.getenv("GEMINI_API_KEY")
if not _api_key:
    raise SystemExit("GEMINI_API_KEY not found. Check your .env file.")

client = genai.Client(api_key=_api_key)

# Tried in this order. If one is busy, we wait and move to the next.
MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
]


# ---- The shape of the answer we want back (the "schema") ----
class TaskOut(BaseModel):
    task: str
    owner: Optional[str] = None
    due: Optional[str] = None
    priority: Literal["low", "medium", "high"] = "medium"


class MeetingOut(BaseModel):
    tasks: List[TaskOut]
    decisions: List[str]
    unclear: List[str]


INSTRUCTIONS = """You extract action items from meeting notes.
Rules:
- Only include tasks that are clearly stated in the notes. Never invent tasks.
- owner: the person responsible, exactly as named. Use null if nobody is named.
- due: the deadline as written in the notes (e.g. "Friday"). Use null if none is given.
- priority: "high" for urgent or blocking work, "low" for nice-to-have, otherwise "medium".
- decisions: things the group decided (not tasks).
- unclear: short notes about missing information, e.g. "No deadline given for the login bug".
"""


def _call_model(notes, tries_per_model=2, wait_seconds=5):
    """Call Gemini, trying each model in turn. Returns the raw JSON text."""
    config = types.GenerateContentConfig(
        system_instruction=INSTRUCTIONS,
        response_mime_type="application/json",
        response_schema=MeetingOut,
        temperature=0,
    )
    for model in MODELS:
        for attempt in range(1, tries_per_model + 1):
            try:
                response = client.models.generate_content(
                    model=model, contents=notes, config=config
                )
                return response.text
            except errors.APIError as e:
                print(f"[llm] {model} (try {attempt}): error {e.code}")
                if e.code in (429, 500, 503) and attempt < tries_per_model:
                    time.sleep(wait_seconds)
                else:
                    break
    raise RuntimeError("All models failed. Wait a few minutes and try again.")


def extract_tasks(notes, max_attempts=3):
    """Turn raw meeting notes into a validated MeetingOut object.

    If the AI returns JSON that does not match our schema, we ask again.
    """
    last_error = None
    for _ in range(max_attempts):
        raw = _call_model(notes)
        try:
            return MeetingOut.model_validate_json(raw)
        except ValidationError as e:
            last_error = e
            print("[llm] Bad JSON from the model, trying again...")
    raise RuntimeError(f"Could not get valid JSON: {last_error}")


if __name__ == "__main__":
    sample = (
        "Weekly review. Ravi will send the report by Friday. "
        "We need to fix the login bug urgently, Priya said she can take it. "
        "Next review is on Monday. Someone should also update the website banner."
    )
    result = extract_tasks(sample)
    print(result.model_dump_json(indent=2))

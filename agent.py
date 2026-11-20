"""agent.py - answers questions about tasks using tool calling.

The AI is given one tool: get_tasks(). When you ask a question, the AI
decides to call that tool, reads the database rows, then writes the answer.

Run a quick test with:  python agent.py
"""
import time
from typing import Optional

from google.genai import errors, types

import db
from llm import MODELS, client


def get_tasks(owner: Optional[str] = None, status: Optional[str] = None) -> list:
    """Look up tasks stored in the database.

    Args:
        owner: Only return tasks for this person (e.g. "Priya"). Leave empty for everyone.
        status: Only return tasks with this status, such as "open". Leave empty for all.

    Returns:
        A list of tasks. Each has: id, meeting_id, task, owner, due, priority, status.
    """
    rows = db.get_tasks()
    if owner:
        rows = [r for r in rows if (r["owner"] or "").lower() == owner.lower()]
    if status:
        rows = [r for r in rows if (r["status"] or "").lower() == status.lower()]
    return rows


SYSTEM = """You answer questions about tasks from meetings.
- Always call get_tasks to look up the data. Never guess.
- If no tasks match, say so plainly.
- Keep answers short and clear. Mention owner, due date and priority when useful."""


def answer_question(question, tries_per_model=2, wait_seconds=5):
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM,
        tools=[get_tasks],  # the SDK calls our function automatically when needed
        temperature=0,
    )
    for model in MODELS:
        for attempt in range(1, tries_per_model + 1):
            try:
                response = client.models.generate_content(
                    model=model, contents=question, config=config
                )
                return response.text
            except errors.APIError as e:
                print(f"[agent] {model} (try {attempt}): error {e.code}")
                if e.code in (429, 500, 503) and attempt < tries_per_model:
                    time.sleep(wait_seconds)
                else:
                    break
    raise RuntimeError("All models failed. Wait a few minutes and try again.")


if __name__ == "__main__":
    print(answer_question("What is Priya working on?"))

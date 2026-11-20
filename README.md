# Meeting Notes to Tasks

An LLM-powered API that turns messy meeting notes into a structured task list, stores it in a database, and answers plain-English questions about the tasks.

Built as a one-day learning project by Narmadha J.

## What it does

1. **Extract:** send raw meeting notes. The model returns validated JSON with tasks (task, owner, due date, priority), decisions, and unclear items.
2. **Store:** tasks are saved in a SQLite database (`meetings` and `tasks` tables).
3. **Ask:** ask questions like "What is Priya working on?". The model calls a `get_tasks` tool, reads the real database rows, and answers from them.

Example input:

> Ravi will send the report by Friday. We need to fix the login bug urgently, Priya said she can take it. Someone should also update the website banner.

Example output (shortened):

```json
{
  "tasks": [
    {"task": "Send the report", "owner": "Ravi", "due": "Friday", "priority": "medium"},
    {"task": "Fix the login bug", "owner": "Priya", "due": null, "priority": "high"},
    {"task": "Update the website banner", "owner": null, "due": null, "priority": "medium"}
  ],
  "unclear": ["No owner or deadline assigned for updating the website banner"]
}
```

## Tech

- Python, FastAPI, Pydantic
- SQLite
- Google Gemini API (`google-genai`) with structured JSON output and tool calling

## How it works

| File | Purpose |
|---|---|
| `main.py` | FastAPI endpoints: `POST /notes`, `POST /ask`, `GET /tasks`, `POST /tasks` |
| `llm.py` | Sends notes to the model, validates the JSON against a Pydantic schema, retries on bad output, falls back across models when one is busy |
| `agent.py` | Question answering with tool calling (`get_tasks` reads the database) |
| `db.py` | SQLite tables and queries |
| `eval.py`, `eval_data.json` | Evaluation script and 20 hand-written test meetings |

## Run it locally

1. Create a free API key in Google AI Studio.
2. Copy `.env.example` to `.env` and put your key in it. Never commit `.env`.
3. Install and run:

```
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

4. Open http://127.0.0.1:8000/docs to try the endpoints.

Run the evaluation with `python eval.py`.

## Evaluation

The test set has 20 hand-written meetings with 26 expected tasks, including hard cases: decisions with no tasks, a dropped plan, a correction ("actually, make that Friday"), a pronoun, two owners sharing a task, and a note written in Tanglish (Tamil and English mixed).

| Metric | Result |
|---|---|
| Expected tasks found | 26 / 26 |
| Owner correct | 26 / 26 |
| Due date correct | 26 / 26 |
| Extra tasks | 1 (a shared task split per person) |

## Limitations

- The test set is small and written by me, so the score shows the basics work, not that it is production-ready.
- Free-tier API limits caused rate-limit and busy-server errors during testing, so the code retries and falls back to other models.
- No user login, and a single SQLite file, so it is a prototype for one user.

## Next steps

- Semantic search over past meetings using embeddings
- Docker and cloud deployment
- A larger and harder test set

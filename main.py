"""main.py - the web API (FastAPI)."""
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import agent
import db
import llm

app = FastAPI(title="Meeting Notes to Tasks")
db.init_db()  # make sure tables exist when the app starts


class TaskIn(BaseModel):
    meeting_title: str
    task: str
    owner: Optional[str] = None
    due: Optional[str] = None
    priority: str = "medium"


class NotesIn(BaseModel):
    title: str
    notes: str


class QuestionIn(BaseModel):
    question: str


@app.get("/")
def home():
    return {"message": "Meeting Notes to Tasks API is running"}


@app.post("/notes")
def create_from_notes(item: NotesIn):
    """Send raw meeting notes. The AI extracts tasks, and we save them."""
    try:
        result = llm.extract_tasks(item.notes)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    meeting_id = db.add_meeting(item.title, item.notes)
    for t in result.tasks:
        db.add_task(
            meeting_id, t.task, owner=t.owner, due=t.due, priority=t.priority
        )
    return {
        "meeting_id": meeting_id,
        "tasks": [t.model_dump() for t in result.tasks],
        "decisions": result.decisions,
        "unclear": result.unclear,
    }


@app.post("/ask")
def ask_question(item: QuestionIn):
    """Ask a question in plain English, e.g. 'What is Priya working on?'"""
    try:
        return {"answer": agent.answer_question(item.question)}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/tasks")
def create_task(item: TaskIn):
    """Add a single task by hand."""
    meeting_id = db.add_meeting(item.meeting_title, raw_notes="(added manually)")
    task_id = db.add_task(
        meeting_id, item.task, owner=item.owner, due=item.due, priority=item.priority
    )
    return {"task_id": task_id, "meeting_id": meeting_id}


@app.get("/tasks")
def list_tasks(owner: Optional[str] = None, status: Optional[str] = None):
    return db.get_tasks(owner=owner, status=status)

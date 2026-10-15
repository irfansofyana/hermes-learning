"""Real Hermes dashboard routes; host auth wraps this namespace.

No package-context singleton is shared with agent plugins. Both adapters resolve
profile storage per request and use the same SQLite service file.
"""
import importlib.util
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("hermes_learning_spike_http_runtime", ROOT / "runtime.py")
if spec is None or spec.loader is None:
    raise RuntimeError("Cannot load the learning spike runtime")
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)
router = APIRouter()


class StartBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(default="Retry and idempotency", min_length=1, max_length=120)


class ContextBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    context_id: str = Field(min_length=1, max_length=64)


class AttemptBody(ContextBody):
    run_id: str = Field(min_length=1, max_length=64)
    answer: str = Field(min_length=1, max_length=8000)


def call(name, body):
    try:
        return runtime.action(name, body)
    except runtime.LearningError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/lesson")
def get_lesson():
    return runtime.lesson()


@router.get("/state")
def get_state():
    return call("state", {})


@router.post("/start")
def start(body: StartBody):
    # Only this human-facing HTTP action and the slash command issue contexts.
    try:
        return runtime.store().start(body.label, origin="workspace_action")
    except runtime.LearningError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/hint")
def hint(body: ContextBody):
    return call("hint", body.model_dump())


@router.post("/attempt")
def attempt(body: AttemptBody):
    return call("attempt", body.model_dump())


@router.post("/leave")
def leave(body: ContextBody):
    return call("leave", body.model_dump())


@router.post("/runs")
def runs(body: ContextBody):
    return call("runs", body.model_dump())

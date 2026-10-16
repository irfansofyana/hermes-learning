"""Human workspace API mounted beneath the host's authenticated plugin namespace."""
import importlib.util
from pathlib import Path
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hermes_learning_http_runtime', ROOT / 'runtime.py')
if spec is None or spec.loader is None:
    raise RuntimeError('Cannot load learning runtime')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)
router = APIRouter()

# Config works in Pydantic v1 and v2; no coercion of API version or action.
class ActionBody(BaseModel):
    action: StrictStr = Field(min_length=1, max_length=40)
    params: dict[str, Any]
    api_version: StrictInt

    if hasattr(BaseModel, 'model_validate'):
        model_config = ConfigDict(extra='forbid')
    else:
        class Config:
            extra = 'forbid'


def call(name, params, api_version=1):
    try:
        return runtime.action(name, params, channel='ui_direct', api_version=api_version)
    except runtime.LearningError as exc:
        raise HTTPException(status_code=getattr(exc, 'status', 409), detail=str(exc)) from exc


@router.get('/state')
def get_state():
    return call('state', {})


@router.get('/track/{track_id}')
def get_track(track_id: str):
    return call('track', {'track_id': track_id})


@router.get('/activity/{activity_id}')
def get_activity(activity_id: str, context_id: str | None = None):
    params = {'activity_id': activity_id}
    if context_id:
        params['context_id'] = context_id
    return call('activity_read', params)


@router.get('/source/{source_id}')
def get_source(source_id: str):
    return call('source_read', {'source_id': source_id})


@router.get('/export')
def get_export():
    return call('export', {})


@router.post('/action')
def post_action(body: ActionBody):
    return call(body.action, body.params, body.api_version)

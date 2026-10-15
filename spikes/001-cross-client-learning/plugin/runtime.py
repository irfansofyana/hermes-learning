"""Stateless host adapter. Resolve active-profile storage on every operation."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("hermes_learning_spike_store", ROOT / "learning_store.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError("Cannot load the learning spike service")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
Store, LearningError = _module.Store, _module.LearningError


def store():
    from plugins.plugin_storage import plugin_data_dir
    return Store(plugin_data_dir("hermes-learning-spike") / "data.db")


def lesson():
    return json.loads((ROOT / "lesson.json").read_text())


def action(name, params):
    service = store()
    context = params.get("context_id", "")
    if name == "state":
        return service.state()
    if name == "hint":
        return service.hint(context)
    if name == "attempt":
        return service.submit(context, params.get("run_id", ""), params.get("answer", ""))
    if name == "leave":
        return service.leave(context)
    if name == "runs":
        return service.new_run(context)
    raise LearningError("Unknown action")

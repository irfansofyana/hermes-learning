"""Hermes Learning disposable plugin. No model-facing start/enroll tool."""
import json
from pathlib import Path
from . import runtime


def command(raw_args):
    args = raw_args.strip().split(maxsplit=1)
    if not args:
        return "Use /learning-spike start <label>, status, or leave <context-id>. This spike saves learning records only after explicit start."
    try:
        if args[0] == "start":
            return json.dumps(runtime.store().start(args[1] if len(args) > 1 else "Retry lesson", origin="slash_command"))
        if args[0] == "status":
            return json.dumps(runtime.store().state())
        if args[0] == "leave" and len(args) > 1:
            return json.dumps(runtime.action("leave", {"context_id": args[1]}))
        return "Unknown action. Use start, status, or leave."
    except runtime.LearningError as exc:
        return json.dumps({"error": str(exc)})


def register(ctx):
    ctx.register_command("learning-spike", command,
                         "Explicitly start/status/leave tracked spike learning.", args_hint="<start|status|leave> [label or context-id]")
    root = Path(__file__).parent
    ctx.register_skill("teach", root / "skills/teach/SKILL.md", "Teach the spike without filler; preserve ad hoc/tracked boundaries.")
    ctx.register_skill("humanizer", root / "skills/humanizer/SKILL.md", "Humanizer-compatible teaching adaptation: direct prose with technical fidelity.")
    definitions = [
        ("learning_spike_status", "Read saved spike state only when the learner asks to inspect or resume it.", "state", {}),
        ("learning_spike_lesson", "Read the authored example lesson without starting tracking or writing learning records.", "lesson", {}),
        ("learning_spike_hint", "Record and return a hint for an explicitly started context.", "hint", {"context_id": {"type": "string"}}),
        ("learning_spike_submit", "Submit the learner's verbatim answer to the current explicit practice run; retries reuse its server-issued ID.", "attempt", {"context_id": {"type": "string"}, "run_id": {"type": "string"}, "answer": {"type": "string"}}),
        ("learning_spike_leave", "Leave the specified tracked context when the learner asks; do not delete saved records.", "leave", {"context_id": {"type": "string"}}),
    ]
    for name, description, action_name, properties in definitions:
        def handler(params, _action=action_name, **kwargs):
            del kwargs
            try:
                value = runtime.lesson() if _action == "lesson" else runtime.action(_action, params)
                return json.dumps(value)
            except runtime.LearningError as exc:
                return json.dumps({"error": str(exc)})
        schema = {"name": name, "description": description, "parameters": {
            "type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}}
        ctx.register_tool(name=name, toolset="learning_spike", schema=schema, handler=handler)

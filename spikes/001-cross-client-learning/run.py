"""Run the real Hermes plugin in an isolated local home. No daily-home installs.

Usage: python run.py prepare | serve | tool NAME JSON | command TEXT
All subprocesses use a fresh HOME as well as HERMES_HOME: redirecting only the
latter under ~/.hermes would still discover machine-level daily plugins.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PLUGIN_ID = "hermes-learning-spike"


def isolated_environment(root, source):
    root = root.resolve()
    marker = root / ".learning-spike-owned"
    if root.exists() and any(root.iterdir()) and not marker.exists():
        raise SystemExit("Refusing a nonempty directory not owned by this spike.")
    for name in ("os-home", "hermes-home", "tmp"):
        (root / name).mkdir(parents=True, exist_ok=True)
    marker.touch(exist_ok=True)
    token_path = root / "session-token"
    if not token_path.exists():
        token_path.write_text(secrets.token_urlsafe(32))
        token_path.chmod(0o600)
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(root / "os-home"),
        "HERMES_HOME": str(root / "hermes-home"),
        "TMPDIR": str(root / "tmp"),
        "PYTHONPATH": str(source),
        "PYTHONDONTWRITEBYTECODE": "1",
        "HERMES_DISABLE_LAZY_INSTALLS": "1",
        "HERMES_WEB_DIST": str(source / "hermes_cli/web_dist"),
        "HERMES_DASHBOARD_SESSION_TOKEN": token_path.read_text(),
    }


def worker(action, args):
    from hermes_constants import get_hermes_home, get_default_hermes_root
    expected = Path(os.environ["HERMES_HOME"]).resolve()
    assert get_hermes_home().resolve() == expected
    assert get_default_hermes_root().resolve() == expected, "Isolation failed: machine root differs."
    if action == "configure":
        from hermes_cli.config import set_config_value
        set_config_value("plugins.enabled", json.dumps([PLUGIN_ID]))
        set_config_value("plugins.disabled", "[]")
        set_config_value("plugins.isolation", "in_process")
        set_config_value("security.allow_lazy_installs", "false")
        print("Configured isolated Hermes home; daily HOME is not inherited.")
        return
    from hermes_cli.plugins import discover_plugins, get_plugin_manager
    discover_plugins()
    pm = get_plugin_manager()
    if action == "serve":
        from hermes_cli.web_server import start_server
        start_server(host="127.0.0.1", port=int(args[0]), open_browser=False, isolated=True)
    elif action == "tool":
        from tools.registry import registry
        print(registry.dispatch(args[0], json.loads(args[1]), scope=pm.scope_key))
    elif action == "command":
        # Exercise the actual registered command handler, never a model enrollment tool.
        command = pm._plugin_commands.get("learning-spike")
        if not command:
            raise RuntimeError("Learning command was not registered")
        print(command["handler"](args[0]))
    elif action == "inspect":
        skills = pm.list_plugin_skills(PLUGIN_ID)
        from tools.skills_tool import skill_view
        readable = {}
        for name in skills:
            result = json.loads(skill_view(f"{PLUGIN_ID}:{name}", preprocess=False))
            readable[name] = bool(result.get("success") and result.get("content"))
        print(json.dumps({"plugins": [p for p in pm.list_plugins() if p["name"] == PLUGIN_ID],
                          "skills": skills, "skills_readable": readable}, default=str))
    else:
        raise ValueError("Unknown worker action")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "_worker":
        return worker(sys.argv[2], sys.argv[3:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "serve", "tool", "command", "inspect"])
    parser.add_argument("arguments", nargs="*")
    parser.add_argument("--home", type=Path, default=Path(os.environ.get("TMPDIR", str(Path.home() / ".hermes/cache/scratch"))) / "hermes-learning-spike-runtime")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--port", type=int, default=0)
    options = parser.parse_args()
    source = options.source
    if source is None:
        spec = importlib.util.find_spec("hermes_constants")
        if spec is None or not spec.origin:
            raise SystemExit("Pass --source /path/to/hermes-agent and use its Python environment.")
        source = Path(spec.origin).resolve().parent
    source = source.resolve()
    if not (source / "hermes_cli/web_dist/index.html").is_file():
        raise SystemExit("The existing Hermes dashboard build is missing; no installation/build will be attempted.")
    env = isolated_environment(options.home, source)
    cmd = [sys.executable, "-B", str(Path(__file__).resolve()), "_worker"]
    if options.action == "prepare":
        target = Path(env["HERMES_HOME"]) / "plugins" / PLUGIN_ID
        shutil.copytree(HERE / "plugin", target, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        subprocess.run(cmd + ["configure"], env=env, check=True, cwd=env["HOME"])
        print("Isolated plugin staged at", target)
    elif options.action == "serve":
        if not (Path(env["HERMES_HOME"]) / "plugins" / PLUGIN_ID).is_dir():
            raise SystemExit("Run prepare first.")
        os.chdir(env["HOME"])
        os.execve(sys.executable, cmd + ["serve", str(options.port)], env)
    else:
        expected = {"tool": 2, "command": 1, "inspect": 0}[options.action]
        if len(options.arguments) != expected:
            parser.error(f"{options.action} expects {expected} arguments")
        subprocess.run(cmd + [options.action] + options.arguments, env=env, check=True, cwd=env["HOME"])


if __name__ == "__main__":
    main()

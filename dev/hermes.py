"""Run the real Hermes plugin in an isolated local home. No daily-home installs.

Usage: python dev/hermes.py prepare | serve | tool NAME JSON | command TEXT
All subprocesses use a fresh HOME as well as HERMES_HOME: redirecting only the
latter under ~/.hermes would still discover machine-level daily plugins.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

HERE = Path(__file__).resolve().parents[1]
PLUGIN_ID = "hermes-learning"


def isolated_environment(root, source):
    root = root.resolve()
    marker = root / ".learning-host-owned"
    if root.exists() and any(root.iterdir()) and not marker.exists():
        raise SystemExit("Refusing a nonempty directory not owned by this learning runner.")
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
    elif action == "inspect":
        skills = pm.list_plugin_skills(PLUGIN_ID)
        from tools.skills_tool import skill_view
        readable = {}
        for name in skills:
            result = json.loads(skill_view(f"{PLUGIN_ID}:{name}", preprocess=False))
            readable[name] = bool(result.get("success") and result.get("content"))
        print(json.dumps({"plugins": [p for p in pm.list_plugins() if p["name"] == PLUGIN_ID],
                          "skills": skills, "skills_readable": readable, "commands": list(pm._plugin_commands)}, default=str))
    else:
        raise ValueError("Unknown worker action")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "_worker":
        return worker(sys.argv[2], sys.argv[3:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "serve", "tool", "inspect"])
    parser.add_argument("arguments", nargs="*")
    parser.add_argument("--home", type=Path, default=Path("/tmp/hermes-learning-runtime"))
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
    python = next((candidate for candidate in (source / '.venv/bin/python', source / 'venv/bin/python') if candidate.is_file()), None)
    if python is None:
        raise SystemExit('The host Python environment is missing; no installation will be attempted.')
    cmd = [str(python), "-B", str(Path(__file__).resolve()), "_worker"]
    if options.action == "prepare":
        target = Path(env["HERMES_HOME"]) / "plugins" / PLUGIN_ID
        # Stage only release artifacts, never this repository's .git, tests or data.
        from package import collect
        for relative, content in collect(HERE).items():
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        subprocess.run(cmd + ["configure"], env=env, check=True, cwd=env["HOME"])
        print("Isolated plugin staged at", target)
    elif options.action == "serve":
        if not (Path(env["HERMES_HOME"]) / "plugins" / PLUGIN_ID).is_dir():
            raise SystemExit("Run prepare first.")
        os.chdir(env["HOME"])
        os.execve(str(python), cmd + ["serve", str(options.port)], env)
    else:
        expected = {"tool": 2, "inspect": 0}[options.action]
        if len(options.arguments) != expected:
            parser.error(f"{options.action} expects {expected} arguments")
        subprocess.run(cmd + [options.action] + options.arguments, env=env, check=True, cwd=env["HOME"])


if __name__ == "__main__":
    main()

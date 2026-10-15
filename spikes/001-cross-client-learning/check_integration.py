"""Small real-host integration check. Run after run.py prepare + serve.

Uses an isolated-home session token without printing it. Exercises the actual
Hermes registry in separate subprocesses and actual authenticated HTTP routes.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from urllib.error import HTTPError

HERE = Path(__file__).resolve().parent
PREFIX = "/api/plugins/hermes-learning-spike"


def url_origin(url):
    if any(ord(char) <= 32 or ord(char) == 127 for char in url):
        raise ValueError("URL contains whitespace or control characters.")
    parsed = urlsplit(url)
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL credentials are not allowed.")
    port = parsed.port
    return parsed.scheme, parsed.hostname, port if port is not None else (80 if parsed.scheme == "http" else 443)


def loopback_url(url):
    origin = url_origin(url)
    parsed = urlsplit(url)
    if (origin[:2] != ("http", "127.0.0.1") or parsed.port is None or parsed.port < 1 or
            parsed.path not in {"", "/"} or parsed.query or parsed.fragment):
        raise ValueError("Expected an HTTP loopback origin with an explicit port.")
    return f"http://127.0.0.1:{parsed.port}"


class SameOriginRedirects(HTTPRedirectHandler):
    def __init__(self, base_url):
        self.origin = url_origin(base_url)

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        try:
            if url_origin(newurl) != self.origin:
                raise ValueError("Refusing an off-origin redirect.")
        except ValueError:
            fp.close()
            raise
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    try:
        base_url = loopback_url(args.url)
    except ValueError:
        parser.error("This check is restricted to an isolated loopback server.")
    # Never route the isolated session token through environment proxies.
    opener = build_opener(ProxyHandler({}), SameOriginRedirects(base_url))
    token = (args.home / "session-token").read_text()

    def request(path, body=None, auth=True):
        headers = {"Content-Type": "application/json"}
        if auth:
            headers["X-Hermes-Session-Token"] = token
        req = Request(base_url + path, headers=headers,
                      data=None if body is None else json.dumps(body).encode())
        try:
            with opener.open(req, timeout=15) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            with error:
                return error.code, json.loads(error.read())

    def worker(action, *extra):
        result = subprocess.run([sys.executable, str(HERE / "run.py"), "--home", str(args.home),
                                 "--source", str(args.source), action, *extra],
                                text=True, capture_output=True, check=True)
        return json.loads(result.stdout.strip().splitlines()[-1])

    checks = []
    assert request(PREFIX + "/state", auth=False)[0] == 401
    assert request(PREFIX + "/start", {"label": "unauthenticated"}, auth=False)[0] == 401
    checks.append("host authentication rejects unauthenticated GET/POST")
    code, state = request(PREFIX + "/state")
    assert code == 200
    baseline = len(state["contexts"]), len(state["attempts"])
    assert request(PREFIX + "/hint", {"context_id": "not-approved"})[0] == 409
    negative = worker("tool", "learning_spike_hint", json.dumps({"context_id": "not-approved"}))
    assert "error" in negative
    assert request(PREFIX + "/state")[1]["contexts"] == state["contexts"]
    checks.append("HTTP and real registry reject context-free writes")
    lesson = worker("tool", "learning_spike_lesson", "{}")
    assert lesson["schema_version"] == 1 and "criteria" not in lesson
    checks.append("real tool returns authored lesson without enrollment or solution key")
    context = worker("command", "start integration-check")
    assert context["origin"] == "slash_command"
    assert request(PREFIX + "/state")[1]["contexts"][-1]["id"] == context["id"]
    checks.append("registered slash command and HTTP share the same store")
    hint = worker("tool", "learning_spike_hint", json.dumps({"context_id": context["id"]}))
    assert "hint" in hint
    payload = {"context_id": context["id"], "run_id": context["run_id"],
               "answer": "Integration fixture: a retry may repeat the committed effect; timeout does not imply rollback."}
    code, result = request(PREFIX + "/attempt", payload)
    assert code == 200 and result["attempt"]["assistance"] == "targeted_hint"
    assert result["attempt"]["status"] == "awaiting_assessment"
    checks.append("tool hint survives HTTP answer submission; assessment remains pending")
    retry = worker("tool", "learning_spike_submit", json.dumps(payload))
    assert retry["duplicate"] and retry["attempt"]["id"] == result["attempt"]["id"]
    changed = dict(payload, answer="different payload")
    assert request(PREFIX + "/attempt", changed)[0] == 409
    checks.append("cross-adapter retry returns same attempt and changed payload conflicts")
    new = request(PREFIX + "/runs", {"context_id": context["id"]})[1]
    second = request(PREFIX + "/attempt", dict(payload, run_id=new["run_id"]))[1]
    assert second["attempt"]["id"] != result["attempt"]["id"]
    checks.append("new server-issued run permits intentional identical answers")
    assert request(PREFIX + "/leave", {"context_id": context["id"]})[0] == 200
    assert "error" in worker("tool", "learning_spike_submit", json.dumps(payload))
    final = request(PREFIX + "/state")[1]
    assert len(final["contexts"]) == baseline[0] + 1
    assert len(final["attempts"]) == baseline[1] + 2
    assert final["store_id"] == worker("tool", "learning_spike_status", "{}")["store_id"]
    checks.append("exit revokes later tool writes without deleting committed attempts")
    inventory = worker("inspect")
    plugin = next(p for p in inventory["plugins"] if p["name"] == "hermes-learning-spike")
    assert plugin["enabled"] and not plugin["error"] and plugin["tools"] == 5
    assert set(inventory["skills"]) == {"teach", "humanizer"}
    checks.append("real loader registers five tools, a command, and bundled teach/humanizer skills")
    code, plugins = request("/api/dashboard/plugins")
    assert code == 200 and "hermes-learning-spike" in json.dumps(plugins)
    checks.append("real dashboard discovers the frontend plugin")
    print(json.dumps({"passed": len(checks), "checks": checks, "store_id": final["store_id"],
                      "attempts_in_store": len(final["attempts"])}, indent=2))


if __name__ == "__main__":
    main()

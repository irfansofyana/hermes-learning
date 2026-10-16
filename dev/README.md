# Isolated learning workspace preview

This preview serves the shared UI against the actual learning store, using a Python standard-library HTTP adapter. It does not load Hermes, install the plugin, restart the daily instance, or prove compatibility with the real dashboard, Electron client, or messaging channels.

From the repository root, build the shared UI and run:

```sh
cd ui
npm install
npm run build
cd ..
python3 -B dev/serve.py --port 8877 --data-dir /tmp/hermes-learning-preview
```

Open <http://127.0.0.1:8877/>. The workspace starts empty. Use its explicit creation and authoring actions to add learning records. No demo content is automatically inserted.

Omit `--data-dir` to create a new temporary directory on each launch. The directory is printed at startup and retained after shutdown, so it can be reopened with `--data-dir`. Explicit data directories must be outside the repository and `~/.hermes`. Preview data uses `learning.sqlite3` and never uses Hermes profile-path discovery. Stop the server with Ctrl+C.

The server binds only to `127.0.0.1`. Visiting the home page establishes an HttpOnly, SameSite=Strict cookie. API reads require that cookie; writes also require an exact same-origin `Origin` header, JSON content type, and the versioned action envelope. Host validation and fetch-site checks reject cross-site requests. No CORS access is enabled. Restarting the server rotates its session token; reload the home page afterward.

API base: `/api/plugins/hermes-learning`. Supported reads are `/state`, `/track/{id}`, `/activity/{id}?context_id=...`, `/source/{id}`, and `/export`. Writes use `POST /action` with `{ "action": "...", "params": {}, "api_version": 1 }`. The adapter restricts actions to the explicit UI workflow and dispatches them as `ui_direct`.

Run focused HTTP verification:

```sh
python3 -B -W error::ResourceWarning -m unittest discover -s tests -p test_preview.py -v
```

These tests bind ephemeral loopback ports. A sandbox that prohibits socket creation must allow loopback execution for this command. Tests cover session authentication, origin/Host checks, the action envelope, read routing, and static path restrictions; they use a fake dispatcher to isolate the HTTP boundary. Store and real host integration have separate tests and verification requirements.

## Learning-loop checks

Run `python3 -B dev/evaluate.py` for deterministic tool/record scenarios. Live-model cases and their limits are documented in [the evaluation guide](../docs/evaluations/tutoring.md).

`dev/check-workspace.mjs` exercises the built workspace in a browser, including linked example activities, hint/answer/feedback, objective progress, source import, draft recovery and isolation across activity switches, visuals, and mobile dark layout. Start a preview with a **fresh empty data directory** first: this check explicitly creates synthetic learning records and refuses a store containing tracks. It needs an existing Playwright installation; none is bundled with the plugin.

```sh
LEARNING_PREVIEW_URL=http://127.0.0.1:8882 \
PLAYWRIGHT_MODULE=/absolute/path/to/playwright/index.mjs \
CHROME_PATH=/path/to/google-chrome \
node dev/check-workspace.mjs
```

Omit `PLAYWRIGHT_MODULE` to resolve `playwright` normally and `CHROME_PATH` to use Playwright's installed Chromium. Screenshots go to `/tmp/hermes-learning-ui-check`, overridable with `LEARNING_SCREENSHOT_DIR`. Restricted containers may require loopback/browser permission; `LEARNING_BROWSER_NO_SANDBOX=1` is an explicit opt-in for disposable test containers that cannot use Chromium's sandbox.

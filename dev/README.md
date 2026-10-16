# Development guide

Use Node.js 22+ and Python 3.11+. The plugin backend uses Hermes’s FastAPI/Pydantic runtime.

## Local preview

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

## Repository installation check

The repository root is the installable package. `npm --prefix ui run build` writes the committed host bundles to `dashboard/dist/index.js` and `desktop/plugin.js`; `dev/package.py` and the isolated host runner use an explicit release-file list from that root.

With an existing Hermes checkout, run its actual Desktop installer discovery against this checkout:

```sh
node dev/check-install.mjs /path/to/hermes-agent
```

Append `https://github.com/irfansofyana/hermes-learning` to also clone and probe the published repository, then install its desktop component into a temporary directory. This checks that the remote bundle matches the local build. All temporary files are removed afterward; no daily Hermes profile or desktop installation is touched. Run this after publishing layout or bundle changes.

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

## Host bundles and isolated setup

Build output:

| Surface | Artifact | Runtime |
| --- | --- | --- |
| Backend + web | Root Python modules and `dashboard/` | Hermes backend plugin manager and dashboard |
| Desktop | `desktop/plugin.js` | Hermes native disk-plugin loader and `@hermes/plugin-sdk` |
| Development preview | `ui/dist/` | Local isolated preview server |

The web bundle uses the host's `__HERMES_PLUGIN_SDK__.React` and authenticated `fetchJSON`. Desktop imports the host's React and SDK and uses `ctx.rest`. Neither ships a second React runtime into Hermes. Both are built from `ui/src/`; do not edit generated bundles by hand.

## Check the real host in isolation

Use an existing Hermes checkout and its Python environment. These commands stage a copy into a fresh owned directory, not your daily Hermes profile:

```sh
/path/to/hermes-agent/.venv/bin/python -B dev/hermes.py prepare --source /path/to/hermes-agent --home /tmp/hermes-learning-host
/path/to/hermes-agent/.venv/bin/python -B dev/hermes.py inspect --source /path/to/hermes-agent --home /tmp/hermes-learning-host
/path/to/hermes-agent/.venv/bin/python -B dev/hermes.py serve --source /path/to/hermes-agent --home /tmp/hermes-learning-host --port 8878
```

The dashboard tab is `/learning`; the plugin ID is `hermes-learning`. The command is `/learning-track`, because `/learning` is already a built-in command in the tested host. Remote desktop needs both the installed frontend and the compatible plugin on its connected backend/profile. Backend installation alone is not proof that a remote desktop frontend is installed.

For native disk distribution, the loader expects `<local HERMES_HOME>/desktop-plugins/hermes-learning/plugin.js`. The tested unified plugin installer also discovers a package's `desktop/plugin.js` and copies it into the local desktop-plugin directory. Enablement is exposed under **Capabilities → Plugins → Desktop** in the tested desktop build. Follow your host's plugin installation workflow; no daily installation or restart was performed by this change.


## Test suite

Run the backend suite with the same Python environment that supplies Hermes's FastAPI dependencies. Preview HTTP tests need loopback socket permission.

```sh
/path/to/hermes-agent/.venv/bin/python -B -W error::ResourceWarning -m unittest discover -s tests -v
npm --prefix ui test
npm --prefix ui run build
python3 -B dev/evaluate.py
/path/to/hermes-agent/.venv/bin/python -B -W error::ResourceWarning -m unittest discover -s spikes/001-cross-client-learning/tests -v
node spikes/001-cross-client-learning/tests/check_recovery.cjs
```

The service tests cover consent/revocation, cross-track references, source policy, version/key gating, retries, assistance, corrections, objective evidence, fixed-clock scheduling, concurrent startup, and backup restoration. The deterministic evaluation checks complete tool flows; it does not evaluate a model's teaching. See the [tutoring evaluation guide](../docs/evaluations/tutoring.md) and [compatibility](../docs/compatibility.md) for observed results and runtime boundaries.

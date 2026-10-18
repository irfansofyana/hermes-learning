# Development guide

Use Node.js 22+ and Python 3.11+. The backend uses Hermes's FastAPI/Pydantic runtime. Work against disposable stores and isolated Hermes homes; local preview and verification do not require installing into or restarting a daily profile.

## Local preview

The preview serves the shared UI against the real Learning store through a Python standard-library HTTP adapter. Its tutor transport is deliberately simulated and visibly labelled. Generate creates synthetic outline/lesson content through the real course actions; chat replies are deterministic. Explicit rewrite, roadmap, extension and regeneration requests create synthetic proposals through `course_propose`; **Apply changes** and dismiss exercise the real human-only actions. Proposal content is simulated, not a model-quality result. No model call, repository fetch, or real Hermes session occurs.

```sh
npm --prefix ui install
npm --prefix ui run build
python3 -B dev/serve.py --port 8877 --data-dir /tmp/hermes-learning-preview
```

Open [the local preview](http://127.0.0.1:8877/), enter a topic, and choose **Generate learning path**. A fresh store starts empty; loading the page does not insert examples. Production Desktop and dashboard entrypoints never import the simulated tutor transport.

Omit `--data-dir` for a fresh temporary directory on each launch. The server prints the directory and retains it after shutdown, so it can be reopened later with `--data-dir`. Explicit directories must be outside this repository and `~/.hermes`; preview storage never uses Hermes profile-path discovery. Stop with Ctrl+C.

The server binds only to `127.0.0.1`. Visiting its home page establishes an HttpOnly, SameSite=Strict cookie. API reads require that cookie; writes also require an exact same-origin `Origin` header, JSON content type, and a versioned action envelope. Host/fetch-site validation rejects cross-site requests, and CORS is not enabled. Restart rotates the session token; reload the home page afterward.

The API base is `/api/plugins/hermes-learning`. Reads include `/state`, `/track/{id}`, `/activity/{id}?context_id=...`, `/source/{id}`, and `/export`. Actions use `POST /action` with `{ "api_version": 1, "action": "...", "params": {} }`. Course reads also use the `course_read` action. The preview allowlist includes course publication actions so the simulated transport can exercise persistence; this is not evidence of model authorization in a real host.

## Browser checks

`dev/check-navigation.mjs` holds a simulated lesson publication while browsing saved lessons, future lesson goals, home, and another path. It verifies only one generation starts, the tutor remains attached, background completion stays with its own path, and reading position is preserved, including mobile navigation. Use the browser environment variables below and a disposable preview store.

`dev/check-selection.mjs` runs against the labelled disposable preview using the same browser environment variables below. It applies Desktop’s body-level selection restriction and verifies actual mouse drag selection plus native clipboard copying for lesson titles/text/code, both chat roles, thinking, and source text. It makes no model calls.

`dev/check-integrated.mjs` exercises the current primary interface: multiple files and an unsupported PDF, an unread link, first-lesson generation, inline chat, next-lesson generation, read markers, reload/Continue with history, tutor visibility, and mobile dark-mode draft preservation. It checks console/page errors and horizontal overflow and captures screenshots outside the repository.

The integrated check also returns to the saved-path list during generation, verifies the saved title and original-request description, and checks title persistence after reload. The preview supplies the fixed title “Queue Fundamentals”; it verifies persistence and rendering, not AI naming quality. Real model generation supplies `path_title` with the outline, or with the next lesson for an older unnamed path. Titles are at most 100 characters and generated once per path; opening an older path alone does not start a naming call or rewrite its saved name.

Start an isolated preview first. The check creates a new path in its store, so use disposable test data. Bring an existing Playwright installation; none is bundled with the plugin.

```sh
LEARNING_PREVIEW_URL=http://127.0.0.1:8877 \
PLAYWRIGHT_MODULE=/absolute/path/to/playwright/index.mjs \
CHROME_PATH=/path/to/google-chrome \
node dev/check-integrated.mjs
```

Omit `PLAYWRIGHT_MODULE` to resolve `playwright` normally and `CHROME_PATH` to use Playwright's installed Chromium. Screenshots default to `/tmp/hermes-learning-integrated-check`; override with `LEARNING_SCREENSHOT_DIR`. Restricted environments may need loopback/browser permission. `LEARNING_BROWSER_NO_SANDBOX=1` is an explicit opt-in for disposable containers that cannot use Chromium's sandbox.


## Course update checks

Use a disposable preview store to exercise lesson rewrites and roadmap changes (`revise`), added lessons (`extend`), and replacement paths (`regenerate`). Check the proposal summary, roadmap differences, lesson content and read-progress impact before applying. Dismiss a proposal, reload with another pending proposal, and attempt to apply one whose base revision is stale. Failure must leave current content unchanged. Confirm that unchanged rich lessons and their read markers survive revision/extension, modified lessons become unread, regeneration resets position/progress, and sources plus the tutor binding survive every mode.

Generation must finish or stop before proposal/apply. Also check a failed generation, then a requested edit, and confirm that retrying publication from an older completed job cannot restore obsolete lessons. Ordinary explanation/example questions must not create proposals. Use model `learning_course_propose` only for preparing changes and UI-only `course_apply`/`course_dismiss` for decisions. The model has no apply tool.

Repeat the relevant flow against actual isolated Hermes and Desktop with the configured model, including reload and failed/stale operations, before claiming live-host update support. Do not use the learner's live courses as fixtures. Record observed results and boundaries in [compatibility](../docs/compatibility.md); the preview, unit tests and production build establish separate evidence.

## Host bundles

| Surface | Artifact | Runtime |
| --- | --- | --- |
| Backend + dashboard | Root Python modules and `dashboard/dist/index.js` | Hermes backend plugin manager and dashboard SDK |
| Desktop | `desktop/plugin.js` | Native disk-plugin loader and `@hermes/plugin-sdk` |
| Development preview | `ui/dist/` | Isolated local server and explicitly simulated tutor |

Build from `ui/src/` with `npm --prefix ui run build`; do not edit generated bundles by hand. The two host bundles are committed at the repository root's public package locations.

Both host bundles use the host's React runtime. The dashboard uses authenticated `fetchJSON` for Learning actions and `buildWsUrl('/api/ws')` for the tutor gateway. Desktop uses `ctx.rest` for Learning actions and public host requests/events for the tutor. Shared session logic is in `tutor-session.mjs`, adapters in `tutor-transport.mjs`, and React binding in `useTutor.jsx`.

## Isolated host checks

Use an existing Hermes checkout and its Python environment:

```sh
/path/to/hermes-agent/.venv/bin/python -B dev/hermes.py prepare --source /path/to/hermes-agent --home /tmp/hermes-learning-host
/path/to/hermes-agent/.venv/bin/python -B dev/hermes.py inspect --source /path/to/hermes-agent --home /tmp/hermes-learning-host
/path/to/hermes-agent/.venv/bin/python -B dev/hermes.py serve --source /path/to/hermes-agent --home /tmp/hermes-learning-host --port 8878
```

These commands stage a copy in a fresh owned home. The dashboard tab is `/learning` and the plugin ID is `hermes-learning`. The workspace is the only learning entrypoint; the retired tracked-chat command is no longer registered.

A remote Desktop frontend needs both its local frontend installation and the compatible agent component on the connected backend/profile. Backend installation alone does not install the native frontend. The native loader expects `<local HERMES_HOME>/desktop-plugins/hermes-learning/plugin.js`; the tested unified installer discovers `desktop/plugin.js` and copies it there. Enablement is under **Capabilities → Plugins → Desktop** in the tested host.

Real gateway/model verification must exercise session creation, publication through Learning tools, inline replies, restoration, and interruption against an isolated host. Source inspection, simulated responses, and a production build cannot establish those runtime claims. Record exact tested surfaces and limitations in [compatibility](../docs/compatibility.md).

## Repository installation check

The repository root is the installable package. `dev/package.py` and the isolated runner use an explicit release-file list from that root.

```sh
node dev/check-install.mjs /path/to/hermes-agent
```

Append `https://github.com/irfansofyana/hermes-learning` to clone and probe the published repository and install its Desktop component into a temporary directory. This also checks whether the remote bundle matches the local build. Temporary files are removed afterward; the daily profile is untouched. Run it after publishing package-layout or bundle changes.

## Test suite

Use the Python environment that provides Hermes's FastAPI dependencies. HTTP tests bind ephemeral loopback ports and need socket permission.

```sh
/path/to/hermes-agent/.venv/bin/python -B -W error::ResourceWarning -m unittest discover -s tests -v
npm --prefix ui test
npm --prefix ui run build
python3 -B dev/evaluate.py
/path/to/hermes-agent/.venv/bin/python -B -W error::ResourceWarning -m unittest discover -s spikes/001-cross-client-learning/tests -v
node spikes/001-cross-client-learning/tests/check_recovery.cjs
```

Backend tests cover course revisions, proposal authorization/idempotency and stale application, course job authorization/idempotency, publication and source boundaries, legacy evidence, context revocation, concurrent startup, and restoration. UI unit tests cover input limits, inert Markdown rendering, host transport lifecycle, session identity/history, permission handling, interruption, and uncertain delivery without replay. Preview HTTP tests cover authentication, origin/Host checks, action envelopes, routes, and static path restrictions.

`dev/evaluate.py` checks deterministic tool/record scenarios, not teaching quality. Live-model evaluation and its limits are documented in [the evaluation guide](../docs/evaluations/tutoring.md). Keep simulated UI checks, real-host integration, and model-quality evidence distinct when reporting results.

`dev/lesson_quality.py fingerprint` prints hashes of current authoring guidance and the fixed lesson cases. Its `compare` command prepares blinded review sheets from saved baseline/candidate lessons; it makes no model calls. See the [lesson quality benchmark](../docs/evaluations/lesson-quality/README.md) for capture format, repeatable source fixtures, human rubric and limitations. Keep capture files and reviewer keys outside the repository.

## Rich lesson rendering checks

With a fresh empty local preview store, run `dev/check-rendering.mjs` using the same `LEARNING_PREVIEW_URL`, `PLAYWRIGHT_MODULE`, `CHROME_PATH`, and optional sandbox settings as the integration check. It refuses nonempty stores and requires the simulated-preview label. It creates three synthetic lessons to verify highlighted code and clipboard text, GFM content and footnote return links, all visual types and keyboard stepping, and light desktop/dark mobile layouts. Screenshots default to `/tmp/hermes-learning-rendering-check`; override with `LEARNING_SCREENSHOT_DIR`. No model runs or real-host data changes are involved.

Production UI bundles include pinned Markdown and syntax-highlighting dependencies. `npm --prefix ui run build` regenerates `THIRD_PARTY_NOTICES.md`, which is included in the release-file list.

For explicit removal of the old experience's data, use [the legacy cleanup procedure](../docs/data-and-recovery.md). Test it only against disposable stores during development. The browser check also verifies that records navigation is absent and old client drafts are discarded.

`dev/check-updates.mjs` checks conversational lesson rewrites, extension, regeneration, review/apply/dismiss, pending-proposal reload, and read-progress/conversation preservation in the simulated preview. Use the same Playwright environment settings as the other browser checks and an isolated disposable store; it creates one new path. Screenshots default to `/tmp/hermes-learning-updates-check`.


## Lesson practice and model checks

`dev/check-practice.mjs` uses the labelled preview and a disposable store. It checks configured-model selection, separate inline feedback, hints, retry/history, navigation during evaluation, local draft and backend feedback restoration, explicit tutor handoff, skipping independently from read progress, and mobile overflow. Use the same Playwright environment variables as the other browser scripts. Screenshot files are `/tmp/hermes-learning-practice-desktop.png` and `/tmp/hermes-learning-practice-mobile.png`. The preview has synthetic models and deterministic feedback; it never calls an external model.

Backend tests in `test_lesson_practice.py` cover lesson metadata, version-bound capabilities, idempotency, source policy, revoked contexts, concurrent submissions, and model preference authorization. Adapter tests exercise the practice tool restriction hook. JavaScript tests cover model discovery/branch routing and the independent practice session controller, including forbidden tools, interruption, uncertain delivery, and restoration. Real model teaching quality still requires the separate evaluation procedure.

`node dev/check-gateway-contracts.mjs /path/to/hermes-agent` validates the plugin’s actual model-switch and practice-creation payloads against the installed Hermes Pydantic wire contracts. It also reproduces the rejected `session.branch_stored` override fields on affected hosts. It imports schemas only: no gateway connection, model call, credential access, or service restart. Override `HERMES_PYTHON` if the checkout uses a different Python environment. Run this alongside simulations when changing host RPC payloads; a shared internal implementation does not imply identical public method parameters.


`python3 dev/seed-media.py` creates a fresh temporary preview database and prints its directory. Start `dev/serve.py --port 8897 --data-dir <printed-directory>`, then run `dev/check-media.mjs` with the same Playwright environment variables as the other browser scripts. This exercises real Mermaid and the bundled Archify renderer, a saved PNG whose original file has been deleted, malformed/forbidden source fallback, zoom, nested preview dialogs, reload, mobile layout, and absence of external requests. Screenshots are `/tmp/learning-media-desktop.png` and `/tmp/learning-media-mobile.png`. Node.js 18+ must be available to the backend preview for Archify. Python media tests cover all five Archify types and image persistence, backup, quota/type restrictions and cross-path access.

`dev/check-review.mjs` checks the unified revision diff, collapsed context, rendered media comparison, minimize, mobile layout, and apply/reload. Seed with `python3 -B dev/seed-media.py`, serve its returned disposable directory, and run with the browser environment variables above. The check applies its fixture proposal. `dev/check-updates.mjs` also covers the diff review in conversational rewrite, extension, regeneration, and dismissal flows.

`dev/seed-continuity.py` creates an isolated path with an earlier lesson edit and a flagged later lesson. Serve its returned directory and run `dev/check-continuity.mjs` with the browser environment variables above. It checks keep/reload, a new warning after another edit, proposing and applying a fix, mobile layout, and saved earlier content in the next generation prompt. The tutor remains simulated; this validates context delivery and workflow, not live-model teaching quality.

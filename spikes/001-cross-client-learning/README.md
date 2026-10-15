# 001: Cross-client learning spike

## Verdict: PARTIAL

A runnable throwaway plugin with an interactive authored lesson, backend-owned attempts, real Hermes tool registration, and a real dashboard UI. The web/backend path is exercised, and read-only rendering/navigation is verified in a real isolated Electron host. Desktop writes and messaging remain manual checks. This is not the full product and is not ready to install into a daily instance without review.

## What you can try

Read the short retry/idempotency scenario, step through its SVG sequence, and optionally predict the outcome. Reading does not start tracking. Select **Start tracked learning**, optionally ask for a recorded hint, and submit an answer. The backend saves it as **awaiting assessment**, not as mastered. Leave tracking to reject later writes while retaining the committed answer.

The only lesson is an authored fixture, clearly labeled. It is not a retrieved paper, fabricated API result, or model-generated tutorial. No model call is needed for this spike.

## Run without touching your daily Hermes

Prerequisites: an existing Hermes source/runtime with FastAPI and the built dashboard already available. No npm or Python dependencies are installed by these commands. Use Hermes's Python environment if your shell Python cannot import its dependencies.

From the repository root, substitute the path to your existing Hermes source:

```bash
python spikes/001-cross-client-learning/run.py --source /path/to/hermes-agent prepare
python spikes/001-cross-client-learning/run.py --source /path/to/hermes-agent serve
```

The server binds **127.0.0.1** on an OS-assigned port and prints `HERMES_DASHBOARD_READY port=...`. Open `http://127.0.0.1:<port>/learning-spike` in a browser on that machine. Stop only this foreground process with Ctrl-C. An optional `--port <port>` before `serve` chooses a fixed local port.

By default the disposable runtime lives under the current scratch directory. Both OS `HOME` and `HERMES_HOME` are redirected, credentials are not copied, lazy installs are disabled, and the runner asserts that Hermes's default/machine root matches the isolated home. Redirecting only HERMES_HOME under the daily `.hermes` directory is insufficient isolation. Runtime state can be removed by scratch cleanup; use a dedicated `--home /path/to/empty-test-directory` if you want to keep spike records. The runner refuses an unrelated nonempty directory.

`prepare` uses Hermes's configuration setter only inside that private home and stages a copy of the plugin. It preserves that home's learning database. Run it again after editing plugin files, then restart only the owned test server to reload backend routes. Do not use the global dashboard stop command; it could target other servers.

The isolated server has its own session token. Never publish `session-token`, the runtime directory, HTML containing injected credentials, or active context IDs. Do not expose this spike on a public bind.

## Basic checks

```bash
python -B -W error::ResourceWarning -m unittest discover -s spikes/001-cross-client-learning/tests -v
node spikes/001-cross-client-learning/tests/check_recovery.cjs
node --check spikes/001-cross-client-learning/plugin/dashboard/dist/index.js
node --check spikes/001-cross-client-learning/plugin/desktop/plugin.js
```

After `prepare`, inspect actual registered tools and bundled skills:

```bash
python spikes/001-cross-client-learning/run.py --source /path/to/hermes-agent inspect
```

With the real isolated server running, execute the small integration check. Use the runtime home printed by preparation and the server's port:

```bash
python spikes/001-cross-client-learning/check_integration.py   --source /path/to/hermes-agent   --home /path/to/isolated-runtime   --url http://127.0.0.1:<port>
```

It exercises actual host authentication, command registration, registry dispatch, HTTP routes, shared storage, retry/conflict behavior, and exit. It writes only labeled integration fixtures. Re-running adds another explicit test context and two committed fixture attempts. This is deliberate, not a clean-database assertion.

## Tools and skills

Registered toolset: `learning_spike`.

- `learning_spike_lesson`: read the authored scenario.
- `learning_spike_status`: inspect saved state only when requested.
- `learning_spike_hint`: record requested help in an active context.
- `learning_spike_submit`: submit a verbatim answer using the server-issued run ID.
- `learning_spike_leave`: revoke the selected context.

There is intentionally no model-facing enroll/start tool. Explicit entry is through the workspace action or registered `/learning-spike start <label>` command. A helper can exercise the registered command in the isolated runtime:

```bash
python spikes/001-cross-client-learning/run.py --source /path/to/hermes-agent command 'start My test'
python spikes/001-cross-client-learning/run.py --source /path/to/hermes-agent tool learning_spike_lesson '{}'
```

Use `tool learning_spike_submit '<JSON>'` with the IDs returned by the explicit start, `run_id`, and `answer`. The helper does real registry dispatch; it does not simulate a model conversation or verify messaging integration.

Bundled skills: `hermes-learning-spike:teach` and `hermes-learning-spike:humanizer`. The latter is an original project-specific, Humanizer-compatible adaptation, not a vendored copy of a developer-profile skill. Host registration and skill retrieval are verified; actual model adherence has not been evaluated.

## Manual checklist

- Open the web page. Reading/step controls do not create a tracking context.
- Start tracking, request a hint, submit a prediction, and observe saved/pending state.
- Refresh or open a second view; explicitly select the active context. The same attempts appear. Draft answers do not transfer.
- Retry a failed submission without changing the saved run/answer. It does not create another attempt. Use **New attempt** for an intentional repeat. If a new-run response is lost or another client advances it, Refresh follows the current server run; an uncertain answer retains its original retry identity until exact committed readback resolves it.
- Leave tracking. Existing answers remain; late writes fail.
- After separate installation approval, enable the desktop plugin in a test desktop client and connect it to the same backend. Verify the same diagram and attempts. Do not install into the daily desktop just to tick this box.
- After separate installation approval, manually try the tools/skill through whichever messaging channels you use. Do not conclude all channels work from one successful test.

## Observed results

See [recorded results](results/README.md), [integration assertions](results/integration.json), and the web screenshots when present.

## Intentional limits

- Context IDs are personal-use write capabilities, not robust conversation-bound consent. No start tool is exposed, and inactive/unknown contexts are rejected, but natural-language opt-in and per-session provenance are not fully enforced. Broad R10 is only partially proven.
- UI refresh for another client's changes is manual. Drafts are memory-only and lost on reload; there is no offline synchronization or implemented local-draft recovery.
- No discovery/curriculum generation, PDF ingestion, source retrieval pipeline, scheduled review, persisted grading/self-assessment, or automatic model feedback.
- No raw-user-message verification or explicit UI-versus-chat capture field yet. Submitted tool text is relayed as given; full evidence provenance remains future work.
- Both adapters use the same controlled schema/renderer behavior; the small renderer is duplicated to avoid a bundler. The real desktop host has been checked for read-only rendering/navigation; that does not establish its write flows or full cross-client UX.
- SQLite initialization is basic and the database is disposable. A release migration/backup policy is not implemented.

## Recommendation

Keep the shared backend and host adapter pattern if manual use confirms it is useful. Resolve session-bound consent and real desktop/messaging behavior before promoting this into the first usable product. Do not expand ingestion or grading while those boundaries remain unproved.

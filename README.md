<img src="ui/src/learning-mark.svg" width="64" height="64" alt="Hermes Learning winged book logo">

# Hermes Learning

A personal learning workspace for Hermes Agent: source-grounded study, interactive diagrams, practice, and evidence shared across desktop, web, and chat tools.

**Status: v0.1 development plugin implemented.** The actual Hermes web plugin and Electron desktop plugin have been exercised against the same isolated backend. The full requirements remain the product roadmap; this is not a claim that every proposed policy or messaging workflow is release-certified. See [compatibility and verification](docs/compatibility.md) for tested versions, a host startup workaround used during verification, and remaining boundaries.

## What is implemented

- A shared React workspace with study, progress, sources and evidence views; sequence, state-machine and code-trace visuals; light/dark themes, keyboard controls and narrow layouts.
- Saved discovery and proposed paths, optional background/goal/session time, and separate learner approval. Start from a vague curiosity, a goal, or a source.
- Candidate source recommendations with accept/decline actions, curated excerpts, source locators and model-sharing policies, and conservative quote matching.
- Explanation, prediction, trace and build activities linked to objectives, with diagnostic/practice/transfer purposes and conceptual/practical evidence. Immutable revisions preserve the original prompt and criteria.
- Authored and generated hints saved with their actual content and attribution; generated-help retries preserve one event. Local UTF-8 text, Markdown and code import offers an editable preview before attachment.
- Verbatim answers with server-issued retry identity, local draft recovery, assistance/channel provenance, separate self/agent assessments, disputes, and append-only corrections.
- Criterion-level feedback, uncertainty, objective progress and a suggested next step, including pending assessments and disputes. Linked activities schedule objective reviews and suggest another available activity for practice.
- An inspectable review queue, manual deferral, archive/pause/resume, safe JSON export and consistent SQLite backup. Desktop prepares the resume command in a new chat; both clients provide the follow-up tutor request to copy.
- Hermes backend tools, `/learning-track` commands, an authenticated dashboard adapter, a native desktop adapter, and original teaching/Humanizer guidance.

Ordinary educational chat remains ad hoc. Opening the workspace reads records but does not enroll another conversation. Explicit start/resume creates a revocable tracking context. Submission saves an answer as awaiting assessment; no model call or automatic grade happens behind the button. The authored retry example is optional and creates records only when explicitly started.

## Build and try it

Use Node.js 22+ and Python 3.11+. The plugin backend uses Hermes's existing FastAPI/Pydantic runtime; the standalone development preview needs only Python's standard library.

```sh
npm --prefix ui ci
npm --prefix ui run build
python3 -B dev/serve.py --port 8877 --data-dir /tmp/hermes-learning-preview
```

Open [the local preview](http://127.0.0.1:8877/). It uses the real learning service and an isolated SQLite store, not mock saved progress. The browser preview itself is not the Hermes host. See [preview details](dev/README.md).

Build output:

| Surface | Artifact | Runtime |
| --- | --- | --- |
| Backend + web | `plugin/` | Hermes backend plugin manager and dashboard |
| Desktop | `plugin/desktop/plugin.js` | Hermes native disk-plugin loader and `@hermes/plugin-sdk` |
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

## Package

After building:

```sh
python3 -B dev/package.py
```

This produces a combined backend/web/desktop package and a standalone desktop package in `dist/`, with checksums. Packages contain code and teaching skills, not learning records, session tokens, developer dependencies, or the preview database.

## Data and recovery

The backend resolves the active profile's `plugin_data_dir('hermes-learning')/data.db` on every operation. SQLite uses WAL, guarded schema initialization, transactions and revision checks. The desktop and web clients must point to that same backend/profile.

Drafts are private to the browser/desktop origin, scoped by store, track and activity, and labeled unsubmitted. They persist in local storage until cleared; they are not encrypted, synchronized between devices, or authoritative evidence. Session tracking selection is separate from drafts. Failed delivery retains the exact answer/run identity; definitive rejections preserve editable text. Explicitly abandoning an uncertain retry warns that another attempt may duplicate a previously delivered answer.

JSON export is a human-readable safe view, **not a full backup**. Use `Store.backup(new_path)` with an existing protected destination directory for a consistent complete SQLite snapshot. Stop writers before restoring the complete database; do not replace a live database while WAL files are in use. No arbitrary backup/restore path is exposed to the agent or web API.

## Verification

Run the backend suite with the same Python environment that supplies Hermes's FastAPI dependencies. Preview HTTP tests need loopback socket permission.

```sh
/path/to/hermes-agent/.venv/bin/python -B -W error::ResourceWarning -m unittest discover -s tests -v
npm --prefix ui test
npm --prefix ui run build
python3 -B dev/evaluate.py
/path/to/hermes-agent/.venv/bin/python -B -W error::ResourceWarning -m unittest discover -s spikes/001-cross-client-learning/tests -v
node spikes/001-cross-client-learning/tests/check_recovery.cjs
```

The service tests cover consent/revocation, cross-track references, source policy, version/key gating, retries, assistance, corrections, objective evidence, fixed-clock scheduling, concurrent startup, and backup restoration. The deterministic evaluation checks complete tool flows; it does not evaluate a model's teaching. See the [tutoring evaluation guide](docs/evaluations/tutoring.md) and [compatibility](docs/compatibility.md) for observed results and runtime boundaries.

## Remaining product boundaries

- Conversation-bound consent needs a verified Hermes identity bridge. Current contexts are revocable private capabilities, not authenticated conversation identities. This is a personal single-user plugin.
- Chat authoring uses Hermes tools; no new backend inference, search service, PDF ingestion, repository execution, or automatic full-book processing is included.
- Reference verification is author-reported. Source protection follows declared source references; it cannot retrospectively retract content already shared with a model.
- Review uses a transparent 1/3/7-day heuristic: policy v2 follows linked objectives, while unlinked legacy activities retain policy v1. Evidence summaries are not calibrated mastery or retention estimates.
- Generated-help capture requires the tutor to use the help tool before giving assistance. Teaching quality and actual messaging-channel behavior need ongoing evaluation; skill loading alone does not prove adherence.
- Native chat preparation depends on the inspected desktop composer API, preserves existing drafts, and does not send messages. Arbitrary remote/proxy topologies, offline writes, multi-user operation, and all-version host support are not claimed.

## Product documents

[Requirements](docs/requirements.md) · [Architecture](docs/architecture.md) · [Learner flows](docs/user-flows.md) · [Teaching quality](docs/teaching-quality.md) · [Implementation plan](docs/superpowers/plans/2026-10-16-learning-plugin.md)

The [original disposable spike](spikes/001-cross-client-learning/README.md) and its recorded results are retained as historical evidence. They are not the current product package.

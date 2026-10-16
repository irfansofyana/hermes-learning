# Hermes Learning implementation plan

> **For agentic workers:** Use superpowers:executing-plans. Independent backend and adapter tasks may run in parallel with explicit file ownership.

**Goal:** Implement the personal learning plugin described in the existing product requirements, with one shared, polished web/desktop workspace.

**Architecture:** A new `plugin/` package replaces the disposable spike as the development target. A transactional SQLite learning service owns records. Thin Hermes tool and HTTP adapters call it; a shared React workspace is bundled into dashboard and desktop entry points. The original spike remains historical evidence, not a compatibility claim for the new implementation.

**Tech stack:** Python 3, SQLite, FastAPI host adapter; React, CSS, esbuild; Python unittest and browser interaction checks.

**Spec:** `docs/requirements.md`, `docs/architecture.md`, `docs/user-flows.md`. The user authorized implementation on `spike/cross-client-learning` on 2026-10-16. No daily-instance installation or restart is included.

## Product and visual direction

One calm learning workspace with a narrow track navigator, generous reading area and contextual practice panel. Use pale neutral surfaces, deep ink text, restrained teal, a serif study title and clear sans-serif controls. Diagrams are functional controlled SVG, not decorative imagery. Dark mode follows the host, with a local preview toggle for development. At narrow widths navigation collapses and practice follows the reading area.

Views: Continue learning, track workspace (Study / Sources / Evidence), discovery and path approval, source attachment, activity authoring, and review queue. Empty states offer actual creation actions; examples require an explicit action and are labeled authored demonstrations. No invented progress percentages. Tracking, pending assessment, unknown assistance and source disclosure remain visible.

## Global constraints

- Reading an overview does not enroll. Explicit start/resume creates a workspace context; leave revokes it. No model-facing start tool.
- Store identity, schema/API version and client compatibility are checked before writes. Learning data stays outside the repository.
- Content is plain text or validated structured sequence data. No imported executable markup or automatic network/document ingestion.
- Sources have metadata-only / selected-excerpts / full-text policies. Model retrieval applies policy independently of UI access.
- Attempts retain immutable activity versions, channel and assistance; submissions await assessment. Self and agent assessments remain separate.
- Source retrieval and backend inference are not silently introduced. Chat handoffs are copyable and honest about what happens next.
- Drafts stay local and unsubmitted, scoped by store/track/activity/run; uncertain submission identity survives refresh.
- Release verification must distinguish local preview, adapter tests, real dashboard, real Electron, and real messaging.

## Shared service contract

`plugin/learning_store.py` exports `LearningError` and `Store(path, clock=None)`.
`Store.dispatch(action: str, params: dict, *, channel='ui_direct') -> dict` handles these actions. Writes require `context_id` except `start` and `resume`, which are restricted by adapters to explicit user actions.

- `state {}` → `{api_version:1,schema_version:1,store_id,tracks,sources,activities,attempts,assessments,reviews}`. Never return contexts/capabilities or hidden activity solutions here.
- `start {title,interest}` → `{context_id,track_id}`; creates exploring track. `resume {track_id}` → fresh context; `leave {context_id}` revokes only that context.
- `track {track_id}` → `{track,sources,activities,attempts,assessments,reviews}` with safe activity summaries.
- `brief {context_id,revision,brief,objectives}` edits track proposal; `approve {context_id,revision}` activates it; `track_status {context_id,revision,status}` supports active/paused/archived without deleting evidence.
- `source {context_id,title,kind,url,locator,excerpt,sharing,verification}` creates curated source; `source_read {source_id}` returns human content or policy-filtered model content by channel.
- `activity {context_id,title,kind,prompt,criteria,solution,hints,source_ids,visual}` creates immutable v1; `activity_read {activity_id,context_id?}` returns gated activity. `run {context_id,activity_id}` issues `{run_id,activity_id}`.
- `help {context_id,run_id,level}` records and returns help; levels nudge/targeted-hint/worked-step/full-solution-shown.
- `submit {context_id,run_id,answer}` → `{attempt,duplicate}`; exact retry idempotence, changed retry conflicts.
- `assess {context_id,attempt_id,method,feedback,outcome,supersedes?}` appends self or agent assessment; outcome needs-work/developing/demonstrated; method attribution follows channel.
- `dispute {context_id,assessment_id,reason}` appends dispute and marks review reason; `review {context_id,review_id,due_at}` adjusts due date.
- `resume_brief {track_id}` returns server-derived continuity and text alternatives, no hidden keys.
- `export {}` returns versioned learning records; `backup(path)` produces consistent SQLite backup outside normal API/tool actions.

Track fields: `id,title,interest,status,brief,objectives,revision,created_at,updated_at`. Activity summary fields: `id,track_id,title,kind,prompt,source_ids,version,visual` (bounded visible steps). Source: `id,track_id,title,kind,url,locator,sharing,verification`. Attempt: `id,track_id,activity_id,run_id,answer,channel,assistance,status,created_at`. Assessment: `id,attempt_id,method,feedback,outcome,supersedes,created_at`. Review: `id,track_id,activity_id,due_at,reason,policy_version`.

## Review focus

1. Revoked contexts and cross-track IDs must fail before mutations; model adapters cannot issue consent.
2. Solution/source content must not leak through state, resume, export tools or structured visuals.
3. Lost submission responses must preserve exact run and payload across reload and must not overwrite drafts during polling.
4. Concurrent startup and submission, incompatible schema, backup restoration and stale revisions must fail safely or recover deterministically.
5. Empty data, long labels, narrow screens, keyboard focus, host theme and disconnected backend must remain usable.

## Tasks

### 1. Durable learning domain
Files: `plugin/learning_store.py`, focused sibling modules if needed, `tests/test_learning_store.py`.
- [x] Write failing tests for explicit entry/exit, revision guards, source policy, immutable activity criteria, assistance, retry conflicts, assessment correction, deterministic review, concurrency and backup.
- [x] Implement the shared contract with transactionally guarded schema initialization and bounded validation.
- [x] Run `python3 -B -W error::ResourceWarning -m unittest discover -s tests -v`.

### 2. Hermes adapters and teaching bundle
Files: `plugin/runtime.py`, `plugin/__init__.py`, `plugin/plugin.yaml`, `plugin/dashboard/plugin_api.py`, `plugin/dashboard/manifest.json`, `plugin/skills/*`, `tests/test_adapters.py`.
- [x] Test tool registration, no start/resume tool, method attribution, malformed requests, and profile-local resolution.
- [x] Register descriptive learning tools and explicit `/learning-track start|resume|approve|leave|status` commands; implement GET state/track/activity/source and POST action endpoints. HTTP POST `/action` accepts `{action,params,api_version:1}`.
- [x] Bundle original teaching/Humanizer guidance covering discovery, source provenance, opt-in, verbatim relay, and pending assessment.
- [x] Verify against available host source; report untested host entry/session binding honestly.

### 3. Shared workspace and build
Files: `ui/src/*`, `ui/package.json`, `ui/build.mjs`, `plugin/desktop/package.json`, generated dashboard/desktop bundles.
- [x] Generate a visual concept before implementation and derive layout, copy and tokens.
- [x] Build a shared workspace factory with injected React/request transport; externalize host React and isolate styles to the plugin root.
- [x] Implement navigation, track creation/proposal approval, study/sequence controls, source management, activity authoring, draft recovery, assistance, submission, self-assessment, evidence and reviews.
- [x] Poll visible state every 25 seconds; refresh on focus/reconnect; clean up listeners and reject stale connection results.
- [x] Build both host entry points and a local preview with a real isolated service, never a fake production backend.

### 4. Integration and delivery
Files: development preview script, README and compatibility documentation.
- [x] Run full new and existing spike tests, build and syntax checks.
- [x] Browser-test empty entry → explicit creation → path approval → source/activity → answer → assessment → review, plus reload, narrow and dark layouts.
- [x] Compare rendered study screen with concept; fix typography, spacing, contrast, overflow and behavior.
- [x] Review cross-adapter data/consent boundaries and record any genuine host/runtime limitations.
- [x] Document setup, coordinated packaging, backup and remaining release verification. Preserve daily Hermes instance.

## Delivery outcome (2026-10-16)

The implementation tasks above are complete for v0.1. Both real host frontends were exercised against one isolated backend, including native Electron writes and restart persistence. This does not complete every roadmap requirement. Conversation-bound consent, messaging verification, generated-help capture, and objective-level review remain documented in README and compatibility notes. The tested host required a temporary missing-import startup workaround; daily host files were untouched.

# Integrated Learning Implementation Plan

> Execution: subagent-driven implementation with independent file ownership, followed by integration and review. The user explicitly requested implementation without further approval checkpoints, directly on main.

**Goal:** Generate lessons from topics, projects and sources and run the tutor inside Learning.
**Architecture:** Add course records and bounded generation tools to the existing SQLite service. A shared client controller uses native Hermes sessions through Desktop SDK or authenticated dashboard WebSocket. Replace the primary UI; retain the old records interface as a secondary view.
**Tech Stack:** Python/SQLite/FastAPI, React/esbuild, Hermes gateway JSON-RPC.
**Spec:** docs/superpowers/specs/2026-10-16-integrated-learning-design.md

## Global constraints
- Work on main; preserve existing learning records and public root package layout.
- No daily Hermes installation/restart; use isolated profiles for validation.
- No extra provider credentials, silent fallback AI, copied commands or initial interview.
- Generation and Continue are explicit user actions that authorize their scoped records and model work.
- Text/Markdown/code imports only; unsupported inputs and unread links remain visibly identified.

## Shared contracts
All backend calls use POST /action with api_version:1.
- course_start({request_id,title,intent,level,materials}) -> {track_id,context_id,job_id}. intent=topic|project|sources; level=beginner|intermediate|advanced. materials use existing source fields title,kind,url,locator,excerpt,sharing. Atomic and idempotent.
- course_open({track_id}) -> {track_id,context_id,job_id?,lesson_key?}; recovers an active generation context or prepares a new context for a human Continue action.
- course_read({track_id}) -> {track,outline:[{key,title,goal}],lessons:[{key,title,content,source_ids,visual}],position:{lesson_key,completed:[]},binding:{session_id,scope}|null,jobs:[],sources:[]}. No context capabilities in read results. Source contents obey channel policy.
- course_generate({context_id,request_id,lesson_key?}) -> {job_id}. No lesson_key means initial outline+first lesson; a key permits that lesson only.
- course_bind({context_id,session_id,scope}) -> binding. UI only, durable Hermes stored session ID.
- course_position({context_id,lesson_key,completed?}) -> position. UI only.
- course_plan({context_id,job_id,summary,assumptions,lessons:[{key,title,goal}]}) -> outline. Model publication for an authorized initial generation job, idempotent.
- course_lesson({context_id,job_id,lesson_key,content,source_ids,visual?}) -> lesson. Validated publication, idempotent and restricted to job's path/lesson.
- course_job_status({context_id,job_id,status,error?}) -> job. UI controls stopped/failed status; completion follows successful publication.

Transport factory createTutorTransport(host) / createWebTutorTransport(SDK) returns {request(method,params),onEvent(type,callback):unsubscribe,dispose()}. Events normalized to {session_id,payload}; actual host event names preserved. Web transport authenticates with SDK.buildWsUrl('/api/ws'). Requests connect lazily; failures are explicit and uncertain prompts are never automatically replayed.
Tutor controller is integrated by root: creates/resumes durable session, binds it, submits contextual prompt, streams events, restores history, handles approval/clarification, rejects stale path/profile events.
UI App consumes request(path,body), tutor transport and scope, preview flag. Root owns controller and entrypoint wiring; UI worker owns new interface only.

## Tasks and ownership
1. Backend worker: course storage module, learning_store/runtime integration, __init__ tools, manifest, package allowlist and backend tests. Write failing boundary tests then implement and run existing tests.
2. Transport worker: ui/src/tutor-transport.mjs and ui/test/tutor-transport.test.mjs. Inspect real host protocol and test request correlation, auth URL, disconnect, cleanup, event normalization and no retry.
3. UI worker: ui/src/LearningApp.jsx, learning-workspace.css, CourseContent.jsx, input helper and tests. Home/input, outline/lesson/tutor, source status, legacy records affordance, responsive layout. Root supplies useTutor hook.
4. Root: ui/src/useTutor.jsx + tutor-session.mjs tests; Desktop/dashboard/preview entrypoints; guidance/docs; build/isolated browser and host integration; review and fix; commit/push.

## Review focus
- Resume returns runtime session ID differing from durable ID; preserve identity and history.
- Disconnect after prompt acceptance must not automatically submit twice.
- Cross-track, revoked context, metadata-only sources and malformed generated lessons must fail closed.
- File errors must preserve valid inputs and allow removal; first lesson must not remain permanently blank after a failed turn.
- Old tracks must remain accessible; generated content must never execute HTML or source code.

## Verification
Python unittest suite with host dependencies, Node UI tests, production build and JS syntax checks. Browser checks cover actual service with explicitly simulated transport; separate isolated Hermes check establishes actual model/gateway operation. Record exact runtime limitations rather than claiming all hosts work.


## Completed implementation and validation

Implemented the integrated lesson reader/tutor, topic/project/source entry, bounded source retrieval publication, native/web conversation transport, durable conversation restoration, explicit Stop/reconnect/retry, and the retained detailed records view. Fresh review findings were fixed: cancelled preparation, missing conversation recovery, failure restoration, selected level context, later-lesson job recovery, completion races, and legacy objective preservation.

- 77 Python tests passed with the Hermes environment and loopback permission; no skips.
- 57 UI tests passed; production Desktop, dashboard, and preview bundles built.
- Deterministic learning-contract evaluation and local actual-Hermes installer discovery passed.
- `dev/check-integrated.mjs` passed against a disposable preview store, including project/files/link input, embedded conversation, next lesson, reading position, reload/Continue, and mobile dark layout. This uses an explicitly labelled simulated tutor.
- The actual isolated web dashboard used the configured model to save a two-lesson outline and first complete lesson (765 characters), complete its generation job, and persist its conversation binding, without navigation away from `/learning`.
- The actual isolated Electron plugin restored that web-created lesson and conversation and answered a live follow-up inside Learning; no page errors. No daily-host changes or restart. Temporary access-only credentials were removed, and the daily auth file hash remained unchanged.

Known limits: text/Markdown/code imports only; URLs require host reading tools and report agent-observed retrieval status. Published outlines/lessons remain immutable. Assumption adjustments are conversational. Verification targets Hermes v0.22.2 with the documented temporary host annotation workaround; it does not establish all-version or multi-user support.

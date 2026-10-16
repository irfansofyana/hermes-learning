# Architecture

The primary interface generates lessons and runs a tutor inside Learning. The service retains the existing activity/evidence system and adds course records without reinterpreting historical answers. [Compatibility](compatibility.md) records runtime verification; [the integrated design](superpowers/specs/2026-10-16-integrated-learning-design.md) describes the intended experience and constraints.

```text
Desktop UI -- host.request / host.onEvent --+
Web UI ----- authenticated gateway WS -----+--> Hermes sessions and configured model
                                          |             |
Shared React learning workspace           |       Learning model tools
             |                            |             |
             +----- versioned HTTP API ---+-------------+--> Learning service --> SQLite
```

## Ownership and boundaries

Hermes owns conversation history, model credentials, agent execution, and tool permissions. Learning owns paths, lessons, supplied sources, generation jobs, reading position, and practice evidence. The plugin uses public session operations; it does not write to Hermes conversation tables or introduce a separate model provider.

**Generate learning path** authorizes creation of the requested path, its material, and bounded model work. **Continue** establishes or recovers the path's learning context and restores its conversation without submitting a prompt. Ordinary mounting reads saved state. Neither learning vocabulary in an unrelated chat nor loading a teaching skill authorizes plugin persistence.

Repository material is read-only teaching input. Imported code and model-generated Markdown never execute in the workspace. Source text is untrusted material, not instructions. Skills guide teaching; service validation independently enforces authorization and disclosure.

## Records and actions

The API remains version 1. Additive records live beside existing tracks, activities, runs, attempts, assistance, assessments, and reviews:

| Record | Responsibility |
| --- | --- |
| Track | Original goal, topic/project/source intent, level, and saved direction |
| Course | Ordered outline, assumptions, selected lesson, read markers, and tutor binding |
| Lesson | Published Markdown, source references, optional bounded visual, and originating job |
| Generation job | Authorized path, context, target lesson, request identity, status, and publication result |
| Course request | Idempotency identity for atomic initial path creation |

All HTTP actions use `POST /action` with `{ "api_version": 1, "action": "...", "params": {} }`.

| Action | Caller and effect |
| --- | --- |
| `course_start` | UI: atomically save the goal and materials, establish context, and create the initial job; repeated identical request IDs return the same result |
| `course_open` | UI: explicitly continue a track; recover an unfinished job's authorizing context when needed |
| `course_read` | Read the track, outline, lessons, position, sources, and jobs; UI may also read the tutor binding; no context capability is returned |
| `course_generate` | UI: authorize initial generation or one selected outline lesson; an explicit new request can supersede unfinished work for that target |
| `course_bind` | UI: save a durable Hermes session ID with its store scope |
| `course_position` | UI: select a published lesson and optionally record which published lessons were read |
| `course_job_status` | UI: record stopped or failed work; successful publication completes its job |
| `course_plan` | Model publication: save an ordered outline and assumptions for an authorized initial job |
| `course_lesson` | Model publication: save only the job's authorized lesson with validated content, references, and visual |
| `course_source` | Model publication: record retrieved text or a retrieval failure for an explicitly supplied URL within the active job |

Model publication tools use the `learning_` prefix. They cannot create arbitrary generation work, resume unrelated tracks, or expand a job's target. Publication is transactional and idempotent; a changed payload conflicts with an existing publication. Source IDs must belong to the path, and unread links cannot be cited as source text. Saved outlines and lessons currently remain immutable.

## Tutor lifecycle

`LearningApp.jsx` orchestrates explicit course actions. `useTutor.jsx` wraps the shared `TutorSession` controller; `tutor-transport.mjs` supplies the Desktop and dashboard adapters. Desktop uses public `host.request` and `host.onEvent`. The dashboard obtains an authenticated WebSocket URL through `SDK.buildWsUrl('/api/ws')`.

The controller creates or resumes one conversation per path, binds its durable session ID, then submits a prompt containing the current course context and source metadata. It does not copy every source excerpt into each message. The tutor reads permitted text through Learning tools.

Runtime session IDs can change after resume or compression. The controller uses the current runtime ID for gateway requests and events while retaining the durable ID for later restoration. Bindings are scoped to the authoritative Learning store identity; the selected host profile is also carried in host operations. Backend/profile changes reset the UI and controller so a draft or late event cannot attach to another path.

Streaming events update the transcript and refresh published course data. History restoration reconciles saved messages with the host's current state. Permission and clarification requests appear inside the tutor and require an explicit response. Stop interrupts the current runtime and records stopped generation where applicable.

A lost acknowledgement is not automatically replayed. The UI exposes reconnect so the controller can reconcile the saved session before another prompt. Partial outlines and lessons remain saved; retrying generation is a separate user action. A missing provider, disconnected gateway, or failed publication leaves a visible error rather than a fallback answer.

## Sources and rendering

Import accepts supported UTF-8 text, Markdown, and code. Per-source limits are 50,000 characters and 200 KB; a path accepts at most 20 materials with aggregate excerpt limits of 100,000 characters and 200,000 UTF-8 bytes. The UI also bounds serialized material before submission. Failed files remain individually visible and removable.

Supplied text is marked `provided`; links begin `unread`. Retrieval can record `read`, `failed`, or `unsupported` with failure details. Retrieval success is agent-reported, not independent verification. Sharing policies remain `metadata-only`, `selected-excerpts`, and `full-text`; metadata-only text is withheld from model reads and cannot support model-authored lesson content.

External research citations use ordinary Markdown links containing the actual retrieved URL. Attached material still uses validated `source_ids`. Lesson publication rejects internal provider citation markers with a retryable validation error; older unresolved markers display a missing-source-link label instead of exposing search handles or guessing a URL.

The UI renders Markdown as escaped React elements. Raw HTML, scripts, source code, and arbitrary visual markup are not interpreted. Sequence, state-machine, and code-trace visuals use the existing bounded schemas and fixed components, with source disclosure and hidden-step gates enforced by the service.

## Practice evidence and storage

Marking a lesson read is distinct from mastery. A tutor question does not become an attempt. Existing practice captures immutable activity versions and criteria, exact answers, known assistance, author/channel attribution, and separate self or agent assessments. Corrections supersede earlier assessments without erasing evidence; disputes remain attributable.

Objective progress joins attempts, assistance, assessments, and disputes. Conceptual and practical evidence remain separate. Pending assessment and disputes take precedence in the legacy next-action projection. Objective-linked reviews retain policy v2 and legacy activities policy v1, with transparent 1/3/7-day scheduling.

The server-local SQLite store uses guarded initialization, transactional writes, WAL/busy handling, and explicit store identity. Store paths resolve for the active profile per operation. Context validation rejects cross-track, revoked, and stale writes. Source disclosure applies to nested lesson, activity, help, and feedback content. Local drafts are unsubmitted UI state, not authoritative evidence.

## Distribution and verification

The repository root is the installable package. Shared React sources build committed Desktop and dashboard bundles. Remote backend installation and local Desktop frontend installation are distinct requirements.

The development preview uses the real Learning service with an explicitly simulated tutor transport. It verifies UI and persistence flows without model calls, link retrieval, or daily-profile changes. Production bundles use host transports only. Unit tests, preview browser checks, and isolated real-host tests establish different boundaries; passing one does not establish the others. See [development](../dev/README.md) and [compatibility](compatibility.md).

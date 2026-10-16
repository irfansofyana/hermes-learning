# Architecture

The primary interface generates lessons and runs a tutor inside Learning. The retired activity-management app and chat-command entry flow are no longer registered or bundled. [Compatibility](compatibility.md) records runtime verification; [the integrated design](superpowers/specs/2026-10-16-integrated-learning-design.md) describes the intended experience and constraints.

```text
Desktop UI -- host.request / host.onEvent --+
Web UI ----- authenticated gateway WS -----+--> Hermes sessions and configured model
                                          |             |
Shared React learning workspace           |       Learning model tools
             |                            |             |
             +----- versioned HTTP API ---+-------------+--> Learning service --> SQLite
```

## Ownership and boundaries

Hermes owns conversation history, model credentials, agent execution, and tool permissions. Learning owns paths, lessons, supplied sources, generation jobs, pending course proposals, reading position, and tutor bindings. The plugin uses public session operations; it does not write to Hermes conversation tables or introduce a separate model provider.

**Generate learning path** authorizes creation of the requested path, its material, and bounded model work. **Continue** establishes or recovers the path's learning context and restores its conversation without submitting a prompt. Ordinary mounting reads saved state. Neither learning vocabulary in an unrelated chat nor loading a teaching skill authorizes plugin persistence.

Repository material is read-only teaching input. Imported code and model-generated Markdown never execute in the workspace. Source text is untrusted material, not instructions. Skills guide teaching; service validation independently enforces authorization and disclosure.

## Records and actions

The API and storage schema remain version 1. The current workspace uses these records:

| Record | Responsibility |
| --- | --- |
| Track | Original goal, topic/project/source intent, level, and saved direction |
| Course | Current revision, ordered outline, assumptions, selected lesson, read markers, and tutor binding |
| Course proposal | Pending summary, proposed outline/lesson changes, base revision, request identity, and decision status |
| Lesson | Published Markdown, source references, optional bounded visual, and originating job |
| Generation job | Authorized path, context, target lesson, request identity, status, and publication result |
| Course request | Idempotency identity for atomic initial path creation |

All HTTP actions use `POST /action` with `{ "api_version": 1, "action": "...", "params": {} }`.

| Action | Caller and effect |
| --- | --- |
| `course_start` | UI: atomically save the goal and materials, establish context, and create the initial job; repeated identical request IDs return the same result |
| `course_open` | UI: explicitly continue a track; recover an unfinished job's authorizing context when needed |
| `course_read` | Read the track, revision (default 1 for older courses), proposals, outline, lessons, position, sources, and jobs; UI may also read the tutor binding; no context capability is returned |
| `course_generate` | UI: authorize initial generation or one selected outline lesson; an explicit new request can supersede unfinished work for that target |
| `course_bind` | UI: save a durable Hermes session ID with its store scope |
| `course_position` | UI: select a published lesson and optionally record which published lessons were read |
| `course_job_status` | UI: record stopped or failed work; successful publication completes its job |
| `course_plan` | Model publication: save an ordered outline and assumptions for an authorized initial job |
| `course_lesson` | Model publication: save only the job's authorized lesson with validated content, references, and visual |
| `course_propose` | Model: save a bounded proposal for the active track without changing its visible course |
| `course_apply` | Human UI only: atomically apply a pending proposal if its base revision is current |
| `course_dismiss` | Human UI only: dismiss a proposal without changing course content |
| `course_source` | Model publication: record retrieved text or a retrieval failure for an explicitly supplied URL within the active job |

Model publication tools use the `learning_` prefix. They cannot create arbitrary generation work, resume unrelated tracks, or expand a job's target. Publication is transactional and idempotent; a changed payload conflicts with an existing publication. Source IDs must belong to the path, and unread links cannot be cited as source text. Initial publication uses `course_plan` and `course_lesson`; subsequent changes to saved content use proposals.

## Conversational course changes

`learning_course_propose` accepts `context_id`, a stable `request_id`, `base_revision`, `mode` (`revise`, `extend`, or `regenerate`), `summary`, optional full `outline` entries (`key`, `title`, `goal`), and optional `lessons` (`lesson_key`, `content`, `source_ids`, optional `visual`). Lesson titles come from the proposed outline. At least one actual change is required. Normal source, citation, content and visual bounds apply; pending proposals and payload sizes are bounded.

- **Revise** keeps the existing outline when omitted. An explicit outline can add, remove or reorder lessons; supplied lesson content replaces only those lessons. Unchanged lesson records and read markers survive; replaced lessons receive a higher version and lose their read marker, and removed lessons lose theirs. The selected lesson stays valid.
- **Extend** requires the existing outline as an identical prefix plus new entries. Only new lessons can be supplied. Existing lessons, selection and read progress survive.
- **Regenerate** requires a new outline and complete first lesson. It replaces all current lessons and resets read markers and position to that first lesson.

Sources and the tutor binding survive every mode. Storage retains current lesson records rather than a lesson-history archive. Each apply increments the course revision. Apply is atomic and idempotent; stale base revisions conflict, and applying a proposal invalidates other pending proposals. Active generation must finish or stop before proposing or applying. A completed generation job cannot republish obsolete content after a course change.

The human reviews a summary, roadmap differences, changed/new lessons and reading-progress impact before choosing **Apply changes** or dismissing. Neither decision is registered as a model tool. Pending proposals survive reload. Stale or failed operations report an error and preserve the visible course. Validation rejects cross-track IDs, revoked contexts, restricted or unread source references, and invalid content. Model reads filter restricted proposal content and never expose context capabilities.

## Tutor lifecycle

`LearningApp.jsx` orchestrates explicit course actions. `useTutor.jsx` wraps the shared `TutorSession` controller; `tutor-transport.mjs` supplies the Desktop and dashboard adapters. Desktop uses public `host.request` and `host.onEvent`. The dashboard obtains an authenticated WebSocket URL through `SDK.buildWsUrl('/api/ws')`.

The controller creates or resumes one conversation per path, binds its durable session ID, then submits a prompt containing the current course revision, selected lesson, context and source metadata. An ordinary question authorizes an answer; an explicit edit request can authorize a proposal, but only the human UI applies it. It does not copy every source excerpt into each message. The tutor reads permitted text through Learning tools.

Runtime session IDs can change after resume or compression. The controller uses the current runtime ID for gateway requests and events while retaining the durable ID for later restoration. Bindings are scoped to the authoritative Learning store identity; the selected host profile is also carried in host operations. Backend/profile changes reset the UI and controller so a draft or late event cannot attach to another path.

Streaming events update the transcript and refresh published course data. History restoration reconciles saved messages with the host's current state. Permission and clarification requests appear inside the tutor and require an explicit response. Stop interrupts the current runtime and records stopped generation where applicable.

A lost acknowledgement is not automatically replayed. The UI exposes reconnect so the controller can reconcile the saved session before another prompt. Partial outlines and lessons remain saved; retrying generation is a separate user action. A missing provider, disconnected gateway, or failed publication leaves a visible error rather than a fallback answer.

## Sources and rendering

Import accepts supported UTF-8 text, Markdown, and code. Per-source limits are 50,000 characters and 200 KB; a path accepts at most 20 materials with aggregate excerpt limits of 100,000 characters and 200,000 UTF-8 bytes. The UI also bounds serialized material before submission. Failed files remain individually visible and removable.

Supplied text is marked `provided`; links begin `unread`. Retrieval can record `read`, `failed`, or `unsupported` with failure details. Retrieval success is agent-reported, not independent verification. Sharing policies remain `metadata-only`, `selected-excerpts`, and `full-text`; metadata-only text is withheld from model reads and cannot support model-authored lesson content.

External research citations use ordinary Markdown links containing the actual retrieved URL. Attached material still uses validated `source_ids`. Lesson publication rejects internal provider citation markers with a retryable validation error; older unresolved markers display a missing-source-link label instead of exposing search handles or guessing a URL.

The UI renders CommonMark and GitHub-style tables, task lists, strikethrough, autolinks and footnotes through React Markdown. Raw HTML remains escaped text, and image references become safe links instead of automatically loading remote media. Tables preserve column headers, alignment, inline formatting and horizontal scrolling on narrow screens. Fenced code uses its language name for syntax highlighting, includes a copy control, and falls back to plain code for unknown or omitted languages. Rendering code never executes it.

Each lesson can include one structured schema-1 sequence, state-machine or code-trace visual, rendered by fixed components with step navigation and a text alternative. Code traces highlight the referenced source line and show authored variable values; these are teaching examples, not execution evidence. Visuals allow 1–30 steps, at most 10 sequence participants or 20 states, valid node references, continuous state transitions and 1-based code-line references. Mermaid, raw HTML/SVG and arbitrary rendering scripts are not supported diagram inputs.

Lesson publication validates the existing visual schema, then normalizes `visible_steps` to the full step count before computing its idempotency hash. Reading older lessons projects the same complete visibility without rewriting stored records. Identical legacy retries compare normalized publication content; changed content still conflicts. Assessed activities retain their separate hidden-step and solution gates. Source disclosure applies before a lesson is returned to the model: restricted derived content also withholds its visual.

## Practice evidence and storage

Marking a lesson read is distinct from mastery. A tutor question does not become an attempt. Existing practice captures immutable activity versions and criteria, exact answers, known assistance, author/channel attribution, and separate self or agent assessments. Corrections supersede earlier assessments without erasing evidence; disputes remain attributable.

Objective progress joins attempts, assistance, assessments, and disputes. Conceptual and practical evidence remain separate. Pending assessment and disputes take precedence in the legacy next-action projection. Objective-linked reviews retain policy v2 and legacy activities policy v1, with transparent 1/3/7-day scheduling.

The server-local SQLite store uses guarded initialization, transactional writes, WAL/busy handling, and explicit store identity. Store paths resolve for the active profile per operation. Context validation rejects cross-track, revoked, and stale writes. Source disclosure applies to nested lesson, activity, help, and feedback content. Local drafts are unsubmitted UI state, not authoritative evidence.

## Distribution and verification

The repository root is the installable package. Shared React sources build committed Desktop and dashboard bundles. Remote backend installation and local Desktop frontend installation are distinct requirements.

The development preview uses the real Learning service with an explicitly simulated tutor transport. It verifies UI and persistence flows without model calls, link retrieval, or daily-profile changes. Production bundles use host transports only. Unit tests, preview browser checks, and isolated real-host tests establish different boundaries; passing one does not establish the others. See [development](../dev/README.md) and [compatibility](compatibility.md).

## Retired experience

There is one frontend: home → path → lesson, with source material and the embedded tutor. There is no secondary Learning records app, activity form, review queue, or main-chat handoff. The teaching package exposes eight course/source tools; the old practice tools and `/learning-track` command are not registered. Internal record-service operations remain for shared implementation and API compatibility, but are not a second product flow.

Old data is discarded rather than converted into courses. `dev/retire_legacy.py` removes legacy-only tracks and their associated records, plus activity/answer/assessment/review/help/run/recommendation records even when attached to a course. It keeps current courses, lessons, materials, jobs, positions and bindings. Cleanup is an explicit operator action, not a destructive read or automatic upgrade. Each client also clears the old interface's draft, location and handoff storage when Learning opens.

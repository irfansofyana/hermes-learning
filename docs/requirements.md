# Draft requirements

Status: draft for user review. This is not approval to implement. Product scope is agreed in principle; details, dependencies, and acceptance criteria below remain proposed.

## Goal and scope

A personal learning system inside Hermes that connects conceptual study from books/papers with investigation of existing projects and hands-on implementation. Desktop, web, and ordinary agent chat access one server-owned learning record. One canonical deployment/profile; no multi-user administration.

## Functional requirements

### R1. Start and manage a track

Create a track from a learning goal or selected source. Propose objectives and prerequisites for learner approval; allow revisions, pausing, and archiving. Persist a next-activity pointer independently of a chat session.

Acceptance: create through a tool, open in both UIs, start a new chat, and resume the same activity by track ID.

### R2. Ground learning in sources

Attach source metadata and allowed local content for books, papers, repositories, and notes. Preserve document section/page locators when available and repository commit/file locators. Distinguish quoted/source-supported statements from tutor interpretation. Expose extraction failures rather than inventing references. Initial support is curated text/Markdown and pinned repository excerpts; broader PDF extraction is conditional on a separate probe.

Acceptance: follow an explanation reference to the stored excerpt and locator. An unavailable locator is explicitly reported.

### R3. Support concept study and practical investigation

Offer explanation, prediction, guided source/code tracing, exercises, and small build/transfer tasks. Let the learner choose explain-first or attempt-first per activity; the global default is unresolved. Help is available on demand. Ordinary work chat does not silently enter teaching mode.

Acceptance: a lesson connects a concept to a source and a practical task; requesting a hint changes the recorded assistance level.

### R4. Provide visual learning workspaces

Desktop and web expose a track overview and an activity workspace with source, visualization, practice, and progress views. Initial visual support includes controlled diagrams and one step-through sequence/algorithm example. Each visual has a text alternative and source references where applicable. Avoid arbitrary model-authored executable code.

Acceptance: both real host plugins render the same saved diagram, support step controls and resizing, and remain usable by keyboard. Reject malformed diagram data and render a recoverable error.

### R5. Record evidence honestly

Record original answer, activity/objective, provenance, assistance, assessment method, feedback, and uncertainty. Separate conceptual evidence from practical results. Viewing a lesson or passing an agent-written test does not automatically establish independent mastery. Allow an assessment to be disputed and superseded without erasing history.

Acceptance: save an assisted attempt, challenge its grade, and inspect the original and corrected assessments from another client.

### R6. Schedule review

Provide a simple inspectable due-review queue based on saved attempts and learner adjustments. Allow deferral and manual correction. Do not present review heuristics as calibrated scientific probabilities.

Acceptance: fixed-clock tests cover due items, deferral, and repeated submissions; all interfaces agree on the due queue.

### R7. Expose agent tools and skills

Provide descriptive English tools for track lookup/creation, next activity, source retrieval, attempt submission, progress, and review. Bundle teaching skills for grounding, progressive hints, assessment uncertainty, and transitions to experiments. Text conversations support essential actions without requiring a rendered widget.

Acceptance: complete a text-only activity using registered tools and verify its saved state through both UIs. Verify tools remain available in the intended messaging runtime.

### R8. Maintain cross-client consistency

The shared learning service owns all durable changes. API and tools call the same policies. Idempotency prevents duplicate attempt creation; revisions detect competing edits. Refresh on reconnect. An acknowledgment means data committed, not merely that a prompt was queued.

Acceptance: duplicate submission stores one attempt; stale edit reports a conflict; disconnected clients do not show unsaved work as saved.

### R9. Protect and recover personal data

Keep records/artifacts outside source control on the deployed backend. Enforce host authentication, profile/connection scoping, safe paths, and content validation. Disclose external model processing. Provide export and backup/restore guidance. Never execute imported repository code automatically.

Acceptance: unauthorized API access fails, switching profile/backend does not leak prior cached data, malicious artifact paths fail, and restore recovers a track plus its referenced artifacts.

## Delivery stages

1. Feasibility spike: prove a visual and an attempt traverse tools, backend, desktop, and web.
2. First usable slice: track creation, curated sources, study/practice, evidence, minimal review, and cross-session resume on all surfaces.
3. Improve source extraction and visualization breadth after actual use. No commitment to a universal parser, complex graph UI, or advanced memory model.

## Non-functional requirements

Use supported host extension points, no DOM scraping or core fork. Document tested host versions and separate desktop-client/backend installation. Show loading, error, empty, stale, and disconnected states. Preserve theme compatibility and readable narrow layouts. Bound model/tool work and record available usage metadata; do not promise fixed costs or zero retries. Test migrations, concurrency, lifecycle cleanup, and recovery.

## Out of scope

Multiple users/roles, classroom collaboration, billing, offline write synchronization, cross-server replication, arbitrary-code sandbox infrastructure, autonomous mining of all chats, calibrated mastery claims, exact inline UI parity, and full book/paper parsing in the first slice.

## Open decisions

- Teaching default and degree of learner-directed navigation.
- Initial parser and supported source formats after the curated-text slice.
- Supported host versions and concrete messaging platform for validation.
- Exercise execution isolation if later required.
- License and distribution policy; public visibility alone is not an open-source license.
- Source storage/retention limits and deletion policy.

# Draft requirements

Status: revised draft for user review. Documentation changes do not authorize product implementation, plugin installation, or service restarts. Agreed product scope is preserved; detailed policies below require review.

## Goal and scope

A personal learning system inside Hermes that connects conceptual foundations from books/papers to repository investigation and hands-on projects. Desktop, web, and ordinary agent chat share server-owned learning state. Use one canonical deployment/profile. Both goal-first and source-first entry are required. Visualization and usable source navigation are core.

## R0. Content authorship and assessment ownership

Activities, visualizations, and assessments record author kind and provenance: learner, chat agent, self-assessment, or explicitly configured service-model operation. An assessment identifies its method and the activity/rubric version used.

For the first usable slice, a chat agent can author activities through tools and a learner can add curated material. UI submissions commit without requiring an active chat and enter `awaiting_assessment`. The learner can self-check against a rubric or request agent review of pending attempts in chat. These are separate assessment records, not interchangeable grades. Service-side inference is a later option until host inference, cost, retries, and lifecycle are probed; it is not silently invoked on submit. UI actions must explain when they hand off to chat rather than implying automatic generation.

Acceptance: submit in web with no chat open; verify pending status in desktop. Self-assess, then request agent review from a fresh chat. Both assessments reference the same attempt and retain their author/method.

## R1. Start and manage a learning track

Create from either a goal or selected source. For source-first, curated excerpts plus metadata are sufficient initially; automatic whole-book analysis is not required. Propose objectives/prerequisites for approval. Permit revision, pausing, and explicit archiving. Persist current objective, activity, and next action independently of any chat session.

Acceptance: create a goal-first and a source-first track; open both in desktop/web. Resume an in-progress activity from a new chat using its stable identifier.

## R2. Source grounding and disclosure

Attach books, papers, repositories, and notes with citation metadata, origin, edition/commit when applicable, stored excerpt hash, and locators. Initial input is curated text/Markdown and pinned code excerpts. Do not require a repository clone or automatic network ingestion. Broader PDF extraction, original figures, and exact page navigation require separate probes.

Direct quotes must match stored excerpts under a documented conservative normalization policy. A match proves text correspondence, not correctness or entailment. Reject a failed quote claim or retain it visibly as unverified; never silently relabel it as valid interpretation. Distinguish direct quote, source-supported explanation, and tutor interpretation. Show missing locators and extraction errors explicitly.

Each source has an explicit model-sharing policy: metadata-only, selected-excerpts, or full-text. Default to selected-excerpts for curated source content; never automatically expose an entire uploaded book. Metadata-only source text must be blocked from agent and service-model retrieval, including derived summaries/visuals containing protected text. UI must explain that text retrieved into chat may go to its model provider and conversation history. This policy cannot retract previously disclosed content or text pasted directly into chat.

Acceptance: follow a reference to the stored excerpt with edition/commit and highlighted span when available. A fabricated quote fails verification. Metadata-only content and protected derivatives cannot be retrieved by model-facing tools. No copyrighted content is committed to the public repository.

## R3. Learning activities and assistance

Support explanation, prediction, source/code tracing, and small practical tasks connecting concepts to implementation. The first reusable activity templates are explanation, prediction, and trace; build tasks can be briefs completed outside the plugin with submitted artifacts/reflections. Imported code is never executed automatically.

Let the learner choose explain-first or attempt-first per activity; no personal default is established. Provide progressive help and explicit reveal controls. Record assistance as events when delivered: none, nudge, targeted-hint, worked-step, full-solution-shown. Reading a source is a separate context flag, not automatically a penalty. Agent-generated help must be checkpointed before being represented as durably recorded; uncertainty in capture stays visible.

Acceptance: request a hint in chat, close it, submit in web, and observe that the assistance history persists. A practical activity includes a conceptual question and practical evidence without treating either as proof of the other.

## R4. Visual learning workspaces

Desktop and web provide a track overview with resume/next-action context and an activity workspace for source, visualization, practice, and evidence. Provide loading, empty, error, stale, and disconnected states; readable narrow layouts, theme compatibility, keyboard controls, and text equivalents.

Store model-authored visuals as schema-versioned structured data only. Controlled components render SVG/HTML; do not accept executable model-provided SVG, HTML, JS, or CSS. Validate participant/step references, allowed URLs, label sizes, and total complexity. Escape labels. Derive a factual step-list alternative from the same data; optional explanatory prose remains separate. Record authorship, source references, and review status. Structural validation must not be presented as conceptual verification.

Initial rich visual support is one step-through sequence component. Hide future prediction steps until submission/reveal when the activity requires it. Imported source images are a separate inert artifact type, not executable diagrams.

Acceptance: both real host plugins render the same saved diagram with working steps, resize, theme, and keyboard navigation. Unknown schema, missing references, excessive payloads, and injection labels are rejected or safely displayed without disabling the workspace. Messaging receives a usable text equivalent.

## R5. Evidence and assessment validity

An assessable activity stores prompt, criteria/key points, and version before opening an attempt. Existing attempts retain that version when an activity changes. Normal activity retrieval excludes keys/solutions until submission or explicit reveal. Reveals are server-recorded assistance events. Document that an authoring agent may already know its key inside the same conversation; the gate is not model-memory isolation.

Store submitted answer, objective/activity version, capture channel, assistance history, method, criterion-level feedback, uncertainty, and provenance. Distinguish `ui_direct`, `chat_relayed`, and host-verified capture when proved available. Skills require verbatim relay. Do not claim raw-message verification until the host probe passes. Missing or unverified assistance capture remains unknown rather than independent.

Present conceptual evidence separately from practical outcomes. Evidence types include explanation, recall, prediction, trace, transfer, and practical work. Record elapsed time for later retrieval without asserting a scientifically established threshold. No single mastery percentage or universal definition of independence is required. Viewing a lesson, self-rating, or a passing agent-written test alone cannot establish independent understanding.

Allow disputes and append-only superseding assessments, preserving originals. After commit, show answer and criteria side by side. Uncertain grading can remain ungraded. A corrected assessment recomputes derived review state without deleting historical evidence.

Acceptance: pre-attempt tool/API output contains no key. Hint/reveal changes assistance. A chat-relayed answer is labeled in both UIs. Criteria existed before the attempt. Dispute and correction remain visible, including their effect on future review.

## R6. Review and continuation policy

Maintain a simple, inspectable review queue per objective. Link each due item to evidence and explain its scheduling reason. Allow deferral and manual adjustment. Pin a versioned scheduling policy with fixed-clock tests before implementation. Intervals and evidence thresholds are proposed heuristics, not calibrated forgetting or mastery estimates. Review activities should permit a different example/context rather than requiring exact prompt repetition.

Acceptance: due items, deferral, corrected assessments, and repeated requests behave deterministically under a fixed clock; all interfaces return the same queue and reasons.

## R7. Agent tools, skills, and interface transitions

Provide descriptive English tools for track discovery/creation, learning context, source retrieval, activities, assistance, attempts, assessments, evidence, and review. Skills guide source grounding, progressive hints, uncertainty, and saved checkpoints. Essential flows work without a visual widget.

Learning begins on an explicit request, skill invocation, or workspace action. Do not automatically mine or assess unrelated work chats. A resume-context tool builds current objective, last attempt/assessment, open questions or misconception notes, current activity, and due reviews from server state. Only committed events count as saved progress; general agent memory is not an alternative authoritative learning database.

Tool results include track/activity IDs, text equivalents, and an authenticated workspace URL when a public base URL is configured; never include credentials in links. Workspace provides a copyable resume prompt. Native desktop deep linking is optional until verified.

Acceptance: continue in chat B after activity in chat A; brief matches web/desktop. Complete a visual-bearing activity in messaging using text and then open the same saved activity in web. An unrelated work-chat fixture does not call learning tools. Validate actual registration/use in the selected messaging runtime, not just direct tool invocation.

## R8. Persistence, retries, and interrupted work

HTTP adapters and tools call one learning service. The server issues activity-run/submission identity before an attempt; retries reuse it. Same identity and same payload returns the existing result; changed payload under that identity returns a conflict. A deliberate repeat uses a new identity, even for identical answer text. Provide lookup to resolve uncertain submission outcomes. Do not rely on model-generated keys or answer-text/time-window deduplication alone.

Append attempts, assessments, and assistance events. Use transactional writes and targeted revision checks for editable objectives, activities, and corrections. Verify SQLite concurrency/migrations across actual host processes, using WAL/busy timeout and transactionally guarded migration or an equivalent demonstrated mechanism.

Local unsubmitted drafts are allowed, namespaced by store/profile/activity, labeled `draft: not submitted`, and never mistaken for server progress. No offline committed writes or cross-device draft synchronization initially. Protect private drafts, offer clearing, and document retention. Refetch on focus/reconnect and periodically while visible; initial target is within 30 seconds for changes from another client while connected, with immediate local invalidation after successful writes. Show stale state on failure.

Expose store identity, API/schema version, and compatible client versions. Clear scoped caches and show a store-changed notice when the canonical connection changes. Only initialize storage in the resolved plugin data location; fail loudly on invalid paths. Version incompatibility refuses unsafe writes.

Acceptance: duplicate retries store one attempt; changed-payload retry conflicts; intentional identical repeats store two. Parallel tool/UI commits succeed and concurrent startup does not double-migrate. Restore a local draft after reload. A stale client cannot silently overwrite an edited activity. A backend/store switch cannot appear as silently lost progress.

## R9. Privacy, trust, packaging, and recovery

Keep learning records and sources outside the code repository. Enforce authenticated remote routes and safe artifact paths; verify both direct and configured proxy access. Source text is untrusted data, not permission to call tools. Cap retrieval sizes and reject unsafe markup/links. State-changing tools validate invariants; destructive operations or overrides require explicit confirmation bound to the target/revision, rather than relying on source text or model assurances.

Document that prompt-injection mitigations and scripted tests reduce risk, not prove immunity. Imported content must not silently change objectives, assessments, or authorization. Do not execute imported code automatically. Distinguish trusted plugin code from learning content.

Publish a coordinated backend/dashboard/desktop compatibility contract without assuming one physical installation reaches remote clients. Record runtime-tested Hermes versions. Remote desktop deployment, lifecycle cleanup, and API authentication are release checks.

Provide export and consistent SQLite/artifact backup/restore. Archiving retains records and sources; deletion/purge is a separate confirmed action with a documented dependency/retention preview before it is enabled. Disclose external model processing, available usage, retry behavior, and latency; do not promise a fixed price or zero provider retries.

Acceptance: unauthorized GET/POST and malicious artifact paths fail. Source-injection fixtures cannot bypass mutation validation or confirmation. Incompatible clients refuse unsafe writes. Backup/restore recovers a track, evidence, and referenced artifacts. Host restart preserves committed state.

## Validation layers

- Deterministic service tests: fixed clock, evidence transitions, solution gating, policy enforcement, retry/conflict behavior, migrations, and malformed-data fixtures.
- Adapter contract tests: HTTP and tools exercise the same state transitions and errors.
- Scripted real-agent evaluations: explicit learning entry, verbatim relay, checkpoints, source-injection fixtures, and unrelated work chats. Report model/provider, failures, and observed reliability; these are not deterministic guarantees.
- Actual desktop/web/messaging checklist: rendering, auth, links, responsiveness, cross-client continuity, disconnect/reconnect, and persistence, recorded per tested release.

## Delivery stages

1. Feasibility: real desktop and web diagram, real messaging tools, shared authenticated store, retry safety, assistance continuity, and restart recovery. No standalone mockup substitutes for these probes.
2. First usable slice: both entry points, curated sources, rubric-backed activities, controlled sequence visual, pending/self/agent assessments, evidence, simple review, and resume across all three interfaces. Frontend delivery may be sequenced but desktop remains required and tested.
3. Extend ingestion and visual types after actual use. Add service-model operations only after their probe and a separate design decision.

## Out of scope

Multi-user accounts/roles, classrooms, billing, offline write synchronization, cross-server replication, arbitrary-code execution infrastructure, autonomous mining of chats, calibrated mastery claims, exact inline UI parity, and full book/paper parsing in the first slice.

## Decisions still needed

Before implementation: choose messaging runtime for the probe; specify the first scheduling policy and payload limits; prove host registration/auth/storage/rendering; establish confirmation mechanics. These are technical/specification choices, not permission to guess unsupported APIs.

Before release: supported host/client versions, license, source/draft retention and storage limits, export format, and deletion behavior. Explain-first versus attempt-first remains selectable per activity; a personal default is optional. PDF parsing and code execution are deferred, not prerequisites.

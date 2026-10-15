# Architecture proposal

Status: revised proposal for review, not implementation approval. [Requirements](requirements.md) define behavior and acceptance.

```text
Desktop plugin -------- HTTP API ----+
Web-dashboard plugin -- HTTP API ----+--> Learning service --> SQLite + artifacts
Hermes agent tools -----------------+
Teaching skills guide agent tool use
```

## Ownership

The learning service validates explicit tracking-context authorization, authoring, evidence, assistance events, review policy, source disclosure, and durable changes. Default ad hoc chats do not trigger plugin learning-record writes or automatic personal-track lookup. Merely loading a skill or opening an overview is not enrollment. HTTP and tools are adapters over this service. Skills guide teaching but do not bypass validation. Resolve the profile data path per operation, not at import time. Do not modify Hermes conversation tables.

Activities have immutable assessed versions and pre-attempt criteria. Agent-authored and learner-authored content are attributable. UI answers commit as awaiting assessment without a live chat. Self-assessment and agent review are separate records. Backend model inference is deferred pending a host-inference probe; the UI must explain chat handoffs.

Candidate entities: Exploration/LearningBrief, SourceRecommendation, Track, Objective, Source, SourceLocator, ActivityVersion, ActivityRun, AssistanceEvent, Attempt, Assessment, ReviewItem, Visualization, Artifact. An exploration can exist after explicit persistence opt-in but before any approved track; it stores learner-stated interests, assumptions, unresolved choices, candidate directions/materials, and approval status. Accepted recommendations are not automatically downloaded or authorized for model sharing. Misconception/open-question notes attach to objectives. Durable session references are optional provenance, not the resume mechanism.

## Storage and consistency

One server-local SQLite store plus artifacts. Demonstrate WAL/busy timeout and transactionally guarded migrations across host processes. Append attempts, assistance, and superseding assessments. Use targeted revisions on edits/corrections. Server-issued run/submission IDs make retries safe: same payload returns prior result, changed payload conflicts, explicit new attempt permits identical text. Provide lookup after uncertain delivery.

Store identity and API/schema compatibility are explicit. Refuse invalid storage paths and incompatible writes. Cache by store/profile and reset on connection changes. Local drafts are private, unsubmitted, and clearly labeled; they are not authoritative progress. Poll visible views within an initial 30-second target, refresh on focus/reconnect, and invalidate immediately after a local write. No WebSocket or distributed queue is required initially.

## Learning and visual flow

Explicit tracked entry/resume binds a store/profile and exploration/track to a conversation or workspace context, then fetches a server-derived resume brief, including an unfinished exploration when no track exists. Agent skills handle one-question-at-a-time discovery and source recommendation using host research tools; no new backend search or inference service is assumed. UIs show exploration/proposal/active states and hand off to chat when agent authoring is needed. Reference verification and access status are stored separately from learner approval. Discovery answers are not graded attempts. Check direction after the first activity before expanding the path. Source retrieval enforces model-sharing restrictions and returns labeled untrusted content. Attempts preserve capture channel and known/unknown assistance. Record hints/reveals before claiming they are saved. Gate solutions at tool/API boundaries while acknowledging the authoring agent may know them already.

Store visual data only as a bounded versioned schema. Fixed SVG/HTML components render escaped labels, step controls, source links, and a deterministic step-list alternative. Model-provided executable markup is disallowed. Schema validity does not imply semantic correctness. Original source figures are inert artifacts with provenance and distinct ingestion requirements.

## Ad hoc/tracked boundary

Ordinary chat can explain, explore, and visualize without invoking persistence. Tracking is scoped, visible, and revocable rather than inferred from learning vocabulary. Promotion previews selected earlier context, requires import approval, and creates no retrospective assessment. Track-path approval and source-sharing permissions remain separate.

Workspace has Start tracked learning/Resume/Leave actions; messaging announces entry/exit. Ad hoc side questions do not become attempts or revise objectives. Leaving or an explicit untracked exchange stops recording in that context until an explicit resume. Validate active context on writes and reject stale/late mutations after exit. Identify an actual host-authorized entry mechanism in the spike; a model-generated flag is not sufficient. Other chat contexts do not inherit consent automatically.

Do not persist ad hoc content into plugin records, including diagnostics disguised as learning state. Host conversation retention remains separate. Local unsubmitted drafts, source retrieval policies, and server-confirmed saving still apply within opted-in workflows.

## Integration and trust

Backend plugin, dashboard adapter, desktop adapter, and skills share contracts but have different SDK/delivery requirements. Remote backend installation is not frontend distribution. Prove authenticated routes, actual messaging registration, remote desktop access, and cross-process store ownership. Hooks/raw-user-message capture and native deep links remain unverified.

Use host authentication only after enforcement is tested. Validate mutations independently of model assurances; destructive operations/overrides require explicit target-bound confirmation. Protect source sharing, safe paths, draft retention, and artifact references. Do not execute imported code. Prompt-injection tests are regression checks, not immunity proofs.

Test backup/restore of database plus artifacts, interruption, duplicates, migrations, malformed visuals, profile/store changes, and plugin unload/reload. Publish only runtime-tested compatibility claims. No installation or restart is authorized by this document.

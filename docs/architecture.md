# Architecture proposal

Status: revised proposal for review, not implementation approval. [Requirements](requirements.md) define behavior and acceptance.

```text
Desktop plugin -------- HTTP API ----+
Web-dashboard plugin -- HTTP API ----+--> Learning service --> SQLite + artifacts
Hermes agent tools -----------------+
Teaching skills guide agent tool use
```

## Ownership

The learning service validates authoring, evidence, assistance events, review policy, source disclosure, and durable changes. HTTP and tools are adapters over this service. Skills guide teaching but do not bypass validation. Resolve the profile data path per operation, not at import time. Do not modify Hermes conversation tables.

Activities have immutable assessed versions and pre-attempt criteria. Agent-authored and learner-authored content are attributable. UI answers commit as awaiting assessment without a live chat. Self-assessment and agent review are separate records. Backend model inference is deferred pending a host-inference probe; the UI must explain chat handoffs.

Candidate entities: Track, Objective, Source, SourceLocator, ActivityVersion, ActivityRun, AssistanceEvent, Attempt, Assessment, ReviewItem, Visualization, Artifact. Misconception/open-question notes attach to objectives. Durable session references are optional provenance, not the resume mechanism.

## Storage and consistency

One server-local SQLite store plus artifacts. Demonstrate WAL/busy timeout and transactionally guarded migrations across host processes. Append attempts, assistance, and superseding assessments. Use targeted revisions on edits/corrections. Server-issued run/submission IDs make retries safe: same payload returns prior result, changed payload conflicts, explicit new attempt permits identical text. Provide lookup after uncertain delivery.

Store identity and API/schema compatibility are explicit. Refuse invalid storage paths and incompatible writes. Cache by store/profile and reset on connection changes. Local drafts are private, unsubmitted, and clearly labeled; they are not authoritative progress. Poll visible views within an initial 30-second target, refresh on focus/reconnect, and invalidate immediately after a local write. No WebSocket or distributed queue is required initially.

## Learning and visual flow

Explicit learning entry fetches a server-derived resume brief. Source retrieval enforces model-sharing restrictions and returns labeled untrusted content. Attempts preserve capture channel and known/unknown assistance. Record hints/reveals before claiming they are saved. Gate solutions at tool/API boundaries while acknowledging the authoring agent may know them already.

Store visual data only as a bounded versioned schema. Fixed SVG/HTML components render escaped labels, step controls, source links, and a deterministic step-list alternative. Model-provided executable markup is disallowed. Schema validity does not imply semantic correctness. Original source figures are inert artifacts with provenance and distinct ingestion requirements.

## Integration and trust

Backend plugin, dashboard adapter, desktop adapter, and skills share contracts but have different SDK/delivery requirements. Remote backend installation is not frontend distribution. Prove authenticated routes, actual messaging registration, remote desktop access, and cross-process store ownership. Hooks/raw-user-message capture and native deep links remain unverified.

Use host authentication only after enforcement is tested. Validate mutations independently of model assurances; destructive operations/overrides require explicit target-bound confirmation. Protect source sharing, safe paths, draft retention, and artifact references. Do not execute imported code. Prompt-injection tests are regression checks, not immunity proofs.

Test backup/restore of database plus artifacts, interruption, duplicates, migrations, malformed visuals, profile/store changes, and plugin unload/reload. Publish only runtime-tested compatibility claims. No installation or restart is authorized by this document.

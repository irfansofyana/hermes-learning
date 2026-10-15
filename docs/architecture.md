# Architecture proposal

Status: proposed design, not an implementation specification.

```text
Desktop plugin -------- HTTP API ----+
Web-dashboard plugin -- HTTP API ----+--> Learning service --> SQLite + artifacts
Hermes tools -----------------------+
Teaching skills guide agent use of tools
```

## Boundaries

The learning service owns validation, state transitions, evidence, review policy, and persistence. HTTP handlers and tools are adapters over the same service. Skills describe teaching behavior; they cannot authorize unvalidated state changes.

Use one server-local SQLite store initially, with migrations and transactional writes, plus an artifact directory. Resolve storage through the active Hermes profile rather than an import-time global. Do not write directly to Hermes session tables. Attach durable session references as optional provenance; a track survives new chats.

Proposed entities: Track, Objective, Source, SourceLocator, Activity, Attempt, Assessment, ReviewItem, Visualization, Artifact. Attempts record assistance. Assessments can be uncertain, disputed, or superseded. Diagram records contain a schema version, safe structured content, explanation steps, source references, and a text alternative.

## Client consistency

All clients use the canonical backend. Use idempotency keys for attempt submissions, revisions for competing edits, and read-back after writes. Keep only presentation preferences in client storage. Re-fetch on reconnect; do not claim offline work is saved. Polling is an acceptable first implementation; do not require a WebSocket.

## Packaging and integration

Provide agent tools and bundled skills, a dashboard frontend/backend adapter, and a desktop frontend adapter. Frontend SDKs differ. A remote backend install does not automatically install the desktop UI on the client. Test authenticated remote routing and active-profile changes. Determine supported versions with runtime probes before documenting installation.

## Safety and operations

Reuse host authentication where supported and test enforcement. Keep sources private by default, sanitize generated SVG/HTML, treat imported text as untrusted content, bound upload sizes and paths, and disclose outbound model processing. No automatic execution of repository code. Plugin code itself is trusted code, not a sandbox. Require explicit approval for host restarts or installation during a spike.

Back up SQLite and artifacts consistently. Test restore, migrations, duplicate requests, stale clients, and interrupted submissions. No separate distributed service or queue until measured requirements justify one.

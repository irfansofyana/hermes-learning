# Integrated Learning rebuild

Status: proposed for review. Implementation will happen on `main`, as requested.

## Product intent

Hermes Learning turns a topic, a project, or supplied material into lessons the learner can use immediately. The learner stays inside the plugin to read, practise, ask the tutor, and continue later. The AI explains and demonstrates first. It does not begin with a discovery interview.

The current command handoff, separate resume message, path-approval ceremony, and manual activity-authoring forms must no longer be prerequisites for learning. Existing records remain readable.

## The experience

### Start with one input

The home page asks **What do you want to learn or build?** It accepts a topic, a project description, or a request combining these with sources. Example: “Build a job queue in Go using these notes and this repository.”

The learner can attach multiple text, Markdown, and code files, paste material, or add HTTP(S) source/repository links. Show each attachment and its read status. Failed or unsupported files are identified individually, with the option to remove or replace them; never silently discard them. Binary documents such as PDFs are explicitly unsupported in this first rebuild, rather than being presented as successfully read.

Level defaults to beginner and can be changed in an optional control. Background and other preferences are optional. The primary action is **Generate learning path**. A short note beside it explains that the path, supplied material, and progress will be saved and that shared material is sent to the configured Hermes model.

Generation starts with the information supplied. For ordinary ambiguity, choose a reasonable starting point and display a brief editable assumption. Ask a clarification only when the request is unusable without it, such as having no readable material and no topic. Do not require a questionnaire, an initial quiz, or a second path-approval step.

### Generate useful material first

Create an ordered outline and a complete first lesson. Display the outline as soon as it is durably saved, then open the first lesson when ready. Later lessons are generated when selected and saved for subsequent visits. This keeps the initial wait and model usage bounded without presenting empty headings as completed lessons.

Every lesson contains an explanation, a concrete example or walkthrough, and an optional practice step. Appropriate diagrams use the existing bounded visual schemas. Reading and understanding a lesson must not require submitting an answer. Controls include **Explain simply**, **Show an example**, **Ask a question**, and **Next lesson**.

For project requests, the outline consists of milestones with observable deliverables. A build project should progress toward a working result. An existing repository should be taught through its structure, important code paths, and small suggested changes. The tutor must distinguish suggested commands and expected results from code it actually ran.

### Learn in one workspace

Desktop layout:

- A compact left sidebar contains the path and completed/available lessons.
- The main reading area contains the selected lesson, references, visuals, and optional practice.
- A collapsible tutor panel contains the conversation and message composer for that path.

On narrow screens, the outline and tutor become accessible panels; the lesson retains readable width. Switching panels preserves drafts and scroll position. The UI follows the host's light/dark mode and supports keyboard navigation, labelled controls, and reduced motion.

Sources and detailed progress remain accessible as secondary views. They do not dominate the first-use experience. Existing evidence, disputes, and review records remain available without forcing their administration into every lesson.

### Continue automatically

Selecting **Continue** opens the last selected lesson and restores its path's tutor conversation. A user action to generate or continue establishes the learning context internally. Ordinary page mounting only reads data; it does not start model work. No slash command or context ID appears in the normal flow.

Keep one durable Hermes conversation per path, scoped to the connected backend, profile, and Learning store. Runtime session identifiers can change after resume or compression; use durable identifiers for continuity. Changing profiles must never send a draft to the previous or newly selected path accidentally.

## Embedded tutor

Reuse the configured Hermes model, credentials, agent, and learning tools. Do not introduce a separate provider form or direct browser-to-model calls.

The plugin supplies the active learning context, selected lesson, and relevant references to the tutor. It must not copy every attachment into every message. Source text is retrieved through the existing disclosure checks. Context IDs stay out of visible lesson content and user-facing messages.

The tutor teaches directly. Questions are optional exercises or necessary clarifications, not the default response to every request. Requesting a simpler explanation must produce that explanation. Requesting a hint must return a hint without leaving Learning.

Show streaming responses and concrete states: preparing, generating, waiting for permission, stopped, and failed. Provide Stop. Surface host clarification and tool-approval requests inside the tutor panel; never automatically approve them. A missing provider or backend connection produces an actionable error and preserves the learner's input.

Persist the binding between a path and its Hermes conversation in Learning storage. Hermes remains authoritative for conversation history; Learning remains authoritative for paths, lessons, supplied sources, and practice evidence. Do not write directly to Hermes conversation tables.

## Source and project handling

Supplied files are displayed as material, not executed. Keep source titles, file paths or URLs, selected text, retrieval status, and locators. Enforce per-file and aggregate size limits before starting a model turn, using the existing text import limits as a baseline. Oversized input must offer a clear correction rather than silently truncating.

Links are references until successful retrieval. Use Hermes's available reading/research tools for explicitly supplied links and repositories. Missing tools, authentication failures, inaccessible repositories, and unsupported content remain visible. The first usable lesson may proceed from accessible material, with its limitations stated.

Repository learning is read-only by default. Building a project means teaching milestones and reviewing supplied work; automatic execution, installation, and modification of the learner's repository are not part of generation. Host tool permission requirements remain in force.

Lessons cite the actual material used. Distinguish source-supported statements from the tutor's additional explanation. An inaccessible link cannot be described as read, and generated citations cannot establish verification. Imported instructions are untrusted source material.

## Storage and generation contract

Extend the existing SQLite service additively. Preserve the old tracks, contexts, activities, submissions, and assessments. Existing tracks can be continued in the rebuilt interface; new lesson records do not reinterpret historical answers or erase evidence.

New records cover:

- Path setup: topic/project intent, level, assumptions, and source references.
- Ordered lesson outline and generated lesson revisions, including source references and optional visual/activity links.
- Generation jobs with request identity, status, failure details, and published results.
- Tutor binding with durable session ID and backend/profile/store scope.
- Reading position and explicit lesson completion, separate from assessed practice.

New UI-owned generation actions establish a bounded request. Model-facing publishing tools may publish only to that request and path. They cannot start or resume unrelated tracking. Generation authorizes creating the requested path and lessons without an additional approval ceremony; materially changing the user's scope remains a separate user action.

Validate model-produced structures at the service boundary. Save each valid outline/lesson atomically, with idempotent publication and revision guards. Partial generation remains resumable. A malformed response leaves a visible failure rather than an apparently successful empty course.

Lesson reading/completion is not mastery. Quizzes and submitted practice continue to use the existing evidence, assistance, and assessment rules. A normal chat question must not be recorded as an assessed attempt.

## Host integration

Source inspection establishes available interfaces, not a completed runtime test:

- Desktop: public `host.request` and `host.onEvent`; gateway operations include `session.create`, `session.resume`, `prompt.submit`, and `session.interrupt`. Existing Hermes plugins use these for off-screen agent conversations.
- Dashboard: the public SDK exposes authenticated `buildWsUrl` and JSON fetch; the dashboard's chat client uses the `/api/ws` JSON-RPC gateway. Use SDK authentication and base-path handling rather than reading tokens directly.
- Both adapters implement a shared transport contract for request/response, streaming events, connection status, and cleanup. UI components do not depend on private host imports.

Session restoration must reconcile persisted history with streamed events. Check the host's current event and approval schemas during implementation. Do not resend an uncertain prompt automatically: first reconcile whether it was accepted. A duplicate retry must not create two lessons, two paths, or duplicate submitted answers.

The standalone preview retains a deterministic simulated transport for UI tests, explicitly labelled as a preview. Production bundles use only real host transports and never silently substitute canned AI output.

## Implementation boundaries

Keep the repository root installable from `main` and commit rebuilt desktop/dashboard bundles. Do not reintroduce ZIP distribution. Keep the README focused on the product and installation.

Implement in these dependent units:

1. Additive path/lesson/generation/session-binding storage and validated APIs/tools.
2. Shared tutor controller plus Desktop and dashboard gateway transports, including recovery and permissions.
3. Generation-first home, lesson workspace, embedded tutor, and source/project input.
4. Updated teaching guidance, compatibility documentation, migration checks, and actual-host verification.

Do not install into or restart the daily Hermes profile. Use isolated homes and temporary learning stores for verification.

## Acceptance checks

1. Enter a topic and click Generate once. An ordered path and a real first lesson appear without an interview, slash command, or manual path approval.
2. Supply a project goal plus multiple supported files. Generated milestones use those materials and provide locators back to them.
3. Supply an inaccessible repository link or an unsupported file. The UI reports exactly what was not read and preserves other usable inputs.
4. Ask for a simpler explanation or hint from a lesson. A real Hermes response streams inside the plugin; the main chat route never opens.
5. Close and reopen Learning, then Continue. The selected lesson and correct conversation return without a copied command.
6. Stop generation, disconnect during a response, or retry after an uncertain acknowledgement. Saved results survive and no duplicate job or prompt is submitted silently.
7. Switch backend/profile during a turn. Old events and pending replies cannot attach to a different store or path.
8. A tool permission or clarification request is visible and actionable inside the plugin.
9. Existing tracks, attempts, sources, and assessments still load. New reading progress does not claim mastery or change old evidence.
10. Verify both real Desktop and dashboard in isolated profiles, then validate installation from a clean repository checkout. Report untested surfaces explicitly.

## What this replaces

This design supersedes the handoff and discovery-first portions of the existing architecture and teaching guidance. It retains source disclosure, immutable evidence, explicit user initiation of saving/model work, and truthful progress reporting. Implementation must update conflicting documentation and prompts together with the UI.

# Draft requirements

> Historical design: the legacy records interface, manual approvals and chat-command flow are retired. Current behavior is documented in [Learner flows](user-flows.md). Old records are discarded rather than migrated.

Status: revised draft for user review. Documentation changes do not authorize product implementation, plugin installation, or service restarts. Agreed product scope is preserved; detailed policies below require review.

## Goal and scope

A personal learning system inside Hermes that connects conceptual foundations from books/papers to repository investigation and hands-on projects. Desktop, web, and ordinary agent chat share server-owned learning state. Use one canonical deployment/profile. Both goal-first and source-first entry are required, including vague-topic discovery when the learner has neither a concrete outcome nor a source. Visualization and usable source navigation are core. Ordinary educational chat remains ad hoc by default; plugin-owned persistence requires the explicit opt-in defined in R10.

## R0. Content authorship and assessment ownership

Activities, visualizations, and assessments record author kind and provenance: learner, chat agent, self-assessment, or explicitly configured service-model operation. An assessment identifies its method and the activity/rubric version used.

For the first usable slice, a chat agent can author activities through tools and a learner can add curated material. UI submissions commit without requiring an active chat and enter `awaiting_assessment`. The learner can self-check against a rubric or request agent review of pending attempts in chat. These are separate assessment records, not interchangeable grades. Service-side inference is a later option until host inference, cost, retries, and lifecycle are probed; it is not silently invoked on submit. UI actions must explain when they hand off to chat rather than implying automatic generation.

Acceptance: submit in web with no chat open; verify pending status in desktop. Self-assess, then request agent review from a fresh chat. Both assessments reference the same attempt and retain their author/method.

## R1. Start and manage a learning track

### Discovery before a concrete goal

Accept a vague topic such as "I want to learn distributed systems, but I know nothing about it" without requiring an outcome, vocabulary, prior knowledge, or a source. Explore motivation, relevant background, examples that sparked interest, desired depth, and practical constraints as useful context, not a mandatory questionnaire.

Ask one focused question at a time and adapt to the answer. Probe intent rather than grade knowledge the learner has not studied. If the learner cannot choose, provide a short plain-language orientation and a few concrete directions with examples. Explain unfamiliar terms before asking the learner to choose between them. Accept uncertainty as a valid answer. Distinguish self-reported background from demonstrated evidence; discovery does not award mastery or create failed attempts.

Allow "suggest a starting point" at any time. The agent then proposes a small reversible direction with explicit assumptions, or offers an exploratory activity. A clear existing goal/source can skip discovery; do not force an interview every time. Do not generate an exhaustive curriculum before the learner has found a useful direction.

### Agree on a provisional learning brief

Summarize the learner's interest, reason for learning, stated background and unknowns, a first useful outcome, constraints actually expressed, and tentative prerequisites. Separate learner statements from agent assumptions. Invite correction, then propose a small path and starting materials under R2 for approval. For source-first, curated excerpts plus metadata are sufficient initially; automatic whole-book analysis is not required. An exploratory activity can be approved without committing to a full track.

Only after opting into tracked learning under R10, save discovery notes, unresolved choices, recommendation status, and approval state in a backend-owned exploration record that can later link to a track. Before opt-in, discovery can happen in ordinary chat without plugin writes. It can resume across chats/clients before a track exists. The UIs distinguish `exploring`, `path proposed`, and `active learning`; these are product states, not assumed host SDK features. A learner's explicit agreement is needed before treating a proposed direction as approved.

After the first activity, check whether the direction matches the learner's interest. Permit scope changes without erasing discovery or earlier evidence. Allow revision, pausing, and explicit archiving. Persist current objective, activity, and next action independently of any chat session.

Acceptance:
- Start with a broad topic and no knowledge/source. The agent asks an intent question, uses the answer, explains options when needed, and proposes a small brief, materials, and first activity for approval.
- Reply "I don't know" and then "suggest a starting point." The agent offers a reversible default with labeled assumptions rather than repeating the questionnaire or claiming the learner approved it.
- Start with a precise goal or source; skip unnecessary discovery while retaining path approval.
- After explicit opt-in, pause discovery in chat A and resume its saved record in chat B and desktop/web without inventing missing answers. Without opt-in, the same discovery creates no plugin exploration, recommendation, or progress record.
- Complete an exploratory activity, reject its direction, and revise the brief without losing prior evidence or treating the exploration as failed mastery.

## R2. Source discovery, grounding, and disclosure

### Recommend starting materials

The learner need not supply materials. Using the provisional brief, the agent proposes a small starting set with a reading order and a specific first section/excerpt/activity. Explain why each material fits, its prerequisites and difficulty, and whether it contributes a foundation, an implementation example, or practice. Prefer a few usable choices over a large resource dump. Do not force a project or paper into every track when it would not help the agreed objective.

Verify proposed references and relevant access information through available retrieval tools before marking them verified: title/author or repository identity, edition/commit when relevant, working source link, and whether the relevant content is publicly accessible, paid, or not yet checked. Record provenance and verification status. If a tool or source is unavailable, disclose the limitation, keep the candidate unverified, and offer a usable alternative. Do not invent chapter numbers, quotations, access claims, or a reading assignment from metadata alone; a specific passage assignment requires inspected content or a learner-provided locator clearly labeled as such.

Recommendations remain candidates until the learner accepts or substitutes them. Recommending a book does not purchase, download, attach full text, or grant model-sharing consent. Material discovery can run in chat with host research tools; it does not require a new backend search service or service-side inference. In ad hoc chat, recommend materials without persisting plugin candidates or attaching sources. In an opted-in context, UIs show the saved brief and recommendations and provide the chat handoff when no generation path is available. Guided discovery and source recommendation are required in the first usable slice, while automatic full-document ingestion remains deferred.

### Ground and protect attached material

Attach books, papers, repositories, and notes with citation metadata, origin, edition/commit when applicable, stored excerpt hash, and locators. Initial input is curated text/Markdown and pinned code excerpts. Do not require a repository clone or automatic network ingestion. Broader PDF extraction, original figures, and exact page navigation require separate probes.

Direct quotes must match stored excerpts under a documented conservative normalization policy. A match proves text correspondence, not correctness or entailment. Reject a failed quote claim or retain it visibly as unverified; never silently relabel it as valid interpretation. Distinguish direct quote, source-supported explanation, and tutor interpretation. Show missing locators and extraction errors explicitly.

Each source has an explicit model-sharing policy: metadata-only, selected-excerpts, or full-text. Default to selected-excerpts for curated source content; never automatically expose an entire uploaded book. Metadata-only source text must be blocked from agent and service-model retrieval, including derived summaries/visuals containing protected text. UI must explain that text retrieved into chat may go to its model provider and conversation history. This policy cannot retract previously disclosed content or text pasted directly into chat.

Acceptance: a vague-topic learner receives a short ordered source recommendation tied to the agreed direction, with reasons, prerequisites, verified references or explicit unverified status, and a concrete inspected starting passage when available. Simulate failed retrieval: the agent does not fabricate a reference or claim inaccessible content was read. Declining a candidate leaves it unapproved and attaches no source content. Follow an accepted reference to its stored excerpt with edition/commit and highlighted span when available. A fabricated quote fails verification. Metadata-only content and protected derivatives cannot be retrieved by model-facing tools. No copyrighted content is committed to the public repository.

## R3. Learning activities and assistance

Support explanation, prediction, source/code tracing, and small practical tasks connecting concepts to implementation. The first reusable activity templates are explanation, prediction, and trace; build tasks can be briefs completed outside the plugin with submitted artifacts/reflections. Imported code is never executed automatically.

These recording and assessment rules apply within opted-in tracked contexts. A direct question or untracked side question must not become an attempt merely because its topic matches a track. Let the learner choose explain-first or attempt-first per activity; no personal default is established. Provide progressive help and explicit reveal controls. Record assistance as events when delivered: none, nudge, targeted-hint, worked-step, full-solution-shown. Reading a source is a separate context flag, not automatically a penalty. Agent-generated help must be checkpointed before being represented as durably recorded; uncertainty in capture stays visible.

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

Provide descriptive English tools for exploration/learning-brief persistence, source recommendation status, track discovery/creation, learning context, source retrieval, activities, assistance, attempts, assessments, evidence, and review. Skills guide adaptive intent discovery, source selection/verification, source grounding, progressive hints, uncertainty, saved checkpoints, and default Humanizer editorial behavior under R11. Essential flows work without a visual widget.

Tracked learning begins only through an explicit opt-in or resume action under R10. Generic phrases such as "help me learn this" and loading a teaching skill are not by themselves consent to persist learning records. Do not automatically mine or assess unrelated work or educational chats. A resume-context tool returns saved discovery context and unresolved choices when no track is approved; for active tracks it returns the approved brief, current objective, last attempt/assessment, open questions or misconception notes, current activity, and due reviews from server state. Only committed events count as saved progress; general agent memory is not an alternative authoritative learning database.

Tool results include stable exploration IDs before track creation and track/activity IDs when available, text equivalents, and an authenticated workspace URL when a public base URL is configured; never include credentials in links. Workspace provides a copyable resume prompt. Native desktop deep linking is optional until verified.

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

## R10. Ad hoc by default; explicit tracked-learning opt-in

### Decide by persistence intent, not subject or depth

Ordinary chat is ad hoc unless the learner explicitly starts or resumes tracked learning. Explain concepts, discuss papers, offer discovery questions, and provide useful visuals without requiring enrollment. A long educational discussion, learning-related vocabulary, a source upload, topic similarity to an existing track, installing/loading a plugin or skill, or merely opening a workspace does not authorize learning-record writes.

In ad hoc mode, create no plugin explorations, briefs, candidate materials, source attachments, attempts, assessments, objectives, or reviews; do not automatically fetch a matching personal track to personalize the answer. This restriction concerns plugin-owned state. Normal Hermes history, files created at the learner's request, provider processing, and host retention are separate and must not be described as private/incognito or unsaved everywhere. Plugin diagnostics must not covertly store ad hoc content as learning data.

Do not ask "ad hoc or tracked?" before every educational answer. Answer the question first unless clarification is necessary to help. At a natural transition toward ongoing study, an optional single offer can explain the benefits of saving a track. After a decline, suppress further unsolicited offers in that conversation unless the learner reopens the topic of tracking. Offering or declining creates no plugin learning record.

### Enter and promote explicitly

An explicit "start/save this as a learning track," "continue my named track," or a clearly labeled Start tracked learning/Resume action can authorize entry. Ambiguous requests remain ad hoc; clarify before writes when the learner appears to want saved progress. A specifically labeled skill command may be an entry action only if its tracking behavior is explained; automatic skill selection is not consent.

For ad hoc-to-tracked promotion, show a proposed brief and the selected context/materials to import, and obtain approval for that import. Do not copy the full conversation automatically or retrospectively grade it. Mark imported notes as prior discussion, not independent learning evidence. If the learner explicitly starts a new tracked exploration with no prior import, do not require a redundant second enrollment confirmation. Tracking consent, importing earlier content, approving a learning path, and model-sharing consent are separate scopes.

Bind entry to a stable store/profile, exploration/track, and conversation or explicit workspace activity context. Display the active context in desktop/web and announce entry/resume in messaging. Membership is not global across all chats. Another chat begins ad hoc unless explicitly resumed there. Opening an overview reads existing records but does not activate tracking for unrelated conversations.

### Side questions, pause, and exit

Within a tracked context, an explicit answer to the pending tracked activity may be recorded under its agreed workflow. A side question does not automatically change objectives, create an attempt, or earn assessment evidence. "Just explain this; don't track it" suspends learning-record updates for the exchange. If it is unclear whether text is an activity answer or a side discussion, clarify before saving it as evidence.

Provide Leave tracked learning in desktop/web and an equivalent natural-language action in chat. Leaving stops new recording in that context without deleting/archiving the track. Do not automatically resume recording after an untracked exchange; announce and obtain an explicit resume action. Preserve already committed data; do not claim leaving retracts it. Other deliberately active workspace contexts remain independent and clearly labeled.

Mutating tools/API handlers require a valid active tracking context created by an explicit entry action. Pause/exit invalidates that context for future writes, including late or queued submissions. Return a recoverable status and preserve committed data; never silently reactivate. Resolve the host mechanism for identifying user-authorized entry in the feasibility probe. A model-supplied boolean alone is insufficient proof; do not claim prompt instructions guarantee opt-in enforcement. A request to view a saved record is not consent to modify it.

Acceptance:
- Ask a concept question, discuss a paper, and run a long vague-topic discovery chat without opting in. Receive useful answers with no plugin learning-record writes and no automatic personal-track lookup.
- Decline a tracking offer, then ask more educational questions: no repeated unsolicited offer in that conversation and no persisted exploration.
- Promote selected ad hoc context after a preview: only approved context is imported, and no earlier text becomes an assessed attempt.
- Start an explicitly tracked exploration: persistence begins without a duplicate enrollment prompt, while path approval remains a separate step.
- While answering a tracked activity, ask an untracked side question. It creates no attempt or objective update; resume is explicit. A fresh unrelated chat remains ad hoc.
- Leave tracked learning, deliver a late submission using the old context, and verify rejection with no new learning records. Existing progress remains intact.
- Read a workspace overview without starting/resuming a track: no enrollment, assessment, or learning-progress mutation occurs. UIs and messaging make the active tracking context visible when one is entered.

## R11. Humanized teaching and editorial quality

Bundle the Humanizer skill as a default part of the plugin's teaching-skill package, with teaching-specific guidance in [Teaching quality](teaching-quality.md). It must not depend on a skill installed only in the developer's Hermes profile. Confirm source/version, license, and required attribution before copying or redistributing the skill; packaging and actual activation remain implementation work. Applying editorial guidance is not consent to tracking under R10.

Apply the guidance to discovery questions, explanations, materials recommendations, exercise wording, hints, assessment feedback, visual narration, and learning UI copy. When the plugin's teaching workflow is used in ad hoc chat, use the same quality standard without creating learning records. Do not globally rewrite unrelated Hermes work conversations.

Teach directly and specifically. Explain the mechanism and assumptions at the learner's level, use examples that clarify the current question, and preserve relevant limits/counterexamples. Avoid canned praise, staged introductions, empty summaries, inflated claims, repeated template sections, unnecessary jargon, and ornamental formatting. Do not equate natural writing with casual slang, profanity, short answers, or omission of technical detail. Follow the learner's requested depth and language.

Humanizing must not introduce facts or conceal uncertainty. Preserve quotations, citations, code, identifiers, commands, equations, units, numerical values, assumptions, and logical conditions. Label analogies and explain their limits. If evidence or understanding is missing, investigate or state the gap instead of producing smooth filler. A fluent rewrite is not source verification or educational validation.

Use the skill in embedded mode: learners see the final explanation, not an editing draft or an AI-writing detector report. Begin with an author-side editorial check, not a mandatory second model/service pipeline or streaming postprocessor. Any later automated rewriting needs a separate decision on latency, cost, and factual preservation. The backend still validates durable state and structured payloads; style instructions are not a deterministic correctness guarantee.

Practice is an explicit activity rather than a compulsory response after each explanation. Reading, discussing, and exploring can continue without submitting an answer. In a clear pending practice question, the learner's normal chat reply is the answer; UI uses an explicit submission action. The system reports persistence status, with no extra "confirm saved" step for the learner. Helpful direct answers must not be withheld merely to force a teaching template.

Acceptance:
- Distribute the plugin in a clean compatible Hermes profile with no preinstalled Humanizer; its documented teaching bundle includes the editorial guidance and its required attribution. Verify actual skill loading rather than assuming file presence implies use.
- Exercise discovery, explanation, recommendation, hints, feedback, and visual narration in chat and saved workspace content. Review against the teaching-quality checklist with before/after examples; record subjective judgments as review outcomes, not an objective slop score.
- Rewrite fixtures containing an equation, code identifier, units, quoted passage, citation, caveat, and incorrect learner reasoning. Preserve technical content and attribution; do not flatter the learner or hide the error.
- Ask for a direct explanation with no practice: answer without a compulsory quiz/submission. In practice, submit once and show server-confirmed success or recovery without asking the learner to confirm the save.
- Verify editorial guidance causes neither plugin writes in ad hoc mode nor changes to structured assessment data, source-sharing permissions, or active tracking context.

## Validation layers

- Deterministic service tests: tracked-context mutation authorization and pause/revocation, fixed clock, evidence transitions, solution gating, policy enforcement, retry/conflict behavior, migrations, and malformed-data fixtures.
- Adapter contract tests: HTTP and tools exercise the same state transitions and errors.
- Scripted real-agent evaluations: ad hoc educational conversations with zero plugin writes, opt-in/promotion/exit and untracked side questions, vague-topic discovery, uncertain answers and early exit, skipped interviews for clear goals, reference-verification failures, explicit learning entry, verbatim relay, checkpoints, source-injection fixtures, and unrelated work chats. Report model/provider, failures, and observed reliability; these are not deterministic guarantees.
- Teaching-quality review: Humanizer bundle/activation in a clean profile, representative tutoring outputs, factual-preservation fixtures, and natural practice/persistence UX; style is not a substitute for technical correctness.
- Actual desktop/web/messaging checklist: rendering, auth, links, responsiveness, cross-client continuity, disconnect/reconnect, and persistence, recorded per tested release.

## Delivery stages

1. Feasibility: explicit tracked opt-in with ad hoc zero-write and exit checks, real desktop and web diagram, real messaging tools, shared authenticated store, retry safety, assistance continuity, and restart recovery. No standalone mockup substitutes for these probes.
2. First usable slice: bundled Humanizer teaching guidance, ad hoc/tracked boundaries and explicit transitions, guided discovery from vague topics, both entry points, provisional briefs and source recommendations, curated sources, rubric-backed activities, controlled sequence visual, pending/self/agent assessments, evidence, simple review, and resume across all three interfaces. Frontend delivery may be sequenced but desktop remains required and tested.
3. Extend ingestion and visual types after actual use. Add service-model operations only after their probe and a separate design decision.

## Out of scope

Multi-user accounts/roles, classrooms, billing, offline write synchronization, cross-server replication, arbitrary-code execution infrastructure, autonomous mining of chats, calibrated mastery claims, exact inline UI parity, and full book/paper parsing in the first slice.

## Decisions still needed

Before the spike: no additional product or messaging-channel decision is required. Use an isolated local test environment and the easiest available checks, with manual testing accepted. Investigate host registration/auth/storage/rendering and confirmation mechanics as spike questions. Keep scheduling out of the minimal probe; specify scheduling policy and production payload limits before the first usable release. These are engineering choices and feasibility findings, not questions to repeatedly return to the learner. Changes or restarts affecting the daily Hermes installation still require separate approval.

Before release: supported host/client versions, license, source/draft retention and storage limits, export format, and deletion behavior. Explain-first versus attempt-first remains selectable per activity; a personal default is optional. PDF parsing and code execution are deferred, not prerequisites.

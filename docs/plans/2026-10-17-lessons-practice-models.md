# Lessons, practice, and model selection

Implement the approved product flow on main. Keep practice optional and separate from tutor chat; keep lesson browsing available during model work. Use supported host APIs only; credentials stay with Hermes.

1. Backend: structured teaching metadata and optional practice attached to a lesson/version; validate and carry these through generation/proposals. Human-only model preference per path. Human-only answer submissions create scoped evaluation attempts, model feedback writes only to an authorized pending attempt. Save answer/help exposure/feedback; invalidate pending results when lesson changes. Preserve old lessons without practice.
2. Host integration: discover configured models using the active gateway/profile; persist a per-path selection, apply to session creation and existing sessions without global config writes. Dedicated practice evaluation session, same selected model, no tutoring transcript pollution; retries and uncertain/disconnected sessions do not silently duplicate submissions.
3. UI: model selector on home and tutor; teaching outcome/prerequisites/misconception; separate practice answer, hint/reveal/skip, inline feedback and retry/history, optional tutor handoff. Keep draft answers on navigation and errors; completion never changes selected lesson.
4. Improve teaching prompt and skill: observable outcomes, prerequisites, worked example, coherent project milestones, source grounding, optional criteria-aligned practice; self-check consistency before publishing.
5. Verification: backend contract/isolation/version/idempotency tests, transport tests, production builds, browser simulations covering practice feedback/retry/navigation/model selection and existing lesson navigation. No live model calls without separate authorization. Document compatibility honestly; build both distributable UIs.

Contracts: teaching={outcome,prerequisites:[string],misconception}; practice={kind:explanation|code|project,prompt,criteria:[string],hints:[string],explanation}. Course model is null (Hermes default) or {provider,model}. One practice evaluation per workspace at a time; separate from tutor, no new mastery system. Exercise criteria/reference are ordinary teaching content, not a secure exam.


Implementation notes:
- Implemented stages 1–2 and path model selection; adaptive memory and spaced review remain out of scope.
- Model changes copy authenticated dialogue history into a session.create request with session overrides, because deferred config switches can continue with the old model and session.branch_stored rejects override fields. Applied choice is saved in the binding to avoid needless branches after reload.
- A registered pre-tool hook restricts evaluator sessions to the scoped feedback tool; code is reviewed without execution.
- Explicit recovery reconciles saved attempts using stable request IDs and never replays a possibly delivered prompt. Healthy shared WebSocket connections remain open when another session restores.
- Existing lessons stay readable. Model publication requires teaching/practice; source, topic, and project prompts use the same contract. Lesson versions remain monotonic even if a key is removed and later reintroduced.
- Verified backend contracts, UI controllers, production builds, installer discovery, and labelled simulated browser flows. Live model teaching quality and native Mac behavior were not tested in this change.

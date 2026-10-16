# Evidence-linked learning loop implementation plan

> Implement with superpowers:subagent-driven-development. User authorized execution in this chat; work in the existing feature checkout.

**Goal:** Make learning evidence, objective progress, review and next actions usable together.
**Architecture:** Additive records/contracts and read-only projections in the Python service; shared React workspace consumes the projections. Existing host agents author and assess; no separate inference service.
**Tech stack:** Python, SQLite, React, esbuild.
**Spec:** ../specs/2026-10-16-learning-loop.md

## Global constraints

Preserve API/schema v1 compatibility, explicit consent, immutable evidence, source policy, retry behavior and no read-time writes. No runtime dependencies. Keep existing generated bundles coordinated. No daily host installation.

## Review focus

- Existing stores without new fields must remain readable and usable.
- Generated help must survive retries without leaking restricted source material.
- Superseded/disputed/self-assessed evidence must remain honestly labeled in progress and recommendations.
- Cross-track IDs and malformed visuals must fail without partial writes.
- File import, mobile layout and pending answers must remain recoverable.

## Tasks

- [x] Backend: write failing contract/behavior tests; implement help content/idempotency, objective identity, learner profile, activity links, criterion feedback, derived progress/next actions and objective reviews; extend structured visuals and runtime schemas. Own plugin Python and service/adapter tests.
- [x] Workspace: implement optional setup profile, Progress/next actions, precise tutor handoff, activity types/objective links, feedback/help evidence, local source import, state-machine/code-trace rendering. Write behavior tests for pure import/visual helpers and verify browser flow. Own ui/src and ui/test.
- [x] Host integration: inspect supported SDK/navigation/session APIs and report the safest available existing tutor handoff. Read-only exploration first; no credentials in output.
- [x] Evaluation/integration: add repeatable scenario-based evaluation and human teaching checklist, package runtime modules, update documentation and authored technical example; run backend, UI, browser, packaging checks.
- [x] Review: independently inspect full change for correctness, policy leaks, historical compatibility and product gaps; address findings and rerun affected checks.

## Progress

Baseline: 5 UI tests passed; 39 Python tests passed with loopback allowed (2 HTTP cases skipped under system Python). Final validation used the host virtual environment so HTTP cases ran.

## Final verification

- **62 Python tests passed**, no skips, using the host Python environment and loopback permission. This includes real FastAPI adapter tests, preview boundaries, concurrent SQLite startup, generated-help privacy, legacy reads, criterion feedback, objective projections/reviews and package validation.
- **15 UI helper/recovery/handoff tests passed**. Production web, desktop and preview bundles built; both host bundles passed JavaScript syntax checks.
- **3 deterministic evaluation scenarios passed**. `dev/evaluate.py` explicitly reports that these scenarios do not evaluate a live model or teaching quality.
- **Repeatable browser flow passed** on the final isolated backend and bundle, including exact answers, reload and activity-switch draft isolation, objective progress, source attachment, structured visuals, mobile dark layout, and a review whose old activity was reassigned to another objective. Separate browser checks exercised profile setup, authoring, explicit reveal, malformed UTF-8 rejection and leave. No page errors.
- **Actual isolated Electron handoff passed**: unsent single-line resume draft, verbatim second-request recovery, existing native draft retained, no sessions/messages/attempts/assessments created. No provider was configured for this check. The known temporary host `Path` import workaround was needed; daily source/profile remained unchanged.
- **4 successful live CLI conversations** (2 baseline, 2 final) reproduced and closed the generated-help capture gap while preserving explanation-only behavior. One initial sandbox network failure is separately reported. See [live tutoring evaluation](../../evaluations/live-tutoring-2026-10-16.md); this is a small behavioral sample, not a teaching-quality benchmark.
- Both distribution ZIPs rebuilt with checksums. `git diff --check` passed. No daily installation or restart.

Independent review identified review dates overwritten by unrelated stronger evidence and fallback activities that no longer checked the review objective. Both were fixed with regression tests and the review queue now requests a new task when no current match exists. Browser inspection additionally found and fixed stale activity detail carrying a previous draft into a newly selected activity. Review also prompted truthful unavailable-hint messaging and two separate native handoff messages.

Small remaining UX limits: blanking an already saved session-length field retains its previous value; native request recovery is local to the desktop session rather than synchronized or automatically sent. Conversation-bound consent and broader model/pedagogy evaluation remain separate roadmap work.

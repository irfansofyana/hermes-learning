# Cross-client learning and visualization spike

Status: proposed, not executed. Installation and restarts require separate approval. This spike tests actual host integrations, not a standalone mockup.

## Scenario

One permitted curated excerpt about retries/idempotency, an approved objective, one versioned rubric-backed prediction activity, and one structured sequence visual. Agent tools and authenticated desktop/web APIs access the same backend store. No backend model calls are needed: use authored fixtures and real chat-agent tool calls.

## Lightweight execution policy

Use the easiest available test path; choosing a particular messaging platform is not a blocker or a product-support decision. The learning core remains channel-independent. Use a few automated checks for persistence, explicit tracking opt-in/exit, and retry safety. Verify actual desktop/web behavior manually, and provide the learner a short manual messaging/cross-client checklist. No comprehensive per-channel automation, benchmark framework, coverage target, or new testing infrastructure is required for this throwaway spike.

Record which checks were actually exercised and which remain manual/unverified. Manual testing is acceptable evidence when its steps and observed results are recorded. Do not claim all messaging channels work because one did. Continue to require separate approval before changing or restarting the daily Hermes installation.

## Required probes

| Probe | Pass evidence |
| --- | --- |
| Opt-in boundary | Educational ad hoc chat and declined offers produce no plugin writes or automatic personal-track lookup. Explicit entry enables scoped persistence; selected-context promotion requires approval. Exit rejects late writes and leaves committed records intact. Opening an overview does not enroll. Prove the host entry mechanism rather than trust a model boolean. |
| Shared store | Actual HTTP and tool contexts report the same store identity and data; parallel writes and concurrent initialization succeed. |
| Authentication | Unauthenticated GET/POST fail on direct and configured proxy routes; valid clients work without credentials embedded in links. |
| Desktop and web visual | Actual host plugins render the same structured visual; keyboard steps, resizing, themes, text alternatives, and malformed-payload errors work. Record what frontend code cannot be shared. |
| Messaging | Use an available convenient channel, or let the learner manually check their channels. No platform selection blocks building the spike. Verify tools can resume, retrieve safe text, record assistance, and submit; record only channels actually tested. |
| Continuity | Ask for a hint in chat, close it, answer in web, and inspect preserved assistance/attempt in desktop and a fresh chat. |
| Assessment | UI submission remains pending without chat; self-check and later agent assessment remain separately attributable. Criteria predate the attempt and normal retrieval hides the key. |
| Retry/recovery | Retry the server-issued submission ID after a simulated lost response; one attempt persists. New identity permits an intentional identical answer. Restart with approval and read back records. |
| Navigation and interruption | Workspace URL opens the correct activity. Copyable resume prompt works. Local draft survives reload as unsubmitted; stale/offline state is visible. |
| Teaching quality | Verify the intended Humanizer guidance loads; inspect explanation, hint, and feedback fixtures for concrete teaching and preserved technical meaning. Test direct explanation without forced practice and one-step submission with system-reported save status. Do not treat prose style as a correctness or security guarantee. |
| Agent reliability | Exercise explicit entry, saved checkpoints, verbatim relay, unrelated work chat, and source-injection fixtures. Record failures and provider/model rather than claim perfect reliability. |
| Discovery and materials | Run a broad-topic/no-knowledge chat with an "I do not know" response and "suggest a starting point" exit. After explicit persistence opt-in, save a path-unapproved brief, resume it explicitly in another client, propose a small verified or explicitly unverified source set, and require approval before activation. A failed reference lookup must not produce a fabricated citation. |

## Optional probes

Raw-user-message hooks and correlation, native desktop deep links, and backend model access/retry/cost behavior. Failure here must not silently substitute unverified behavior into the first slice.

## Report

Record tested host versions, deployment topology without secrets, commands, screenshots/artifacts, assertions, observed failures, and unsupported assumptions. Desktop and web both remain required even if probes run in sequence. A failed host boundary is a reported blocker, not proof from a browser demo.

## Exclusions

Full document parsing, arbitrary generated code, production rollout, complete curriculum UI, and retaining throwaway code as a finished implementation without review.

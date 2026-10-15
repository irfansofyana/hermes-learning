# Teaching quality and Humanizer integration

Status: required product direction. The isolated spike bundles an original Humanizer-compatible teaching adaptation; host registration and skill retrieval are exercised, while model adherence remains unevaluated. R11 owns release acceptance. No daily/production installation is implied by this document.

## Integration contract

Bundle the Humanizer skill or an explicitly attributed compatible adaptation inside the plugin's distributed teaching package. Record its source/version/license and comply with redistribution terms. Do not require a skill that happens to exist in the developer's profile. Determine the supported Hermes skill registration/loading path during implementation rather than inventing a manifest field.

Apply teaching guidance while composing the answer. Return final prose only: no draft/rewrite ritual or detector commentary in lessons. Do not add a mandatory second inference call, model proxy, or streaming postprocessor. Confirm activation with actual agent output and clean-profile testing, not merely a file listing.

Editorial behavior and persistence are independent. Useful ad hoc teaching can use Humanizer without tracked enrollment or learning-record writes. Do not replace the user's unrelated work-chat conventions globally.

## How the tutor should write

Answer the learner's actual question first. For a difficult concept, explain its mechanism, use a concrete example, and keep conditions/counterexamples that affect correctness. These are useful ingredients, not headings to repeat in every reply. Use a diagram when it answers a question more clearly, not to decorate the lesson.

Ask focused questions that respond to what the learner said. Avoid repeated "Great question," generic encouragement, staged enthusiasm, filler transitions, unearned certainty, decorative bold labels, and summaries that repeat the preceding paragraph. Do not require fixed word counts or artificially short explanations. Technical depth is welcome when needed.

Feedback identifies the actual error, explains why it matters, and offers a useful next attempt. Do not describe incorrect work as excellent or mark understanding merely because the learner repeated the tutor's words. Respect uncertainty and respond without shaming.

Match requested language and depth. Natural teaching is compatible with formal proofs, exact terminology, careful caveats, and long explanations. It does not require slang or mimicry of the learner's frustration.

## Preserve meaning

Do not alter source quotes, code, commands, identifiers, citation targets, equations, units, numbers, logical quantifiers, or the scope of a claim for stylistic reasons. Explain difficult terminology rather than replacing it with an inaccurate everyday synonym. Keep evidence separate from inference. A useful analogy includes its breaking point when that matters.

Do not invent details to make the lesson vivid. Mark hypothetical examples as hypothetical. Rewriting a factual claim does not validate it; use the source/retrieval policy when verification is needed.

Do not modify grades, assistance flags, rubrics, diagram semantics, source permissions, or tracking consent as part of prose editing. Structured outputs and visual labels remain subject to their normal schema/security rules.

## Examples of the intended tone

The examples below are illustrative wording fixtures, not excerpts from a cited source.

Weak:
> Great question! Let's dive into the fascinating world of idempotency, a crucial pillar of robust distributed systems.

Preferred:
> An idempotent operation has the same effect when repeated as when performed once. For example, setting a value to 5 has that property; increasing it by 5 does not.

Weak feedback:
> Excellent work! You're absolutely right, although there are a few small nuances to consider.

Preferred feedback:
> You assumed the first request failed because the client timed out. The server may already have completed it. Trace what a retry would do in that case.

An explanation should not always end with a quiz. If the learner chooses practice, make the question explicit and accept a normal chat answer. The system handles saving and reports its result; the learner does not confirm that a backend write happened.

## Review checklist

- Does this answer the question, rather than stage an introduction?
- Does each example or visual clarify the mechanism under discussion?
- Are assumptions, uncertainty, and important limits intact?
- Were all technical tokens, quotations, units, equations, and references preserved?
- Does feedback address a specific reasoning error without empty praise?
- Is a question or exercise useful and agreed, rather than mechanically appended?
- Is the explanation readable at the requested depth without padded sections?
- Did editing preserve source boundaries, consent, and structured learning state?

Use human review and regression fixtures. Do not claim an automatic detector proves writing is human, pedagogically sound, or factually correct.

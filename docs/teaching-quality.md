# Teaching quality and Humanizer integration

The plugin bundles its own teaching and clear-prose skills. Generation prompts include the essential lesson rules directly and ask the model to load the skills when available. Structured payload validation and simulated UI tests verify contracts; they do not establish model adherence, factual accuracy, or learning effectiveness.

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

New lessons offer one small optional practice task aligned with the lesson outcome. It has its own answer and feedback area inside the lesson, separate from tutor chat. Learners can skip, use hints, reveal the explanation, retry, or explicitly bring the exercise into chat. A chat answer is not silently saved as an assessed attempt. Reading and assisted completion are not evidence of independent mastery.

## Review checklist

- Does this answer the question, rather than stage an introduction?
- Does each example or visual clarify the mechanism under discussion?
- Are assumptions, uncertainty, and important limits intact?
- Were all technical tokens, quotations, units, equations, and references preserved?
- Does feedback address a specific reasoning error without empty praise?
- Does the optional exercise apply the lesson outcome, with criteria and a reference explanation that agree with the worked example?
- Is the explanation readable at the requested depth without padded sections?
- Did editing preserve source boundaries, consent, and structured learning state?

Use human review and regression fixtures. Do not claim an automatic detector proves writing is human, pedagogically sound, or factually correct.

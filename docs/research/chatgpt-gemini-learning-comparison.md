# ChatGPT, Gemini, and Hermes Learning

Research date: 2026-10-16 (Asia/Jakarta). Hermes snapshot: `8c212c7`.

## Scope and evidence

This compares first-party product documentation with the current Hermes source and recorded verification. It is not a hands-on competitor evaluation or a learning-outcomes study. Product documentation establishes advertised behavior, not its reliability for a particular learner. An undocumented competitor capability is marked unknown, not absent. Hermes requirements describe intended behavior; they are not proof of implementation.

The comparison separates ChatGPT Study mode from its broader visualization and education tooling, and Gemini Guided Learning from study notebooks and the connected notebook product. These surfaces have different availability and should not be treated as one universal mode.

## Main finding

Hermes currently has a persistent learning workspace, an evidence model, and a protocol for a Hermes agent to teach through tools. Its largest gap is the continuity of the tutoring experience: diagnosis, explanation, practice, feedback, and selecting the next useful activity remain largely agent-directed or manual. This is a product assessment inferred from the implementation, not a claim about comparative learning outcomes. See [the workspace](../../ui/src/App.jsx), [practice](../../ui/src/Practice.jsx), and [teaching skill](../../plugin/skills/teach/SKILL.md).

Gemini's study notebooks make the comparison more demanding than the original Guided Learning launch: Google now documents diagnosis and an adaptive progress interface. Hermes cannot claim that persistent learning paths alone distinguish it from the current Gemini offering. [Google's June 2026 announcement](https://blog.google/innovation-and-ai/products/gemini-app/gemini-study-notebooks/)

## What the competitors document

### ChatGPT

Study mode supports conversational explanation, questions, understanding checks, practice, and help with uploaded files/images where available. Memory can personalize it when enabled. It can still make mistakes or give direct answers. These are conversational capabilities, not evidence of an immutable assessment ledger. [Current Study mode help](https://help.openai.com/en/articles/11780217-using-study-mode-in-chatgpt)

OpenAI's March 2026 interactive-learning announcement covers more than 70 math/science concepts with adjustable variables and immediate visual feedback. Separately, the broader Visualizations feature supports interactive explanations and simulations, with rollout and surface restrictions. Neither implies that every Study mode response uses an interactive widget. [Interactive learning announcement](https://openai.com/index/new-ways-to-learn-math-and-science-in-chatgpt/), [Visualizations documentation](https://learn.chatgpt.com/docs/visualizations)

OpenAI also documents a workflow for source-linked study guides, spaced-practice calendars, question banks, and a progress tracker. That is an agent-generated artifact workflow; it does not establish an automatic, built-in longitudinal learner model. Dedicated education plugins were announced in August 2026. [Exam study workflow](https://learn.chatgpt.com/use-cases/build-exam-study-system), [ChatGPT Learn updates](https://learn.chatgpt.com/docs/whats-new)

### Gemini

Guided Learning provides step-by-step explanations and guiding questions. Gemini's student feature documentation also describes reading photos/PDFs, interactive image exploration, custom quizzes, study guides, flashcards, and audio summaries. These are separate learning affordances, not all necessarily part of the Guided Learning mode itself. [Student features, February 2026](https://blog.google/products-and-platforms/products/education/gemini-features-for-students/)

Study notebooks use uploaded materials and a diagnostic quiz to generate lessons and identify gaps. Google describes an objective-based dashboard, with strengths/focus areas and prioritized lesson recommendations. Its launch article describes more than 100 learning objectives per goal. This is a documented personalization system, not proof that those labels are calibrated measures of mastery. [Study notebooks launch](https://blog.google/innovation-and-ai/products/gemini-app/gemini-study-notebooks/)

Current help confirms diagnostics, personalized lessons, and automatically updated progress/recommendations. It also says study notebooks require Keep Activity to be enabled, are available on the web rather than in the Gemini mobile app, and cannot have their learning goal edited in place. General notebooks have different mobile availability. This supersedes assuming that the launch article's promised later mobile support has shipped. [Current notebook help](https://support.google.com/gemini/answer/16972047?hl=en)

The September 2026 Gemini Notebook announcement describes additional multimedia and study features, but several are explicitly staged rollouts or forthcoming. Do not treat voice conversations, additional quiz formats, or interactive learning overviews as universally available merely because the announcement exists. [September notebook update](https://blog.google/innovation-and-ai/products/gemini-notebook/new-study-tools-september-2026/)

## Comparison against the implementation

Competitor entries below refer to the cited product descriptions above. Hermes entries are supported by the linked source files.

| Dimension | ChatGPT learning surfaces | Gemini learning surfaces | Hermes today |
| --- | --- | --- | --- |
| Entry | Ask a question, provide level/materials, use Study mode | Guided Learning or goal/material-based study notebook | Title and curiosity form; proposed brief and separate approval. Discovery happens through the agent. |
| Diagnosis | Conversational checks | Diagnostic quiz and personalized lessons | No diagnostic workflow or structured prerequisite/misconception model. |
| Tutor interaction | Dialogue in the chat | Dialogue; notebook questions alongside lessons | Workspace hands off through a copyable resume prompt. |
| Material intake | Chat uploads where available | Uploaded notes, photos/PDFs, notebook sources | Source metadata and selected text; no plugin-owned file ingestion or search. |
| Visual exploration | Dynamic math/science modules; broader visualizations | Interactive images and notebook study outputs | One validated sequence schema with step navigation and text alternatives. |
| Practice and feedback | Conversational quizzes and explanations | Quizzes feeding lesson recommendations | Authored activities; submit now, self-assess or request agent assessment later. |
| Progress | Memory/artifacts; a native equivalent to Hermes's ledger is not established here | Objective dashboard and recommended priorities | Saved attempts/assessments; no objective-level competence aggregation. |
| Review | Prompted spaced-study workflow | Quiz/flashcard review and adaptive lessons | An explicit queue, using a fixed 1/3/7-day activity schedule. |
| Technical projects | General assistant/coding capabilities; not necessarily a Study mode workflow | Code help/Canvas; not necessarily a study-notebook workflow | Build activity briefs; no execution environment or repository ingestion. |
| Record integrity | Equivalent internal guarantees not documented in reviewed sources | Equivalent internal guarantees not documented in reviewed sources | Immutable attempts/rubrics, assistance attribution, correction/dispute history, retry identity. |

Hermes implementation evidence: [forms](../../ui/src/forms.jsx), [chat handoff and proposed paths](../../ui/src/App.jsx), [practice](../../ui/src/Practice.jsx), [source handling](../../ui/src/Collections.jsx), [sequence renderer](../../ui/src/Sequence.jsx), [service](../../plugin/learning_store.py).

## Discrepancies inside Hermes

1. **Guided discovery is mostly an agent instruction.** The teaching skill requests background, goals, and time, but the workspace offers forms and a chat handoff. A learner does not yet get an integrated diagnostic-to-first-lesson flow. There is also no structured learner profile carrying prerequisites or misconceptions. [Teaching guidance](../../plugin/skills/teach/SKILL.md), [workspace](../../ui/src/App.jsx)

2. **Recorded evidence does not yet drive a competence model.** Assessments contain an outcome and feedback attached to immutable activity/rubric versions. They do not structurally distinguish conceptual versus practical competence or score individual criteria. A completed answer does not establish transfer to another problem. The product brief explicitly wants these distinctions. [Assessment service](../../plugin/learning_store.py#L437), [product brief](../product-brief.md), [requirements R5](../requirements.md)

3. **Review is activity-based rather than objective-based.** Requirements ask for review of learning objectives, including varied examples. The implementation schedules the specific activity 1, 3, or 7 days after assessment. It honestly labels this as a heuristic, but it is a narrower system. [Scheduling implementation](../../plugin/learning_store.py#L454), [requirements R6](../requirements.md)

4. **Generated help cannot be checkpointed as described.** The teaching skill instructs the agent to record even help it generated itself through `learning_help`. The service accepts a help level and returns preauthored content; missing authored help is rejected. There is no payload for the newly generated help text. Calling the tool therefore cannot by itself establish that the actual generated assistance was durably recorded. [Skill instruction](../../plugin/skills/teach/SKILL.md#L24), [help implementation](../../plugin/learning_store.py#L423)

5. **Source labels and checks can be overinterpreted.** A source labeled book, paper, or repository is not an imported or inspected document. Verification status is author-reported. Quote checking establishes a whitespace-normalized match to stored material, not authenticity or whether the source supports a claim. The implementation and skill disclose these limits; product descriptions must preserve them. [Source service](../../plugin/learning_store.py#L338), [source guidance](../../plugin/skills/teach/SKILL.md#L16)

6. **The generic activity UI still follows the prediction example.** Before submission, the practice heading is “Your prediction” for all activity kinds. Explanation, trace, and build activities need wording and affordances that match the task. This is a concrete UI inconsistency, independent of competitor parity. [Practice component](../../ui/src/Practice.jsx#L20)

7. **Tracking consent is stronger than implicit topic matching, but session binding is incomplete.** Start/resume and revocation are implemented. Contexts are private capabilities, not authenticated conversation identities; automatic per-chat isolation is not established. [Compatibility and consent limits](../compatibility.md)

8. **Engineering verification has outpaced teaching verification.** The repository records real isolated dashboard/Electron behavior and shared evidence. It also states that no provider was configured and no actual tutoring or messaging conversation was exercised. Skill retrieval and service tests cannot establish adaptation, good feedback, reliable source use, or learning gains. [Verification record](../compatibility.md)

## Differences worth retaining

Hermes has a useful design focus: a technical learner can preserve the exact answer, which rubric applied, what assistance was used, who assessed it, and subsequent corrections. It also owns an inspectable review queue and a recoverable local store. These are concrete implemented properties. The reviewed competitor documentation does not establish equivalent record semantics; that is not evidence competitors lack them. [Service](../../plugin/learning_store.py), [data/recovery documentation](../../README.md)

Explicit tracking and source-sharing boundaries are also deliberate product choices. They should survive UX simplification. “Local learning records” must not be presented as a guarantee that model processing is local. A Hermes model provider can still receive permitted content. [Compatibility](../compatibility.md), [teaching guidance](../../plugin/skills/teach/SKILL.md)

Books → repository investigation → an independent implementation remains a plausible focus for Hermes, but it is a proposed advantage. Build-task labels and source metadata do not establish that integrated workflow today. [Product brief](../product-brief.md)

## Recommended order of work

These are recommendations inferred from the comparison, not an approved implementation plan.

1. **Evaluate the existing tutor on representative conversations.** Include a vague curiosity, a clear technical goal, a source-first question, incorrect reasoning, a hint, a side question, an exit, and resumption in another client. Record the actual model/provider and inspect both teaching and state writes. This establishes what needs an implementation change versus better guidance.
2. **Resolve the generated-help recording mismatch.** Assistance provenance is central to the evidence model; it needs to describe what was actually shown.
3. **Connect one complete learning loop.** Let a learner diagnose a gap, study a source, attempt a task, receive criterion-specific feedback, and understand the next action with fewer manual handoffs. This does not require silently adding backend inference; existing host integration should be investigated first.
4. **Represent objectives and evidence explicitly.** Link activities to objectives, retain uncertainty and assistance, and test transfer with a different example before recommending progress. Keep review scheduling distinct from claims of mastery.
5. **Reduce source-entry effort and broaden visuals selectively.** Start with source excerpts/imports the learner can inspect and the visual types needed by actual technical tracks. Preserve controlled schemas rather than accepting executable model-generated content.
6. **Prove the technical-learning use case.** Use one book/paper passage, one real repository reference, and one independent task. Assess reasoning separately from the artifact working. This is a more focused target than matching every exam, audio, or flashcard feature.

## Limits and follow-up

No competitor account was tested, no new Hermes live-model evaluation was run, and existing test suites were not rerun for this read-only research. Account-level rollout, pedagogical reliability, grading calibration, and long-term learning outcomes remain unverified. Current help takes precedence over old launch promises. Neither a fluent explanation nor an automatically updated dashboard is sufficient evidence of learning effectiveness.

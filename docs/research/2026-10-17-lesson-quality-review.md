# Making generated lessons worth learning from

Research and implementation review, 17 October 2026. Inspected repository commit `5996a6d` with a clean initial working tree. This review reads generation instructions, publication validation, lesson rendering, practice feedback, and evaluation reports. It does not inspect a representative collection of real generated lessons, run a live model, or measure learner outcomes. Findings about likely output are implementation risks, not observed failure rates.

The companion [evidence review](2026-10-17-effective-ai-lessons-evidence.md) records the primary research and its limits.

The highest-value change is to give each lesson a deliberate teaching sequence: a concrete problem, enough explanation to reason about it, a worked example, and an invitation to try a changed case. Keep extra depth available when needed. Human-like wording helps, but we should judge the result by correctness, useful examples, and what the learner can do afterward.

## Evidence and implications

The US Institute of Education Sciences recommends alternating worked solutions with problems, revisiting material over time, connecting concrete and abstract representations, and pairing relevant graphics with explanations. Its evidence ratings differ across recommendations. These support a lesson with meaningful learner actions; they do not establish a universal lesson length or prove that every paragraph needs an interaction. [IES practice guide](https://ies.ed.gov/ncee/wwc/PracticeGuide/1).

AI-specific studies show that design matters. In a high-school mathematics trial, unrestricted AI improved assisted work but harmed subsequent unaided performance. A tutor supplied with teacher-designed guidance and solutions mitigated that harm without showing a significant unaided advantage over the control. This supports measuring performance after assistance is removed. It does not justify blocking a learner who wants an explanation. [Bastani et al., author manuscript](https://hamsabastani.github.io/education_llm.pdf).

A college physics trial found stronger immediate learning with a carefully designed AI tutor than its active-learning comparison. The authors used expert-designed materials and application controls as well as prompting. This is evidence for a particular tutoring system, rather than proof that an automatically authored course will outperform a human teacher. [Kestin et al., 2025](https://www.nature.com/articles/s41598-025-97652-6).

Our product inference: combine authored teaching patterns, useful controls, and evaluation. Do not expect a request to “write naturally” to supply those by itself. Shortening text can remove padding, but it can also remove the reasoning a beginner needs.

## Comparison with our implementation

| Area | Current behavior and evidence | Improvement |
| --- | --- | --- |
| Outcomes and examples | `ui/src/tutor-session.mjs:18–21` and `skills/teach/SKILL.md:28–32` request observable outcomes, prerequisites, worked reasoning, and consistency checks. | Keep these. Add examples of excellent complete lessons so the model can see appropriate scope and pacing. |
| Natural prose | `skills/humanizer/SKILL.md` and `docs/teaching-quality.md` give useful editorial guidance. The main prompt asks to load the teaching skill if available; that skill asks to use Humanizer if available. | Put a compact version of the essential prose rules directly in the generation prompt. Verify skill activation in a clean profile. |
| Lesson format | `ui/src/CourseContent.jsx:46–50` renders one Markdown body, then the structured visual and references. `LearningApp.jsx:105` places practice after that content. Inline diagram fences already support placing some visuals beside their explanations. | Start by improving Markdown composition. Later add ordered lesson blocks so checks and worked examples can appear where needed. |
| Practice | `PracticePanel.jsx` offers one exercise, progressive hints, reveal, skip, feedback, retry, and history. `practice-session.mjs:7–16` requests criterion-based feedback and limits solution exposure. | Preserve this work. Make the task change a meaningful condition from the worked example; add optional checks within longer lessons. |
| Enforcement | `__init__.py:71–78` requires teaching and practice fields for model-authored publications and revisions. `learning_store.py:497–528` validates their shape. The base runtime retains compatibility with older callers. | Schema validation already guards missing fields in the normal model path. Add semantic review of whether the example, task, rubric, and solution agree. |
| Continuity | `learning_store.py:708–740` supplies earlier lesson excerpts, versions, outcomes, and missing-lesson flags. The prompt requests a coherent evolving project. | Continue reusing the same project. With explicit learner intent, offer targeted remediation based on a submitted practice attempt. Current continuity payloads do not include practice evidence. |
| Evaluation | `docs/evaluations/tutoring.md` distinguishes deterministic contracts from live teaching. The October 16 report covers narrow explanation/help-recording conversations. | Add a generated-lesson benchmark and later a learner study. Existing tests and reported live cases do not establish course quality or retention. |

## Changes to make first

**1. Define a lesson editorial contract and demonstrate it.** Keep one observable outcome per lesson. Open with a concrete situation or task, introduce the mechanism needed to solve it, show intermediate steps and expected results, and address a plausible wrong inference. End with optional application that changes something consequential. Choose the order to suit the subject; do not force identical headings across lessons.

Add three small reference lessons to the teaching package: a beginner concept, a code walkthrough, and a project milestone. Include a weak example beside an improved one with short reviewer notes. Preserve technical assumptions and citation targets during edits. Reference lessons should teach composition rather than encourage copying their wording.

**2. Remove prompts that reward volume.** The later-lesson instruction currently calls for “substantial Markdown” (`tutor-session.mjs:25`). Replace this with a definition of completeness tied to the outcome. Include essentials such as: start with the useful point, cut repeated introductions and summaries, use concrete names and values, and retain reasoning and correctness conditions. Do not add a hard word limit or a minimum diagram count. These would be product heuristics without evidence from this review.

**3. Review generated lessons against a rubric.** Begin with the existing model doing a concise internal consistency check during composition; this fits the current policy against a mandatory second inference call. Review a sample with humans before adding an automated critic. A second model can later flag problems, but agreement between models is not independent factual verification.

Review these questions:

- Can the learner perform the stated outcome using what the lesson teaches?
- Does the worked example show the important decisions and intermediate states?
- Does the exercise require reasoning about a changed case rather than copying a sentence?
- Do the reference answer, success criteria, examples, and visuals agree?
- Does every section add something useful? Are prerequisites and technical limits preserved?
- Do sources support the claims attributed to them?

Track hard defects separately from editorial preferences. A wrong solution or unsupported central claim needs correction even if the lesson reads well. Paragraph length, repeated openings, and excessive headings can flag material for review; none proves poor learning or AI authorship.

## A next iteration for the interface

After establishing a quality baseline, introduce an optional versioned `blocks` format alongside existing Markdown lessons. An ordered list could contain explanation, worked example, diagram, and practice references. Keep the supported block types small and render existing Markdown through the current path.

This requires coordinated changes to tool schemas, store validation, lesson versions, source restrictions, practice identity, renderer, and revision previews. An embedded exercise needs its own stable identity bound to a lesson version; the current single-practice-per-lesson contract is insufficient for multiple checks. Preserve existing attempt history and stale-result behavior during migration.

Place a prediction or explanation opportunity after the relevant example. Offer a reveal and allow navigation without submission. Keep an “expand explanation” option for learners who need more detail. Avoid turning every sentence into a separate card or enforcing answer gates. These interface choices are proposals to test, not effects established by the cited studies.

Offer later retrieval practice as a separate, explicit feature: a fresh problem on a previous outcome when the learner returns. Retain the current distinction between reading, assisted completion, and independent work. The present lesson/practice plan excludes adaptive memory and spaced review; adding them would expand product scope and should receive its own design.

## Example of the intended lesson

Illustrative content, not a generated lesson observed during this review:

> Your client sends a payment request. The server charges the card, but the response gets lost. The client sees a timeout. Retrying with a new operation identity could create a second charge.
>
> An idempotency key lets the server recognize another attempt at the same intended operation. In this example, the server atomically records key `pay-42` with the charge result. A retry with that key and the same parameters returns the recorded result. This behavior depends on the provider's contract, including concurrent requests and key retention.
>
> | Event | Server state | Client knows |
> | --- | --- | --- |
> | First request commits | One charge; result stored for `pay-42` | Waiting |
> | Response gets lost | One charge | Timeout; outcome unknown |
> | Same-key retry | Recorded result returned | Confirmed charge |
>
> Try a changed case: the retry uses `pay-43`. Does the previous key still protect this payment? Explain what the server can recognize.

In the product, put the last task in the practice object. Its reference answer should say that a new key may identify a new operation, so the previous key does not by itself prevent a second charge. An optional deeper explanation can cover mismatched parameters, concurrent requests, and expiry. A suitable later transfer task could ask about retrying email delivery with a provider that offers no idempotency contract.

The same approach works outside programming: show a concrete case, explain the mechanism with enough detail, and ask the learner to apply it under a changed condition.

## How to decide whether the changes help

Create a small evaluation set spanning beginner/intermediate topics, project milestones, attached sources, and a difficult misconception. Generate baseline and candidate lessons using the same inputs, model, source snapshots, and generation settings; retain several samples to expose variability. Have reviewers compare them without knowing which prompt produced each lesson.

Record factual errors, rubric alignment, missing steps, repetition, and reviewer preference. Track generation latency and cost. This establishes an authoring-quality baseline, not learning effectiveness.

Then ask consenting learners to attempt new problems without the tutor immediately after a lesson and after a delay. Score against criteria established in advance; record hints and solution exposure. A next-day or next-week check would be a practical pilot choice, not a scientifically optimal schedule. Compare time spent and unaided performance together. Reading completion, satisfaction, and “sounds human” ratings cannot establish retention.

Recommended order: lesson examples and prompt edits, a repeatable quality evaluation, then ordered blocks and embedded practice. Add adaptive review after the core lessons show useful learning outcomes. No application behavior was changed for this research request.

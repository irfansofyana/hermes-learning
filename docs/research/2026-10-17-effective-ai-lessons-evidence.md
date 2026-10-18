# Evidence for effective AI-generated lessons

Researched 17 October 2026. Scope: instructional design and AI tutoring evidence; implementation comparison is maintained separately. Primary studies and first-party research summaries were found with Brave, then read with Tavily extraction; some publisher pages resisted direct retrieval.

## Summary

The strongest direction is to make lessons elicit thinking: explain a manageable idea, demonstrate it, ask the learner to use or explain it, and respond to their attempt. AI tutoring studies support carefully designed systems, while also documenting harm when assistance replaces thinking. Neither these trials nor multimedia research establishes a universal ideal word count for generated text. The product recommendations below are inferences to test, not proven effects in Hermes.

## AI-specific causal evidence

### 1. Structured AI tutoring can improve immediate learning

Kestin et al. (2025) conducted a randomized crossover study with 194 eligible students in one Harvard introductory physics course, across two lessons. AI tutoring produced higher immediate post-test performance than an active-learning class, with median AI time of 49 minutes versus an assumed 60 minutes of classroom learning. Critically, the authors report that prompts alone did not reliably scaffold multipart problems; the platform enforced their sequence. The tutor also used expert-written, problem-specific material and provided correct solutions in its prompts. This is evidence for the complete designed intervention, not proof that generic AI-written lessons outperform human teaching. Long-term retention and broad subject generalization remain unestablished. [Primary paper, full text](https://www.nature.com/articles/s41598-025-97652-6).

Product inference: encode instructional sequence in lesson structure and rendering; do not depend solely on a style instruction in a prompt.

### 2. Assisted success can hide reduced independent learning

Bastani et al. (2025) studied nearly 1,000 high-school mathematics students in Turkey. Compared with control, a standard-style GPT interface improved assisted practice grades by 48%, but subsequent unaided exam grades fell 17%. A tutor with teacher-designed hints, correct solutions, and common-error information improved assisted practice 127%; its unaided exam result was statistically indistinguishable from control. Safeguards mitigated harm without demonstrating an independent learning advantage. This was one school, mathematics, older GPT-4 deployments, and short-term outcomes—not a long-term retention test. [Published abstract](https://pubmed.ncbi.nlm.nih.gov/40560616/), [authors' full-text PDF](https://hamsabastani.github.io/education_llm.pdf).

A published correction concerns an author affiliation production error, not the reported outcomes. [Correction](https://www.pnas.org/doi/10.1073/pnas.2518204122).

Product inference: distinguish unassisted attempts from answer reveals and hint-assisted success. Learning evaluation should include independent questions rather than completion alone.

## Established learning research; not AI-specific

### 3. Retrieval matters more than the feeling of fluent reading

Roediger and Karpicke (2006) compared restudying prose with free-recall tests in two experiments. Restudy benefited a five-minute final test, while prior retrieval benefited tests after two days or one week. Restudying also raised confidence despite poorer delayed retention. This supports delayed retrieval measures and productive effort; it does not establish that any multiple-choice widget or exercise placement will have the same effect. [Authors' university publication record and abstract](https://profiles.wustl.edu/en/publications/test-enhanced-learning-taking-memory-tests-improves-long-term-ret/).

Product inference: insert recall or explanation opportunities after substantive ideas, and revisit them later using changed examples. Do not treat readability ratings as evidence of learning.

### 4. Active learning has broad classroom support

Freeman et al. (2014) synthesized 225 undergraduate STEM studies. Active learning improved examination/concept-inventory scores by 0.47 standard deviations on average; students in lecture conditions were approximately 1.5 times as likely to fail. This is a meta-analysis of varying classroom interventions, not a controlled comparison of generated text layouts or an AI-specific effect. [Paper abstract](https://pubmed.ncbi.nlm.nih.gov/24821756/).

Product inference: prioritize learner actions with meaningful feedback over adding more explanatory text. The precise interaction design still needs product evaluation.

### 5. Alternate examples and practice; connect concrete and abstract

The US Institute of Education Sciences practice guide (2007) recommends spacing, alternating worked solutions with independent problems, integrating graphics and verbal explanations, connecting concrete and abstract representations, retrieval quizzes, and deep explanatory questions. Its evidence ratings differ: moderate for example/problem alternation, spacing, graphics, and concrete/abstract integration; strong for quiz re-exposure and explanatory questions; minimal for pre-questions. This is an expert synthesis, not one new experiment. [Official guide and evidence ratings](https://ies.ed.gov/ncee/wwc/practiceguide/1).

Product inference: retain worked examples, follow them with a near-transfer attempt, and ask why a step works. Add visuals when they explain a relation or process, not as decoration. Do not insist every lesson follow identical counts or question types.

### 6. Segmenting evidence has boundary conditions

Mayer's first-party account of the segmenting principle reports better transfer from learner-paced segments than continuous narrated animations in three tests, particularly for complex, fast presentations and inexperienced learners. These were multimedia messages, not scrollable prose. [Author's Cambridge chapter](https://www.cambridge.org/core/books/abs/multimedia-learning/segmenting-principle/37240877DDA0362355ADB39936027982).

A later original study, *Short, Long, and Segmented Learning Videos*, compared video presentations with 22 participants and reported greater learning gains for segmented variants. Its small sample and video setting limit generalization. [Primary study](https://link.springer.com/article/10.1007/s10758-024-09745-2).

Product inference: use meaningful conceptual boundaries and learner control; prototype expandable depth and interleaved checks. Evidence supports investigating chunking, not claiming that all lessons must fit 200 words or that shorter is always better.

## Recommended evaluation

Compare the current lesson format with a version that interleaves explanations, examples, attempts, and feedback. Keep subject, learning objective, and content coverage comparable. Use blinded human judgments of accuracy, coherence, specificity, unnecessary repetition, and appropriate challenge; separately measure unaided transfer immediately and delayed recall/transfer after several days. Track time and hint/reveal use as supporting measures. This is an evaluation proposal inferred from the outcome distinctions above, not an established Hermes result.

## Remaining uncertainty

These sources do not show that conversational wording or removal of stock AI phrases independently improves learning. Editorial quality and instructional effectiveness should be judged separately. AI trials tested carefully constructed tutoring systems, whereas Hermes generates broader lessons; local evaluation is required before promising equivalent effects. No universal prose length, number of screens, or retrieval frequency is justified by the studies reviewed.

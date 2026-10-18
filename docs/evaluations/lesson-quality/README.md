# Generated lesson quality benchmark

This benchmark compares saved lesson outputs from two versions of the authoring guidance. It provides six fixed requests, original source fixtures, case-specific checks, a human rubric and an offline blinding helper. It does not call a model, execute lesson code, grade learners or claim that a writing style produces learning gains.

Use this alongside [tool/host evaluation](../tutoring.md). Preview lessons and the bundled reference lessons are authored fixtures, not live-model results. The reference examples use different topics from these cases to reduce direct answer copying.

## Capture comparable runs

1. Choose a baseline and candidate plugin snapshot. Keep the provider, model, source material, learner request, learner level and intent identical. Freeze available generation settings, record settings the host does not expose as `"unavailable"`, and capture at least three fresh samples per case. Start fresh tutor sessions in disposable Learning stores for each sample. Do not use daily courses as fixtures.
2. Before generating each variant, record the authoring fingerprint from that checkout. Keep the case file byte-identical in both checkouts. If an older checkout lacks this helper, run a copy there or compute the same hashes with the helper copied into its `dev` directory. The fingerprint includes the prompt module, teaching skill, Humanizer skill and Markdown reference resources. It identifies file contents, including uncommitted edits; it does not prove that a host loaded those files.

   ```sh
   python3 -B dev/lesson_quality.py fingerprint > /tmp/lesson-candidate-fingerprint.json
   ```

3. In an isolated actual host, generate each case with its specified level and intent. Attach each source excerpt verbatim as a text file named for its fixture title. For the continuity case, use the fixture as the previous milestone and verify the lesson continues its code. Keep `review_checks` out of the model request. The concise case must retain its explicit no-exercise request. Record the actual supplied fixture names/locators in the run log.
4. Export each saved lesson's `content`, `teaching`, `practice`, `source_ids`, and any `visual` without rewriting them. If a lesson contains an asset or diagram that depends on its store, retain a rendered capture for the reviewer and record its location separately; this helper only presents the JSON/text. Remove private context/session/job IDs and credentials. Preserve source IDs used in lesson prose and supply the corresponding source-title mapping to reviewers. Do not use private source text in a committed report.
5. Keep a local capture per variant using the format below. Copy the fingerprint fields into `run`. Record the provider/model actually used, not merely requested defaults. Retain raw outputs, elapsed time, model/tool errors, actual skill-loading evidence and available usage/cost in a separate coordinator log. If a generation fails, report it; do not quietly drop it or substitute a successful output. The helper requires matching completed pairs and refuses an incomplete case set. Report missing/failed samples alongside any partial findings, then rerun the complete comparison when they are resolved.

Capture shape (replace the illustrative metadata and lesson with actual output):

```json
{
  "run": {
    "provider": "actual-provider",
    "model": "actual-model",
    "revision": "commit-from-fingerprint",
    "authoring_sha256": "64-lowercase-hex-characters-from-fingerprint",
    "cases_sha256": "64-lowercase-hex-characters-from-fingerprint",
    "settings": {"temperature": "unavailable", "max_tokens": "unavailable"}
  },
  "lessons": [
    {
      "case_id": "queue-beginner",
      "sample": 1,
      "lesson": {
        "content": "Actual saved lesson Markdown",
        "source_ids": [],
        "teaching": {"outcome": "Actual outcome", "prerequisites": [], "misconception": "Actual misconception"},
        "practice": null
      }
    }
  ]
}
```

Include every case ID in `cases.json`, with sample numbers 1, 2 and 3 for both variants. `practice:null` is valid for an explicit no-exercise request; most other cases should include a complete practice object. The helper checks capture completeness and comparison metadata, not the full publication schema or the truth of self-reported provenance.

## Prepare a blinded review

```sh
python3 -B dev/lesson_quality.py compare \
  --baseline /tmp/lesson-baseline.json \
  --candidate /tmp/lesson-candidate.json \
  --output /tmp/lesson-review-01
```

The helper randomizes A/B separately for each case/sample pair. It withholds run labels and metadata from `review.md` and saves the mapping, capture hashes and run metadata in `key.json`. Give reviewers only `review.md`, plus needed media captures/source mappings. Keep the key until reviewers finish. Content or style may still reveal a variant; this is label blinding, not a guarantee of reviewer ignorance. The helper refuses mismatched provider/model/settings, changed case fixtures, missing/duplicate samples and an existing output directory.

## Review rubric

For each dimension, assign **0** when the lesson fails it, **1** when it needs revision, or **2** when it meets the criterion. Cite the passage or missing step that supports the judgment.

| Dimension | Meets the criterion |
| --- | --- |
| Correctness and sources | Technical claims and quantities are correct under stated assumptions; citations support attributed claims; hypothetical behavior is labeled. |
| Alignment | Outcome, explanation, worked example, optional exercise, criteria and solution agree. |
| Reasoning | The worked example exposes decisions and intermediate state; required concepts appear before use. |
| Application | Optional practice tests a meaningful changed condition rather than exact wording; explicit requests for no exercise are respected. |
| Pacing and prose | Each section contributes to the outcome; no padded opening, repeated metadata or repetitive recap; necessary depth and limits remain. |

Record central factual errors, wrong solutions, unsupported central claims and fabricated execution separately as hard defects. Do not average them away in a total score. Prefer a dimension-by-dimension comparison and an A/B/tie/neither decision with reasons. Do not reject an otherwise correct lesson merely for being long, having a heading, or using a specific word. A checkable outcome matters more than an AI-writing detector score.

Have two reviewers assess a subset when possible; record disagreements. Unblind after reviews, summarize preference, dimension ratings, hard defects, failures and latency/cost. Keep illustrative content separate from actual generated samples. Suggested report fields: date, snapshots/fingerprints, provider/model/settings, case/sample coverage, source setup, loading evidence, observations with excerpts, limitations and next action. There is no scientifically calibrated pass threshold here. Accept an authoring change only after checking that it introduces no unresolved central correctness defect and provides a defensible improvement across the reviewed cases.

## Learning outcomes require a separate evaluation

These reviews assess generated teaching material. To evaluate learning, ask consenting learners to solve new problems without AI immediately afterward and again after a delay, with criteria set in advance. Record hints and reveals separately from unaided work. A next-day or next-week check is a practical pilot choice, not a proven optimal schedule. Keep completion, satisfaction, reviewer preference and retention as distinct outcomes.

Status: benchmark tooling and authored fixtures only. No baseline-versus-candidate live Hermes generation or learner study has been completed by adding these files.

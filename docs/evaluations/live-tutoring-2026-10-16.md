# Live tutoring evaluation — 16 October 2026

Two narrowly scoped conversations exercise the actual Hermes CLI, configured model, plugin tools, and temporary learning store. These observations establish behavior in the tested conversations; they do not measure learning gains or general teaching quality.

## Setup

- Host: Hermes source `d923a5eb487a17c0a68801bba9ef0f56c81040a8`, existing Python 3.11 environment.
- Provider/model: the user's configured `openai-codex` / `gpt-6.1-sol-900k`.
- Baseline plugin: committed `8c212c70bdc23d924c57caf4e92eebc002b6696e`.
- Preloaded skill: **`hermes-learning:learning-teach`**, the registered name, not the `teach` directory name.
- Each case has a new temporary operating-system HOME, HERMES_HOME, plugin copy, database, and session. The host's home and global-root helpers were checked before running.
- The only configured toolset is `learning`. The host also supplies its `tool_describe` metadata helper. No terminal, browser, research, or messaging tools are enabled by the evaluation.
- Each conversation permits at most 8 tool-calling iterations and a **110-second** run budget. An outer process timeout starts termination at 120 seconds; cleanup may finish afterward. There is no `--yolo` flag.
- Credential handling copies only one sufficiently unexpired access token into an access-only OAuth pool entry in the temporary home. No refresh token, daily environment file, broad configuration, hooks, or external-login adoption is copied. Temporary auth files are removed after runs. The daily auth file was byte-identical before and after each completed run.
- Temporary directories are private (0700) and outputs/auth files are private (0600). Raw prompts, IDs, logs, and database evidence remain in the owned temporary evaluation directory; capabilities are omitted from this report.

Invocation shape:

```text
hermes chat --query-file <private-prompt-file> --oneshot -Q --format stream-json \
  --toolsets learning --skills hermes-learning:learning-teach \
  --max-turns 8 --run-budget 110
```

The baseline teaching-skill SHA-256 is `f1756c296f91106a7cf324e824fccf1bb01eb4474338d45ddf2a99acb4783f07`.

## Cases and baseline observations

### Explanation without enrollment or practice

Prompt: “Explain idempotency for a backend engineer in two short paragraphs, using a payment retry example. I only want the explanation right now: no quiz, exercise, tracked learning, or saved learning records.”

The baseline returned two paragraphs covering an ambiguous payment response, reuse of an idempotency key, atomic handling of concurrent retries, rejection of changed parameters, and bounded retention guarantees. It asked no practice questions and made no tool calls. Database evidence contained zero tracks, runs, help events, attempts, or assessments. Exit code was 0; the CLI conversation took 15.4 seconds (27.9 seconds including process startup and teardown).

Assessment: the existing skill already respects this explanation-only request. A passing final run would preserve this behavior, not establish a new capability.

### Generated hint for an existing run

The harness used explicit human-channel actions to create and approve a track, author a payment-retry activity, and create its run. There was **no preauthored hint** at any level. These fixture records are test setup, not model-created enrollment or evidence of learner competence.

The learner request supplied the private context/run identifiers and said they assumed a missing response meant the payment failed. It requested one tailored targeted hint, recording the actual assistance if supported, and explicitly prohibited answer submission or assessment.

The baseline called `tool_describe` and then `learning_help` with level `targeted-hint`. The service returned `help_unavailable` with “No authored help at this level.” The tutor disclosed that it could not record the hint, then supplied:

> A missing response tells you what the client knows, not what the server did. Could the charge already be committed even though the client never received confirmation? Think about what the retry must let the server recognize.

The hint addresses the stated misconception without giving a worked solution. However, the learning database contained **zero help events** after the hint was shown. There were also zero attempts and assessments; the single seeded track/run remained. Exit code was 0; the conversation took 19.9 seconds (30.8 seconds including startup and teardown).

Assessment: this reproduces the assistance-recording discrepancy with a live model. Honest error disclosure does not preserve the content of the assistance in the evidence store.

## Infrastructure observation

The first explanation attempt ran in the restricted network sandbox. Its provider requests failed before any stream opened (`APIConnectionError` caused by connection errors), reported zero input/output tokens, and produced no assistant response or learning writes. The outer timeout terminated it; cleanup finished at 122.6 seconds. This is an infrastructure failure, not a tutoring result. The explanation case was then run once with approved network access; that successful result is the baseline above.

## Final comparison

The same two learner prompts and fixture setup were run against a freshly staged working-tree plugin after the implementation was ready. The final teaching-skill SHA-256 is `687ad1d86622804344ef57b300e33822a4a8b12d90407804d3558497f563e24f`.

| Case | Baseline | Final implementation |
| --- | --- | --- |
| Explanation-only request | Two paragraphs; zero tools or learning writes | Two paragraphs; zero tools or learning writes |
| Tailored generated hint | Authored-hint lookup fails; generated hint is shown but no assistance event is saved | Generated hint is saved successfully before it is shown |
| Exact help content preserved | No saved help content | Tool argument, tool return, stored event, and complete final assistant response are exactly equal |
| Learner answer/assessment boundary | Zero submissions and assessments | Zero submissions and assessments |

The final explanation described the ambiguous outcome, stable operation keys, atomic concurrent handling, and rejection of changed parameters. It did not include the baseline's retention-window caveat; both responses fit the requested two-paragraph scope. This small comparison does not establish a general improvement in explanation quality. The conversation took 15.2 seconds (24.5 seconds including startup and teardown), with exit code 0.

The final hint conversation called `tool_describe`, then `learning_help` with a stable request ID and generated content. There were no tool errors. It returned:

> No response means you don't know the outcome—not that the payment failed. Separate the server committing the charge from the client receiving confirmation: could one happen without the other? Before retrying, consider how the server could recognize “the same intended charge” rather than a new one.

Programmatic comparisons confirmed:

- The complete final assistant response equals the submitted, returned, and persisted hint text exactly, without trimming or paraphrase normalization.
- The event identifies the correct seeded run and activity, `level=targeted-hint`, `origin=generated`, `author_kind=chat-agent`, and `channel=chat_relayed`.
- The saved request ID equals the tool argument. Exactly one help event exists.
- The successful help-tool result preceded the first visible text event.
- No attempt or assessment was created. The fixture remained one track and one run.

The conversation took 21.9 seconds (32.5 seconds including startup and teardown), with exit code 0. All four successful runs completed within the configured budget. All temporary auth copies were removed; the daily auth file was unchanged during each run.

Result: the new generated-help contract closes the reproduced provenance gap in this live case while preserving the tested explanation-only and no-submission boundaries. Retry behavior, disclosure-policy enforcement, and other product paths require their separate deterministic and interface tests; this model sample does not prove them.

## Limits

These are scripted learner prompts answered by a live tutor, with one successful sample per case for each of the baseline and final snapshots. The tracked case supplies consent and records through deterministic setup. It does not establish natural discovery, multi-turn adaptation, objective diagnosis, assessment quality, cross-client handoff, messaging transport, or learning retention. Model nondeterminism and the small sample prevent broad claims about pedagogy.

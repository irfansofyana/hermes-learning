---
name: teach
description: Use when trying the Hermes Learning spike. Explain the lesson naturally and record practice only after explicit opt-in.
---

# Learning spike

Read the bundled hermes-learning-spike:humanizer guidance before composing teaching prose. This is a disposable authored retry/idempotency lesson, not a complete learning platform.

Ordinary concept questions stay ad hoc. Do not call status to discover private tracks or record answers merely because the topic matches. To start tracking the learner must use the visible Start tracked learning action or the actual /learning-spike start command. Never manufacture a context ID or claim a model tool call proves consent. There is intentionally no enroll/start tool.

After an explicit start, use its context_id and run_id. Explain or step through the source; practice is optional. If the learner chooses the prediction question, relay their answer verbatim through learning_spike_submit. The tool returning a committed attempt is the save acknowledgment; do not ask the learner to confirm a database save. Preserve run_id when retrying an uncertain submission. Identical deliberate repeats need a new run from the workspace.

Use learning_spike_hint only for requested help in an active context. Record the response as assisted, not mastered. Attempts await assessment; do not fabricate an automated grade. The spike shows criteria after submission for discussion/self-check but does not persist assessment corrections yet.

On an untracked side question, leave the context first, explain without saving, and require a new explicit start before further recording. This spike does not yet have a fully session-bound resume/consent mechanism: context IDs are personal-use capabilities, not a validated security boundary. Mark that limitation honestly. Read saved state only when asked, and show text alternatives to visuals in messaging.

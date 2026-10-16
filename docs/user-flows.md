# Learner flows

Learning starts with a useful lesson. The tutor lives beside it, using the configured Hermes model. Runtime verification and host limits are recorded in [compatibility](compatibility.md).

## Start with a topic, project, or sources

1. Open Learning and enter what you want to learn or build. For example: “Build a job queue in Go using these notes.”
2. Optionally choose a level; beginner is the default. Attach multiple text, Markdown, or code files, paste material, or add HTTP(S) source/repository links.
3. Check the material list. Unsupported or unreadable files remain visible with their individual errors. Remove or replace them, or proceed with the usable request and sources. Links begin marked as unread.
4. Choose **Generate learning path**. This saves the request and material and authorizes the configured model to prepare an outline and the first lesson.
5. Read the outline as it becomes available, then the complete first lesson. Generation begins from the supplied information without an initial interview or separate path approval.

A source-only request is supported. If there is neither a topic nor usable material or a source link, the input stays in place and the UI explains what is missing. PDF and image import are not supported. Source text is material to study, not code to execute.

The tutor chooses reasonable starting assumptions and displays them with the lesson. **Adjust assumptions** prepares a message to the tutor; it does not directly rewrite the saved outline. Project paths use milestones and concrete deliverables. Suggested commands and expected results must be distinguished from work actually run.

## Read, ask, and continue

- Select a lesson in the left outline. Saved lessons open immediately; selecting an ungenerated lesson explicitly starts its generation.
- Read the explanation and worked example. Optional practice does not block the rest of the lesson.
- Choose **Explain simply**, **Show an example**, or **Ask a question**. The tutor answers inside Learning with the selected lesson as context.
- Open **Source material** to inspect supplied text, locators, links, and retrieval status. An inaccessible repository or unsupported page remains visibly identified; usable material can still support a lesson.
- Choose **Mark as read** to record reading progress, or **Next lesson** to continue. Reading a lesson does not create an assessed attempt or establish mastery.

Desktop shows the path, lesson, and collapsible tutor together. On narrow screens, Path, Lesson, and Tutor tabs switch panels while preserving the draft and panel scroll state. The interface follows the host/system theme, with a theme control in its header.

Tutor requests use the configured Hermes session. Required tool permissions and clarifications appear in the tutor panel and wait for the learner's response; they are never silently approved.

## Return to saved work

Open Learning and choose **Continue** on a saved path. The workspace restores its last selected published lesson and its durable Hermes conversation. Continue establishes or recovers the learning context but does not send a new model prompt. Merely opening the home page only reads records.

Paths and tutor bindings are scoped to the backend's Learning store and profile. Desktop and web can use the same saved path when connected to that store. Switching backend/profile resets the active UI context and draft rather than submitting it to a different conversation. Unsubmitted drafts are not synchronized across devices.

## Stop, reconnect, or retry

**Stop** interrupts a running tutor response. Any outline, lesson, or source result already published remains saved. The current lesson can be generated again through an explicit retry when it was not completed.

If the connection drops after a request may have been accepted, Learning does not automatically resend it. Choose **Reconnect tutor** to restore the conversation and reconcile its state before sending another request. Provider, source, and publication errors remain visible. The request and usable inputs remain available after a failed start.

When returning to an unfinished generation job, the service recovers its authorizing context so the restored conversation can complete or stop that job. A new generation request is a deliberate action; it does not silently replace saved lessons.

## Existing practice and ordinary chat

**Learning records** opens the existing activities, sources, attempts, assessments, disputes, review queue, and detailed progress. Historical evidence remains intact. Submitting a practice answer saves it awaiting assessment; it does not automatically assign a grade. Hints, reveals, exact answers, criteria, and superseding feedback retain their existing evidence rules.

Ordinary educational chat outside Learning remains ad hoc unless the user explicitly starts or resumes tracked study. `/learning-track` remains available for that workflow. A side question is not an assessed attempt, and another chat does not inherit the workspace's context automatically. Host conversation retention is separate from Learning's records.

## Verification scenarios

| Scenario | Expected behavior |
| --- | --- |
| Topic with no attachments | One Generate action produces an ordered outline and a complete first lesson |
| Project plus multiple files | Usable text informs lessons; supplied locators remain available |
| Unsupported file or inaccessible repository | Individual failure remains visible; usable request/material is preserved |
| Simpler explanation or example | A response appears in the embedded tutor, without a chat handoff |
| Reload and Continue | Last published reading position and the correct conversation return without a new prompt |
| Stop, failed publication, or lost acknowledgement | Saved results survive; retry/reconnect is explicit and uncertain prompts are not automatically replayed |
| Backend/profile change | Old events and drafts cannot attach to another store or path |
| Reading and ordinary tutor chat | No automatic assessment, mastery claim, or practice attempt |

The labelled development preview exercises these UI and persistence flows with simulated responses. It does not establish real-model teaching quality or host gateway compatibility.

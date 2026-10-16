# Learner flows

Learning starts with a useful lesson. The tutor lives beside it, using the configured Hermes model. Runtime verification and host limits are recorded in [compatibility](compatibility.md).

## Start with a topic, project, or sources

1. Open Learning and enter what you want to learn or build. For example: “Build a job queue in Go using these notes.”
2. Optionally choose a level; beginner is the default. Attach multiple text, Markdown, or code files, or add HTTP(S) source/repository links.
3. Check the material list. Unsupported or unreadable files remain visible with their individual errors. Remove or replace them, or proceed with the usable request and sources. Links begin marked as unread.
4. Choose **Generate learning path**. This saves the request and material and authorizes the configured model to prepare an outline and the first lesson.
5. Read the outline as it becomes available, then the complete first lesson. Generation begins from the supplied information without an initial interview or separate path approval.

A source-only request is supported. If there is neither a topic nor usable material or a source link, the input stays in place and the UI explains what is missing. PDF and image import are not supported. Source text is material to study, not code to execute.

The tutor chooses reasonable starting assumptions and displays them with the lesson. **Adjust assumptions** prepares a message to the tutor. The tutor can propose an update for review; the saved path changes only after **Apply changes**. Project paths use milestones and concrete deliverables. Suggested commands and expected results must be distinguished from work actually run.

## Read, ask, and continue

- Select a lesson in the left outline. Saved lessons open immediately; selecting an ungenerated lesson explicitly starts its generation.
- Read the explanation and worked example. Optional practice does not block the rest of the lesson.
- Choose **Explain simply**, **Show an example**, or **Ask a question**. The tutor answers inside Learning with the selected lesson as context.
- Open **Source material** to inspect supplied text, locators, links, and retrieval status. An inaccessible repository or unsupported page remains visibly identified; usable material can still support a lesson.
- Choose **Mark as read** to record reading progress, **Mark as unread** to reset that lesson, or **Next lesson** to continue. Reading a lesson does not create an assessed attempt or establish mastery.

Desktop shows the path, lesson, and collapsible tutor together. On narrow screens, Path, Lesson, and Tutor tabs switch panels while preserving the draft and panel scroll state. The interface follows the host/system theme, with a theme control in its header.

Tutor requests use the configured Hermes session. Required tool permissions and clarifications appear in the tutor panel and wait for the learner's response; they are never silently approved.

## Change a lesson or roadmap

Ask the embedded tutor directly: “Rewrite this lesson with a simpler example,” “Adjust the upcoming roadmap for my project,” “Add lessons about deployment,” or “Regenerate this path for an intermediate learner.” The edit controls prepare requests in the same tutor. There are no copied commands, separate interviews or records pages.

The tutor prepares a proposal. Review its summary, roadmap differences, changed or new lesson content, and effect on read markers. Choose **Apply changes** to save it, or dismiss it to keep the current path. A proposal alone does not change the saved lesson or outline. Ordinary questions such as “Explain this more simply” receive a chat answer without changing the path.

Rewriting lessons preserves untouched lessons and their read markers; changed lessons become unread and removed lessons leave the path. Extending a path keeps all existing lessons and progress. Regenerating replaces the lessons and resets reading progress to the new first lesson. All three keep the supplied sources and tutor conversation.

Pending proposals return after reload. If the path changed after a proposal was prepared, applying it reports a conflict and leaves the current path intact; request a fresh proposal against the updated path. Applying one proposal makes other pending proposals stale. Finish or stop active lesson generation before proposing or applying an update. A failed operation keeps the current saved content and shows the error.

## Return to saved work

Open Learning and choose **Continue** on a saved path. The workspace restores its last selected published lesson and its durable Hermes conversation. Continue establishes or recovers the learning context but does not send a new model prompt. Merely opening the home page only reads records.

Paths and tutor bindings are scoped to the backend's Learning store and profile. Desktop and web can use the same saved path when connected to that store. Switching backend/profile resets the active UI context and draft rather than submitting it to a different conversation. Unsubmitted drafts are not synchronized across devices.

## Stop, reconnect, or retry

**Stop** interrupts a running tutor response. Any outline, lesson, or source result already published remains saved. The current lesson can be generated again through an explicit retry when it was not completed.

If the connection drops after a request may have been accepted, Learning does not automatically resend it. Choose **Reconnect tutor** to restore the conversation and reconcile its state before sending another request. Provider, source, and publication errors remain visible. The request and usable inputs remain available after a failed start.

When returning to an unfinished generation job, the service recovers its authorizing context so the restored conversation can complete or stop that job. A new generation request is a deliberate action; it does not silently replace saved lessons.

## Practice and ordinary chat

Practice is optional and stays beside the lesson in the tutor conversation. Ask for an exercise, discuss an answer, or request a hint without starting a separate activity, submitting a graded attempt, or opening a records page. Read markers record reading, not mastery.

Educational chat outside Learning remains ordinary chat. Open Learning to create a saved path. Manual track approvals, `/learning-track` commands, the review queue, and copied tutor requests are retired. Legacy records are discarded rather than imported into the new experience; current paths and their lessons continue normally. Host conversation retention is separate from Learning data.

## Verification scenarios

| Scenario | Expected behavior |
| --- | --- |
| Topic with no attachments | One Generate action produces an ordered outline and a complete first lesson |
| Project plus multiple files | Usable text informs lessons; supplied locators remain available |
| Unsupported file or inaccessible repository | Individual failure remains visible; usable request/material is preserved |
| Simpler explanation or example | A response appears in the embedded tutor, without a chat handoff |
| Reload and Continue | Last published reading position and the correct conversation return without a new prompt |
| Stop, failed publication, or lost acknowledgement | Saved results survive; retry/reconnect is explicit and uncertain prompts are not automatically replayed |
| Rewrite, roadmap revision, extension, or regeneration | Summary and preview appear; only Apply changes updates the saved course |
| Dismiss or reload a proposal | Dismiss preserves current content; reload restores pending proposals |
| Stale proposal or failed update | Error is visible and current lessons remain intact |
| Backend/profile change | Old events and drafts cannot attach to another store or path |
| Reading and ordinary tutor chat | No automatic assessment, mastery claim, or practice attempt |

The labelled development preview exercises these UI and persistence flows with simulated responses. It does not establish real-model teaching quality or host gateway compatibility.

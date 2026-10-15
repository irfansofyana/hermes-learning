# ADR 003: Explicit tracking opt-in

Status: accepted product direction; host enforcement mechanism remains a feasibility question.

## Decision

Ordinary educational chat is ad hoc. Persist learning-plugin records only after explicit start/resume intent in a scoped conversation or workspace activity. A vague topic, long lesson, source upload, matching track, automatic skill load, or opening an overview is not consent to enroll.

Ad hoc assistance can include discovery, explanations, source research, and visuals. It creates no plugin learning records or automatic private-track lookup. Host history, provider processing, and user-requested files remain subject to their separate retention rules.

Promoting a conversation previews the brief and selected context and requires approval for import. No full-transcript import or retrospective grading. Permission to persist an exploration is separate from approval of its proposed path and source-sharing policy.

## UX and lifecycle

Show the active track/exploration in desktop/web, announce it in chat, and provide Leave tracked learning. Side questions do not silently become attempts. Untracked exchanges/exit stop updates in that context until explicit resume, retaining existing records. Other chats do not inherit tracking globally. An optional offer is made at most once after a relevant transition; a decline suppresses unsolicited offers for that conversation.

## Enforcement and validation

The learning service checks a valid active context for mutations, including rejection of late writes after exit. The host-authorized entry mechanism is unverified and must be probed; a model boolean or prompt instruction is not an enforcement boundary. Test ad hoc zero writes, selective promotion, tracked responses versus side questions, context isolation, and exit/reentry in real agent and UI flows. See R10 in the requirements.

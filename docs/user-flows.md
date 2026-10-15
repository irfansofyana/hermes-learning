# Proposed learner flows

Status: proposed product behavior, not runtime-tested plugin integration. Ordinary educational chat is ad hoc; explicit tracking opt-in precedes plugin persistence. Earlier standalone HTML/PNG diagrams omit this boundary and should not be treated as the current complete flow.

## 1. Choose whether to keep a learning record

```mermaid
flowchart TD
    A[Ask a question or explore an interest] --> B[Help normally in ad hoc chat]
    B --> C{Want an ongoing learning record?}
    C -->|No or not requested| D[Continue chat without plugin writes]
    C -->|Explicitly start or save| E{Import earlier discussion?}
    E -->|Yes| F[Preview brief and selected context]
    F --> G{Approve import?}
    G -->|No| D
    G -->|Yes| H[Enter visible tracked exploration]
    E -->|No| H
    H --> I[Discover a direction or approve a small path]
    J[Explicitly resume a saved track] --> K[Enter visible tracked context]
    K --> L[Resume from backend-saved state]
```

This is a user decision, not a question that the agent must ask on every turn. An occasional offer may occur when continuing study becomes useful; a decline suppresses repeat offers in that conversation. Topic, depth, opening a workspace, and loading a skill do not authorize persistence. Normal Hermes conversation history still applies.

## 2. Discover a direction inside tracked exploration

```mermaid
flowchart TD
    A[Explicitly start tracked exploration from a vague topic, goal, or source] --> B{Need help finding a direction?}
    B -->|Yes| C[Discuss motivation and background one question at a time]
    C --> D{Can the learner choose?}
    D -->|Not yet| E[Offer plain-language orientation and concrete examples]
    E --> F[Suggest a small reversible starting direction]
    D -->|Yes| G[Draft a provisional learning brief]
    F --> G
    B -->|No| G
    G --> H[Recommend a few starting materials with verification status]
    H --> I[Review scope, assumptions, and materials]
    I -->|Adjust| G
    I -->|Decline| M[Keep exploring or leave tracking]
    I -->|Approve| J[Begin one learning activity]
    J --> K{Does this direction fit?}
    K -->|Revise| G
    K -->|Continue| L[Continue the study and practice loop]
```

The same discovery conversation can happen ad hoc, but only opted-in exploration is saved in the plugin. Persistence opt-in does not approve the proposed learning path. Discovery is not an examination, and uncertainty is valid. A clear goal/source can skip the interview. Ask for a suggested starting point without completing a questionnaire.

## 3. Study, ask side questions, and leave

```mermaid
flowchart TD
    A[Explicitly resume tracked activity] --> B[Read, visualize, or trace code]
    B --> C{What do you want next?}
    C -->|Answer the activity| D[Explain, predict, or apply]
    C -->|Untracked side question| E[Answer without learning-record updates]
    E --> F{Explicitly resume tracking?}
    F -->|Yes| B
    F -->|No| G[Continue ordinary chat]
    D --> H{Need help?}
    H -->|Yes| I[Record hint or reveal in tracked context]
    I --> D
    H -->|Ready| J[Commit answer and assistance provenance]
    J --> K[Await assessment, self-check, or request agent review]
    K --> L[Inspect criteria, feedback, and uncertainty]
    L --> M{Agree with assessment?}
    M -->|No| N[Dispute with correction history]
    N --> L
    M -->|Yes| O[Continue, review later, or leave tracking]
    O -->|Continue| B
    O -->|Leave| G
```

A side question is not automatically an attempt. If the learner's intent is unclear, ask before recording evidence. Leaving stops new writes in that context without deleting or archiving the track. Existing committed records remain. A different chat stays ad hoc until explicitly resumed; another deliberately active workspace context is independent and labeled.

## Cross-client continuity

After explicit opt-in, committed exploration and activity context can resume in chat, desktop, or web. Switching clients is not automatic enrollment of unrelated conversations. Local unsubmitted drafts do not synchronize across devices. Messaging uses text alternatives; interactive diagrams live in the workspace. The backend rejects late mutations against exited tracking contexts.

## Acceptance scenarios

- **Ad hoc beginner:** "I am curious about distributed systems but know nothing about it." Help clarify direction and suggest materials without a plugin record. A decline of tracking does not cause repeated offers.
- **Promote selectively:** preview and approve selected discussion before saving it as discovery notes. Do not import the full conversation or grade earlier statements.
- **Tracked beginner:** explicitly start tracked exploration, then save unresolved questions and assumptions before a path is approved. Resume in another client and recheck direction after the first activity.
- **Exit:** ask "just explain this; don't track it," receive the explanation without progress updates, and explicitly resume if desired. Leaving does not erase prior data; late writes are rejected.

# Proposed learner flows

Status: product flows derived from requirements; not runtime-tested plugin behavior. Discovery precedes the earlier goal/source setup diagrams when the learner is unsure what to study.

## 1. Discover a direction

```mermaid
flowchart TD
    A[Start with a vague topic, goal, or source] --> B{Need help finding a direction?}
    B -->|Yes| C[Discuss motivation and background one question at a time]
    C --> D{Can the learner choose?}
    D -->|Not yet| E[Offer plain-language orientation and concrete examples]
    E --> F[Suggest a small reversible starting direction]
    D -->|Yes| G[Draft a provisional learning brief]
    F --> G
    B -->|No| G
    G --> H[Recommend a few starting materials with reasons and verification status]
    H --> I[Review scope, assumptions, and materials]
    I -->|Adjust or decline| G
    I -->|Approve| J[Begin one learning activity]
    J --> K{Does this direction fit?}
    K -->|Revise| G
    K -->|Continue| L[Continue the study and practice loop]
```

The learner can ask for a suggested starting point without completing a questionnaire. A speculative direction remains a proposal until explicitly accepted. Discovery is not an examination. A clear goal/source can skip the interview. The saved exploration is available in chat, desktop, and web before a track is active.

## 2. Study and practice

```mermaid
flowchart TD
    A[Resume approved brief and current activity] --> B[Read a source, inspect a diagram, or trace code]
    B --> C[Explain, predict, or apply]
    C --> D{Need help?}
    D -->|Yes| E[Record hint or reveal and continue]
    E --> C
    D -->|Ready| F[Commit answer and assistance provenance]
    F --> G[Await assessment, self-check, or request agent review]
    G --> H[Inspect criteria, feedback, and uncertainty]
    H --> I{Agree with assessment?}
    I -->|No| J[Dispute and preserve a correction history]
    J --> H
    I -->|Yes| K[Continue, revisit, or pause]
    K --> L[Return later with a new review example]
```

At any committed checkpoint, switch clients and resume the same server-owned record. Local unsubmitted drafts do not synchronize across devices. Text alternatives keep the activity usable in messaging; interactive diagrams live in the desktop/web workspace.

## Concrete acceptance scenario

A learner says "I am curious about distributed systems but know nothing about it." The agent explores what sparked the interest. If the learner cannot answer, it explains a few concrete situations and offers a provisional starting point. It proposes a small brief plus verified references or clearly unverified candidates, obtains approval, and begins an introductory activity. Afterward the learner can revise the direction. Pausing during discovery must preserve the unanswered question and assumptions without creating a mastery score or inventing consent.

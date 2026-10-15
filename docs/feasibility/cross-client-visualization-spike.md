# Cross-client visualization spike

Status: proposed; not executed. Installing test plugins or restarting host services requires separate approval.

## Question

Can real desktop and web Hermes plugins display the same interactive learning artifact and share saved attempts with an agent tool on the deployed backend?

## Probe

Use one authored lesson on retry/idempotency with a permitted short source excerpt. Store its structured sequence diagram on the backend. Provide Previous/Next controls, source references, a text alternative, and a single prediction question. Submit an answer through one client or agent tool, then read it from the other interfaces.

## Pass criteria

- Load actual desktop and dashboard plugins without app-core edits.
- Authenticated plugin GET and POST reach the correct deployment/profile.
- Tools and UI use the same persistent service/store across host module boundaries.
- Diagram controls work in both clients, including resize and keyboard operation.
- Save an attempt in chat and observe it in desktop and web after refresh.
- Repeat a submission with the same key; store one attempt.
- Restart the backend with approval; persisted state remains readable.
- Show failure/offline status instead of a false saved state.
- Report installed Hermes versions, artifacts, commands, and observed failures.

## Exclusions

Full document ingestion, model-generated code, production deployment, complete curriculum UI, and committing throwaway code as a finished plugin. Report findings before deciding what to retain.

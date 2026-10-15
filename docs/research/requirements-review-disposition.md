# Requirements review disposition

Status: recommendations incorporated into a revised draft, pending user review. No implementation approval.

## Review provenance

Independent read-only review through `claude-subscription-directsdk-experimental`, requesting and receiving `claude-opus-5-5` in both the initial response and its continuation. The reviewer received requirements, architecture, product brief, capability research, feasibility brief, and README. It did not run the plugin or independently validate host capabilities.

## Adopted

- Define activity/visual authorship, pending UI assessment, self-check versus agent assessment, and deferred service inference (R0).
- Pre-attempt versioned criteria, solution gating, explicit assistance events, answer capture provenance, uncertain/disputed grading, separate conceptual/practical evidence (R3/R5).
- Source correspondence checks, edition/commit/hash provenance, explicit model-sharing policy, and protected derived content (R2).
- Schema-only model-authored visual data, bounded fixed renderers, source references, and deterministic text step lists (R4).
- Explicit learning entry, resume brief, saved checkpoints, workspace links, copyable chat handoff, and text alternatives (R7).
- Server-issued submission identities, concurrency/migrations, store identity, API compatibility, local drafts, and interruption recovery (R8).
- Source-content trust boundaries, target-bound confirmations, backups, compatibility checks, and layered deterministic/agent/manual tests (R9/validation).

## Modified or rejected

- **Defer desktop:** rejected as a scope change. Desktop stays in feasibility and the first usable version; work may be sequenced.
- **Goal-first only:** rejected. Both entry points stay; curated source-first does not require automatic whole-book ingestion.
- **Answer-hash/time-window deduplication:** replaced with server-issued submission identity. Identical intentional attempts are valid.
- **Failed quote becomes interpretation:** replaced with rejection or explicit unverified status; a failed match does not validate a paraphrase.
- **Universal 48-hour independence threshold:** not adopted as fact. Record timing/type/assistance; policies remain transparent heuristics.
- **Ban all destructive agent tools:** replaced with narrow validation and explicit confirmation. No bulk destructive capability is required initially.
- **Full three-artifact packaging prescription:** preserve a coordinated compatibility contract, but let actual host packaging probes determine physical artifacts.

## Remaining decisions

Choose a messaging runtime and explicit scheduling/payload-limit policies before implementation. Probe actual host auth, rendering, cross-process store ownership, and tool-use reliability. Raw-message capture, backend inference, PDF ingestion, and deep links remain unverified or deferred. Neither this review nor the documents establish a security or educational-efficacy guarantee.

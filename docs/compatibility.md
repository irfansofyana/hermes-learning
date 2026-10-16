# Compatibility and verification boundaries

## Integrated workspace (current)

The current Desktop and web plugin generates a path and first lesson from a topic, project, or supplied material, then keeps the tutor beside the lesson. It uses the configured Hermes model through public host conversation APIs. Continue restores the saved lesson position and durable conversation; the primary workflow requires no slash commands or chat switching.

Verified against the local Hermes v0.22.2 checkout at `d923a5eb487` in isolated profiles:

- A real configured model generated a two-lesson outline and published the first lesson through the learning tools in the actual web dashboard. The generation job completed and the conversation binding persisted.
- The actual Electron plugin reopened that web-created lesson and conversation, sent a follow-up to the live model, and received its answer inside Learning. No page errors occurred in either check.
- The preview browser check exercises project/source input, lesson generation, chat, next lesson, read progress, reload/Continue, and mobile dark layout using a **labelled simulated tutor** against the real store. Separate checks covered Stop/retry and failed source retrieval.
- Regression tests cover cancelled preparation, uncertain delivery, reconnect, missing conversations, source policy, idempotent publication, and preservation of legacy assessed evidence.

The host bootstrap required the existing temporary `Path` annotation workaround described below. The daily Hermes installation was not changed or restarted. Live checks used a temporary access-only credential copy and did not copy refresh credentials.

Supported source imports are UTF-8 text, Markdown, and code, plus pasted passages and HTTP(S) source/repository links. Links begin unread; retrieval depends on host reading tools. Retrieval status is agent-reported, not independent verification. PDF/image ingestion, automatic repository execution, offline model work, multi-user authorization, and arbitrary host versions are not supported by this verification. Published lessons and outlines are immutable; requesting different assumptions changes the tutor conversation rather than rewriting the saved path.

Desktop uses `host.request` and `host.onEvent`; web uses an authenticated host WebSocket. Approval and clarification requests require explicit learner responses. Conversation bindings are scoped to the learning store/profile; context capabilities remain revocable permissions rather than authenticated conversation identities. The current manifest declares 21 tools.

## Earlier implementation evidence

The sections below document earlier record-management and chat-handoff releases. References to path approval, 17 tools, or preparing commands describe those releases and the retained **Learning records** view, not the current primary experience.

Hermes Learning targets the plugin registration and dashboard extension APIs inspected in the local Hermes source at commit `d923a5eb487` on 2026-10-16. Source inspection is not a claim that this release was installed or exercised in every host. The daily instance was not installed into, restarted, or modified.

## Adapter contract

The backend plugin ID is `hermes-learning`; the dashboard tab path is `/learning`. Dashboard API routes are relative to the host's authenticated plugin API namespace. `plugin_api.py` loads the runtime by file location, so it does not require the dashboard loader to supply Python package context. Backend registration uses `register_command`, `register_tool`, and `register_skill`, with signatures checked against local host source.

Every operation resolves `plugins.plugin_storage.plugin_data_dir('hermes-learning') / 'data.db'` afresh. The inspected host helper resolves the active Hermes profile on each call. No store singleton caches a previous profile. Dashboard and model tools must run against the same intended profile to share records. Do not point clients at different stores and assume they will reconcile.

Reads: `GET /state`, `/track/{id}`, `/activity/{id}?context_id=…`, `/source/{id}`, and human-facing `/export`. Mutations use `POST /action` with `{ "action": "…", "params": {}, "api_version": 1 }`. The envelope rejects extra fields, string/bool API versions and unsupported versions. Runtime action schemas reject unsupported keys and bound strings, arrays and structured visuals before service dispatch. Domain validation also guards identifiers, track ownership, revisions and source policy.

HTTP uses `ui_direct`; model tools use `chat_relayed`. There are no model start, resume, approve, recommendation-decision, track-status, review-rescheduling or export tools. Model tools can propose candidate resources, check quotes against policy-permitted stored text, and append immutable activity revisions; only the human workspace accepts or declines recommendations. Source-read and quote-check tool results carry explicit untrusted-content annotations. `/learning-track start <topic>`, `/learning-track resume <track-id>`, `/learning-track approve <context-id> <revision>`, `/learning-track leave <context-id>`, and `/learning-track status` are explicit user commands. Agent assessments cannot claim self attribution. A copied chat handoff does not send a message or automatically run a model.

## Consent and disclosure limits

Contexts are revocable capabilities, not authenticated session identities. They are not bound to a CLI session, messaging conversation, browser tab or user principal. Keep context IDs private, do not reuse them across unrelated conversations, and leave a context when finished. The tool registry forwards optional trusted `session_id` keyword arguments, but the slash command callback accepts only raw argument text. The inspected gateway binds a route `session_key` before invoking a command, before a durable session entry exists; CLI command dispatch supplies no identity argument. The public session getter falls back to process environment. These are not a proven common identity at both consent and mutation, so the adapter does not bind to a guessed ID or to whichever model first presents a context. A host bridge supplying the same authenticated session identity at both points is required for enforceable session binding. Multi-user deployment needs a separate identity and authorization design.

Source reads apply disclosure policy for the model channel. The human workspace can inspect its saved source text. State/track/resume summaries do not expose context capabilities or hidden solution keys. JSON export is a safe records export, not a full recovery backup. Use the service's SQLite backup operation for full recovery; no unrestricted backup/export capability is registered as a model tool.

The host must provide authentication and enforce trusted human access to the dashboard namespace. This adapter does not independently authenticate the `ui_direct` channel. An authenticated user capable of calling workspace routes has the same learning permissions as the human UI. Local preview authentication and origin checks are separate development-host behavior.

## Evidence and remaining checks

- Python service and adapter tests run with temporary stores. Adapter tests cover registration, withheld start/resume/approve/export tools, per-operation profile resolution, strict version/envelope checks, actual source filtering, submission channel/assistance, assessment attribution, and direct FastAPI endpoint behavior.
- The inspected host virtual environment provides FastAPI 0.133.1 and Pydantic 2.13.4. The API model uses a compatibility configuration branch for Pydantic v1, but v1 has not been exercised. System Python without FastAPI skips HTTP adapter tests explicitly.
- On 2026-10-16 the service/adapter/preview suite passed with loopback sockets permitted. In the restricted sandbox the four preview HTTP tests cannot bind sockets. This is an environment restriction, not a successful transport check; the successful rerun used temporary stores with no daily-host changes.
- Direct endpoint tests do not establish real Hermes dashboard mounting, host authentication, or tool dispatch through an active agent. Actual isolated host discovery and registry dispatch were additionally exercised as described below. Prior disposable-spike evidence does not establish those properties for this implementation.
- Real dashboard loading and Electron loading/writes were subsequently verified as described below. Real messaging command dispatch, per-session consent binding, and coordinated enable/disable behavior still need dedicated release verification. A desktop shell needs the compatible plugin backend available; a copied UI bundle does not provide a server or inference runtime.

The bundled teaching and prose guidance is original project text. The Humanizer-named adaptation is not a vendored third-party skill and does not claim an upstream project's identity or license; its provenance statement is included in the skill itself.


## Isolated host runner

`dev/hermes.py` stages the allowlisted release files from the repository root into an explicitly owned temporary Hermes home. Its default root is `/tmp/hermes-learning-runtime`; a nonempty directory without the runner ownership marker is refused. It launches the existing host Python environment with a fresh operating-system HOME, fresh HERMES_HOME, minimal environment and no inherited daily credentials. It never installs dependencies or modifies host source. Supply `--source /path/to/hermes-agent` and optionally `--home /tmp/your-isolated-run` to `prepare`, `inspect`, `command`, `tool`, or `serve --port 8878`.

On 2026-10-16, `prepare` and `inspect` against `/tmp/hermes-learning-host-check` loaded the actual host plugin manager: the plugin enabled without errors, registered 17 tools and one `learning-track` command, and both bundled skills were readable through the real skill resolver. An explicit `command 'start Isolated host verification'` followed by real-registry `tool learning_state '{}'` read the same saved track. These are deterministic command/registry checks, not a live model or messaging conversation.

Real inspection found that `/learning` is already a built-in command alias in this host, and Hermes correctly refused to register a conflicting plugin command. The plugin now uses `/learning-track`. The dashboard tab remains `/learning`; source inspection found no matching built-in tab route collision (the host's `/api/learning` REST namespace is separate).

The default isolated dashboard startup failed during the host's FastAPI lifespan: `tui_gateway/methods_onboarding.py:71` references an undefined `Path` in an evaluated annotation. A temporary bootstrap under `/tmp` added only the missing `pathlib.Path` import to that module at test time. This allowed the real host to start on loopback. The installed host source, product plugin, and default runner were not patched. These runtime results therefore apply to the tested host with that specific bootstrap defect compensated; an unmodified checkout containing the defect still needs its host fix before serving.

## Actual frontend verification, 2026-10-16

Tested local source: `d923a5eb487`; native shell reports Hermes Desktop and backend **v0.22.2**. No claim is made about every Hermes release or arbitrary proxy topology.

| Surface | Observed result |
| --- | --- |
| Host authentication | Anonymous plugin-state GET returned 401; authenticated GET returned 200. |
| Real dashboard | `/learning` mounted through the actual dashboard plugin registry, using its React and authenticated `fetchJSON`. UI start → brief → path approval succeeded. Authored source/activity fixtures added through the authenticated API rendered correctly; diagram navigation and UI submission exposed the post-submission criteria. No page errors or alerts. |
| Real Electron | A copied existing desktop build loaded the ESM bundle through the native disk-plugin loader and official SDK. Learning navigation, connected backend state, track creation/proposal/approval, source reads and sequence controls worked. |
| Cross-client evidence | Desktop read the answer saved in web, then submitted its own answer and self-assessment to the same backend. Both persisted across an Electron restart; the real web UI then read the desktop-created answer. |
| Consent and lifecycle | Explicit desktop resume and leave worked. Navigating away removed the workspace root; returning remounted it. Owned Electron/Xvfb processes were stopped and checked for survivors. |
| Embedded layout | The final sequence rendered at 378px in a 378px reading container. Desktop plugin root width and scroll width were both 1020px. The isolated shell was 1280×880. |
| Preview QA | 1440×960 light/dark and 390×844 layouts; drafts restored on reload; hint → answer → self-assessment → dispute → review deferral → leave passed. Small screens use a readable sequence step panel and the same text alternative. |

Electron opt-in was set in isolated local storage; clicking the native Capabilities switch was not the enabling path tested. First-run provider onboarding was dismissed using the host's “I'll choose a provider later” action. No provider was configured, and no live model or messaging call was made. Desktop `host.state.profile` is a profile string and `host.state.gateway` is a connection-status string; the adapter remounts on these transitions, and the shared client additionally checks backend store identity.

The copied desktop source imports only `react` and `@hermes/plugin-sdk`; the web build uses the host's full React object (19.2.7 in the inspected web runtime), including `useId`. Build targets externalize host React. Code and teaching skills are packaged separately from test data, tokens and developer dependencies.

Initial implementation verification: 39 backend/adapter/preview/packaging tests, 5 workspace recovery/validation tests, 10 historical spike Python tests, and 6 historical recovery checks passed. Both production bundles built and passed JavaScript syntax checks. Browser fault injection confirmed that a lost response retried exactly once, revoked-context rejection retained editable answer text, and accepted recommendations could be attached as curated sources.

## Learning-loop verification, 2026-10-16

The follow-up implementation adds schema-1 capability flags rather than requiring a storage migration. Historical rows lacking objective links, learner preferences, generated-help content or criterion results remain readable without read-time writes. The UI checks capabilities before sending new fields. Review policy v2 follows linked objectives; unlinked activities retain policy v1.

| Check | Observed result |
| --- | --- |
| Deterministic evaluation | All three `dev/evaluate.py` scenarios passed: explicit entry/ad hoc boundary; diagnosis → generated help → answer → feedback → next activity; and restricted nested source content. These checks make no model calls. |
| Workspace browser | Real preview flow created three linked example activities, saved authored assistance and a verbatim answer, restored a draft after reload, saved three criterion judgments plus uncertainty, displayed objective progress, scheduled reviews, and suggested another activity. Switching activities kept drafts separate. No page errors. |
| Setup and authoring | Optional background/goal/minutes survived proposal approval. A new diagnostic practical activity retained its objective link and code-trace schema. Future trace steps remained hidden until explicit solution reveal. |
| Source import | A selected Markdown file was previewed without a write, then attached by the explicit Add source action. Invalid UTF-8 was rejected without creating a source. Helper tests additionally cover unsupported formats, binary content and limits. |
| Layout and visuals | Sequence, state-machine and code-trace views rendered in the preview. Light desktop and 390×844 dark layout checks passed without horizontal page overflow. |
| Native tutor handoff | Actual isolated Electron opened a new draft containing only the single-line resume command. It sent nothing. Returning to Learning recovered the command and second tutor request verbatim. An earlier unsent native draft remained in host persistent storage. Zero page errors, host sessions/messages, learner answers or assessments were created. No provider was configured. The same temporary host `Path` workaround described above was required. |
| Live tutor behavior | Two baseline and two final CLI conversations used the configured model in isolated homes. Baseline reproduced a generated hint with no saved event. Final saved the exact hint before showing it; tool argument, return, stored event and final response matched. Explanation-only cases made no learning writes. See the [live evaluation report](evaluations/live-tutoring-2026-10-16.md) for isolation, model, observations and limits. |

The native handoff prepares two separate messages because Hermes parses the entire slash-command argument. The learner sends the resume command first, waits for confirmation, then copies the tutor request into the same conversation. This check establishes composer preparation and recovery, not a complete live tutoring exchange through Electron. Messaging transports and conversation-bound authorization remain outside this verification.

The repeatable browser check is `dev/check-workspace.mjs`; its setup and fresh-store requirement are documented in [dev/README.md](../dev/README.md). Full suite/build/package results for this pass are recorded in the [implementation plan](superpowers/plans/2026-10-16-learning-loop.md).

## Repository URL installation

The original development layout stored the release files under `plugin/`. Hermes Desktop's Git installer checks the selected package root for `plugin.yaml` plus `__init__.py`, and for `plugin.js` or `desktop/plugin.js`. It does not automatically search arbitrary nested folders. Consequently, installing the plain repository URL returned “No agent or desktop plugin artifacts found in this repository,” even though the separately packaged ZIP worked.

The installable files now live at the repository root. This follows the layout used by [hermes-blogwatcher](https://github.com/irfansofyana/hermes-blogwatcher). A nested layout is also valid when the install identifier explicitly selects it, as [hermes-otel's installation instructions](https://github.com/briancaffey/hermes-otel#install) do with `/hermes_otel`; the previous Learning README did not provide that distinction. The `v0.1.0-rc.1` tag retains the old layout; the fix is on `main`.

The actual local Hermes detector reproduced `agent=false, desktop=false` before the change and detects both afterward. The isolated host loads 17 tools, one command and both teaching skills from the relocated package. All 63 Python tests pass, including a new repository-root packaging regression. `dev/check-install.mjs` supports both local detection and a fresh Git clone/desktop installation into a temporary directory, so future release checks can cover the repository URL rather than only a manually staged package.

The host admission validator additionally required the manifest to declare the 17 registered tools. Its security scan flagged a literal adversarial prompt in the evaluation checklist; that case is now described without quoting the attack instruction. All admission checks, including capability probing, desktop surface checks and the security scan, pass. The validator still reports non-blocking private-import warnings for the development host runners and historical spike; production plugin modules use the public integration surface.

## Product limits

- Conversation-bound consent needs a verified Hermes identity bridge. Current contexts are revocable private capabilities, not authenticated conversation identities. This is a personal single-user plugin.
- Chat authoring uses Hermes tools; no new backend inference, search service, PDF ingestion, repository execution, or automatic full-book processing is included.
- Reference verification is author-reported. Source protection follows declared source references; it cannot retrospectively retract content already shared with a model.
- Review uses a transparent 1/3/7-day heuristic: policy v2 follows linked objectives, while unlinked legacy activities retain policy v1. Evidence summaries are not calibrated mastery or retention estimates.
- Generated-help capture requires the tutor to use the help tool before giving assistance. Teaching quality and actual messaging-channel behavior need ongoing evaluation; skill loading alone does not prove adherence.
- Native chat preparation depends on the inspected desktop composer API, preserves existing drafts, and does not send messages. Arbitrary remote/proxy topologies, offline writes, multi-user operation, and all-version host support are not claimed.

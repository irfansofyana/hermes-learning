# Hermes plugin capability research

Status: documentation-backed research; runtime compatibility remains unverified.

## Sources

- [Agent plugin API](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins)
- [Desktop SDK](https://hermes-agent.nousresearch.com/docs/developer-guide/desktop-plugin-sdk)
- [Dashboard extensions](https://hermes-agent.nousresearch.com/docs/user-guide/features/extending-the-dashboard)
- [Plugin model access](https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access)

## Documented surfaces

The agent API provides tools, skills, hooks, and plugin storage. Desktop provides React-based contributions such as panes, routes, and navigation. Dashboard has a separate frontend plugin system. Both frontend systems can reach plugin backend routes under `/api/plugins/<id>`; their SDKs and delivery are not interchangeable.

Desktop disk plugins load plain ESM and restrict imports to the SDK and supported React modules. They are not a general npm application environment. Desktop documentation covers canvas sizing and inline transcript directives. Equivalent custom inline web-chat behavior has not been established in this research.

## Proposed visualization approach

Render validated structured data through controlled SVG/HTML components; do not accept executable model-provided markup. Start with one step-through sequence diagram. Do not assume Mermaid, React Flow, D3, or arbitrary npm imports work unchanged. SVG feasibility is an inference from the rendering surface, not a runtime result; the actual component must be exercised in both hosts.

## Constraints and probes

- Prove tools and HTTP routes access the same profile-scoped store across actual host module loading, not merely unit-test imports.
- Verify authenticated GET/POST calls over remote connections.
- Desktop installation on a client is separate from backend deployment.
- Desktop plugin sockets have a documented OAuth-remote limitation; keep polling fallback.
- Plugins run with substantial authority; error isolation is not security isolation.
- PDF extraction, figure fidelity, source locators, session targeting, and visualization interaction need runtime probes.
- Use host-owned inference where supported; measure latency and disclose retries/fallbacks. Do not promise one facade call equals one provider attempt.

## Evidence categories

Documentation-backed: extension points listed above.
Proposed: shared learning service, schema, frontend layout, visual components.
Unverified: complete packaging/install flow, shared rendering implementation, remote compatibility, and all product acceptance tests.

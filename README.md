# Hermes Learning

A personal learning workspace for Hermes Agent: source-grounded study, interactive visualizations, and practice across desktop, web, and chat.

**Status: research and requirements draft. No runnable plugin exists yet.**

Start with a vague curiosity, a concrete goal, or a source. The agent helps clarify your direction and recommend starting materials. Learn concepts through books and papers, investigate them in real repositories, and apply them in projects. Keep conceptual understanding separate from implementation success and record how much assistance an activity required.

## Intended architecture

One learning service and persistent store on the deployed Hermes backend. Agent tools, a desktop plugin, and a web-dashboard plugin access that service. Teaching skills guide the agent; clients do not own learning state.

This is a personal, single-user deployment. Public source code does not imply public learning data or a multi-user hosted service.

## Documents

- [Draft requirements](docs/requirements.md)
- [Learner flows, including discovery](docs/user-flows.md)
- [Product brief](docs/product-brief.md)
- [Architecture proposal](docs/architecture.md)
- [Related projects](docs/research/related-projects.md)
- [DeepTutor study](docs/research/deeptutor-study.md)
- [Hermes extension research](docs/research/hermes-plugin-capabilities.md)
- [Backend state decision](docs/decisions/001-backend-owned-learning-state.md)
- [Interface decision](docs/decisions/002-desktop-web-and-chat-interfaces.md)
- [Feasibility spike](docs/feasibility/cross-client-visualization-spike.md)

Requirements and architecture require review before implementation. Documented host capabilities are not a runtime compatibility guarantee. Do not upload copyrighted books, personal records, deployment secrets, or credentials to this repository.

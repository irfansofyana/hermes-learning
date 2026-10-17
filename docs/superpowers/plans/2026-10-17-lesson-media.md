# Lesson diagrams and images implementation plan

**Goal:** Render Mermaid first, Archify second, and durable images third inside saved lessons, tutor messages, and proposal previews.

**Architecture:** Keep diagram source and attachment references in lesson Markdown. Bundle Mermaid with the client. Run a pinned, bundled Archify renderer on the backend against validated JSON and display its static SVG using an image context; never execute generated HTML. Store bounded PNG/JPEG imports in the profile SQLite database and fetch them through authenticated JSON actions, including on remote desktops.

**Constraints:** Work on main. Do not restart Hermes or make live model calls. No public uploads or CDN dependencies. Preserve existing structured visuals and revision consent. Node 18+ is required on the backend for Archify, not on the Mac. Retain sources and show actionable rendering failures.

- [x] Mermaid: pinned dependency, strict rendering, SVG sanitization, code/source fallback, zoom and enlarged view; browser checks for malformed and hostile content.
- [x] Archify: vendor pinned MIT renderer and license; bounded subprocess and JSON input; no remote brands, repository inspection, or generated scripts; test all five diagram kinds and missing runtime.
- [x] Images: context-scoped import tool, type/size/dimension validation, durable bytes, track-scoped reads, inline references in lessons and proposals; test cross-track and invalid-file rejection, restart persistence, and idempotency.
- [x] Teach tools/skill updated to publish actual media references; authenticated provider shared by lesson, tutor, practice, and review Markdown.
- [x] Validate backend and UI suites, build desktop/dashboard artifacts, exercise real renderers in isolated browser, update compatibility/packaging notices, commit and push main.

Validation: all five pinned Archify fixtures render to well-formed SVG; real browser checks cover Mermaid, Archify, deleted-original image persistence, proposal previews, malformed/forbidden sources, enlarge/zoom, reload, mobile and no external requests. No Hermes service restart or live-model call.

<img src="ui/src/learning-mark.svg" width="64" height="64" alt="Hermes Learning winged book logo">

# Hermes Learning

A personal learning workspace for [Hermes Agent](https://github.com/NousResearch/hermes-agent). Turn a topic, project, or your own material into lessons, ask a tutor inside the workspace, and continue from saved work.

## What you can do

- **Start learning immediately.** Enter what you want to learn or build, optionally choose a level, and generate an outline and a complete first lesson.
- **Bring your own material.** Attach multiple text, Markdown, or code files, or add source and repository links. Each source shows whether its text is available or retrieval failed.
- **Read and ask in one place.** Follow lessons with formatted Markdown, tables, highlighted code you can copy, and step-by-step sequence diagrams, state machines, or code traces. Ask for a simpler explanation or another example beside the lesson.
- **Change a saved path.** Ask the tutor to rewrite a lesson, adjust the roadmap, add lessons, or regenerate the path. Review the summary and preview, then choose **Apply changes** or dismiss it. Ordinary questions leave saved lessons unchanged.
- **Continue later.** Reopen your last lesson and its tutor conversation. Generate later lessons when you select them.

Updates keep your sources and tutor conversation. Unchanged lessons keep their read markers; rewritten lessons clear theirs, and regeneration resets reading progress.

The tutor uses your configured Hermes model and credentials. Generating a path saves your request and supplied material and sends shared material to that model. Opening Learning alone does not start a model turn. Read markers help you return to a lesson; practice and questions stay in the tutor conversation.

## Install

In Hermes Desktop, open **Install plugin** and paste:

```text
https://github.com/irfansofyana/hermes-learning
```

Enable Learning under **Capabilities → Plugins → Desktop**. The connected Hermes backend also needs the agent component enabled. Built UI files are included on `main`, so no build is needed to install.

For a remote backend, install there too, then restart its dashboard/API server:

```sh
hermes plugins install https://github.com/irfansofyana/hermes-learning --enable
```

Open Learning and enter a topic or project. Desktop and web use the same saved work when connected to the same backend and profile.

## Status

This is an early, personal-use plugin. File import supports UTF-8 text, Markdown, and code; PDF and image import are not available. Links remain unread until retrieval succeeds. Source citations do not independently verify a claim, and reading progress is not a mastery score. Visuals are optional, bounded walkthroughs supplied by the tutor; arbitrary diagram markup and code execution are not supported.

See [compatibility and known limits](docs/compatibility.md) for verified host behavior and remaining work. The local development preview labels its simulated tutor output explicitly.

## More

- [Development and testing](dev/README.md)
- [Data and recovery](docs/data-and-recovery.md)
- [Learner flows](docs/user-flows.md) and [teaching quality](docs/teaching-quality.md)
- [Product requirements](docs/requirements.md) and [architecture](docs/architecture.md)

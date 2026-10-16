<img src="ui/src/learning-mark.svg" width="64" height="64" alt="Hermes Learning winged book logo">

# Hermes Learning

A personal learning workspace for [Hermes Agent](https://github.com/NousResearch/hermes-agent). Study a topic, practise what you learn, and return to your saved work across desktop, web, and chat.

## What you can do

- **Plan your study.** Start with a question, a goal, or a source. Review the proposed learning path before approving it.
- **Learn from your own material.** Add text, Markdown, or code excerpts, and choose what the tutor can read.
- **Practise with feedback.** Work through explanations, predictions, code traces, and build exercises. Save answers, hints, and assessments together.
- **Explore diagrams.** Step through sequences, state machines, and code traces alongside the lesson.
- **Pick up where you left off.** Review progress, revisit scheduled objectives, and resume a track in chat.

Tracking starts when you choose to start or resume a learning track. Ordinary educational chat stays ad hoc. Saving an answer leaves it awaiting assessment; it does not automatically call a model or assign a grade.

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

Open Learning to start a track, or use `/learning-track` in chat. Desktop and web share saved work when connected to the same backend and profile.

## Status

This is an early, personal-use plugin tested with Hermes v0.22.2. Progress reflects saved practice and feedback; it is not a calibrated mastery score. See [compatibility and known limits](docs/compatibility.md) for tested behavior and remaining work.

## More

- [Development and testing](dev/README.md)
- [Data and recovery](docs/data-and-recovery.md)
- [Learner flows](docs/user-flows.md) and [teaching quality](docs/teaching-quality.md)
- [Product requirements](docs/requirements.md) and [architecture](docs/architecture.md)

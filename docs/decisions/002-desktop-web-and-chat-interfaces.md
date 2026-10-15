# ADR 002: Desktop, web, and chat interfaces

Status: accepted product direction; interface details proposed.

Provide desktop and web learning workspaces and tools/skills for ordinary Hermes chat. Essential track, practice, evidence, and resume actions must work in text. Rich visualization lives in the workspaces with text alternatives; identical inline chat rendering is not required.

Desktop and dashboard use different SDKs and delivery mechanisms. Maintain separate host adapters over shared backend contracts. Treat remote desktop installation and connection routing as explicit acceptance tests. No frontend may own independent authoritative progress.

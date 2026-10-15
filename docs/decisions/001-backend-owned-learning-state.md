# ADR 001: Backend-owned learning state

Status: accepted product direction; implementation details proposed.

Keep all durable learning records and artifacts on the canonical Hermes deployment, scoped to its selected profile. Desktop, web, and agent tools use the same service. Client-local data is limited to presentation preferences and disposable caches.

This avoids separate databases and synchronization logic. It requires network connectivity, concurrency handling, server backups, and explicit disconnected states. Replication between independent Hermes deployments and offline writes are outside initial scope.

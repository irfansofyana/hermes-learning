# Data and recovery

The backend resolves the active profile's `plugin_data_dir('hermes-learning')/data.db` on every operation. SQLite uses WAL, guarded schema initialization, transactions and revision checks. The desktop and web clients must point to that same backend/profile.

Drafts are private to the browser/desktop origin, scoped by store, track and activity, and labeled unsubmitted. They persist in local storage until cleared; they are not encrypted, synchronized between devices, or authoritative evidence. Session tracking selection is separate from drafts. Failed delivery retains the exact answer/run identity; definitive rejections preserve editable text. Explicitly abandoning an uncertain retry warns that another attempt may duplicate a previously delivered answer.

JSON export is a human-readable safe view, **not a full backup**. Use `Store.backup(new_path)` with an existing protected destination directory for a consistent complete SQLite snapshot. Stop writers before restoring the complete database; do not replace a live database while WAL files are in use. No arbitrary backup/restore path is exposed to the agent or web API.


# Data and recovery

Learning stores paths, source material, lesson outlines and content, generation jobs, read markers and tutor bindings in the active backend profile's `plugin_data_dir('hermes-learning')/data.db`. SQLite uses WAL and transactional writes. Desktop and web must connect to the same backend/profile to share this data. Hermes owns the actual tutor conversation history.

The retired records interface is removed. Its unsubmitted practice drafts, navigation state and copied chat requests are discarded from each client's local/session storage when Learning opens. They are not imported into the new tutor.

To discard old backend records, stop Learning writers and run the cleanup against an explicit database path:

```sh
python3 -B dev/retire_legacy.py /path/to/plugin-data/hermes-learning/data.db
python3 -B dev/retire_legacy.py /path/to/plugin-data/hermes-learning/data.db --apply
```

The first command reports counts without changes. `--apply` permanently removes legacy-only tracks and their related records, plus old practice/evidence records attached to newer courses. It does not make a backup or migrate old records into lessons. Current courses, lessons, sources, generation jobs, read markers and tutor bindings remain. It does not delete host-owned conversations or other plugins' data.

For a full backup of current Learning data, use `Store.backup(new_path)` with an existing protected destination directory. Stop writers before restoring a complete database; do not replace a live database while WAL files are in use. No arbitrary backup/restore/delete path is exposed as a model tool or web action. JSON export is a safe view rather than a complete recovery backup.

#!/usr/bin/env python3
"""Discard the retired activity experience from one explicit Learning database.

Dry-run by default. --apply permanently deletes legacy tracks and practice
records, including those attached to a newer course. Courses, lessons, source
material, generation jobs, reading position and tutor bindings remain intact.
No backup or migration of the retired records is made. Stop Learning writers
before applying. Hermes conversation history is owned by the host, not this DB.
"""
import argparse
import json
from pathlib import Path
import sqlite3

LEGACY_KINDS = ('activity', 'attempt', 'assessment', 'review', 'dispute', 'help', 'run', 'recommendation')


def retire_legacy(path, *, apply=False):
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise ValueError('Select an existing Learning database file')
    db = sqlite3.connect(path.as_uri() + ('?mode=rw' if apply else '?mode=ro'), uri=True, timeout=15)
    try:
        db.execute('BEGIN IMMEDIATE' if apply else 'BEGIN')
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if db.execute('PRAGMA user_version').fetchone()[0] != 1 or not {'metadata', 'records'} <= tables:
            raise ValueError('Not a supported Learning database')
        if not db.execute("SELECT value FROM metadata WHERE key='store_id'").fetchone():
            raise ValueError('Missing Learning store identity')
        legacy_tracks = [row[0] for row in db.execute("SELECT id FROM records WHERE kind='track' AND track_id NOT IN (SELECT track_id FROM records WHERE kind='course')")]
        legacy_track_ids = set(legacy_tracks)
        candidates = [(ident, kind, tid) for ident, kind, tid in db.execute('SELECT id,kind,track_id FROM records') if kind in LEGACY_KINDS or tid in legacy_track_ids]
        result = {'tracks': len(legacy_tracks), 'records': len(candidates)}
        if apply:
            db.executemany('DELETE FROM records WHERE id=?', [(row[0],) for row in candidates])
            db.commit()
        return result
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        result = retire_legacy(args.database, apply=args.apply)
    except (ValueError, sqlite3.Error) as exc:
        parser.error(str(exc))
    print(json.dumps({'applied': args.apply, **result}))


if __name__ == '__main__':
    main()

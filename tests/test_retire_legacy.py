import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from learning_store import Store
from dev.retire_legacy import retire_legacy


class RetireLegacyTests(unittest.TestCase):
    def test_delete_legacy_tracks_and_practice_without_migrating_them_into_courses(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.db'
            store = Store(path)
            old = store.dispatch('start', {'title': 'Old activity track'})
            new = store.dispatch('course_start', {'title': 'Current path', 'intent': 'topic', 'level': 'beginner', 'request_id': 'new-path'})
            with sqlite3.connect(path) as db:
                for kind in ('activity', 'attempt', 'assessment', 'review', 'dispute', 'help', 'run', 'recommendation'):
                    for tid in (old['track_id'], new['track_id']):
                        ident = f'{kind}-{tid}'
                        db.execute('INSERT INTO records(id,kind,track_id,data) VALUES(?,?,?,?)', (ident, kind, tid, json.dumps({'id': ident, 'track_id': tid})))
                db.execute('INSERT INTO records(id,kind,track_id,data) VALUES(?,?,?,?)', ('lesson', 'lesson', new['track_id'], '{"id":"lesson"}'))
                before = db.execute('SELECT * FROM records ORDER BY seq').fetchall()
                keep = [r for r in before if r[3] == new['track_id'] and r[2] not in ('activity','attempt','assessment','review','dispute','help','run','recommendation')]
            preview = retire_legacy(path)
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute('SELECT * FROM records ORDER BY seq').fetchall(), before)
            self.assertEqual(preview['records'], len(before) - len(keep))
            self.assertEqual(retire_legacy(path, apply=True), preview)
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute('SELECT * FROM records ORDER BY seq').fetchall(), keep)
            self.assertEqual(retire_legacy(path, apply=True), {'tracks': 0, 'records': 0})
            self.assertEqual(Store(path).store_id, store.store_id)

    def test_missing_or_unrelated_database_is_never_created_or_changed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'missing.db'
            with self.assertRaises((ValueError, sqlite3.Error)):
                retire_legacy(path, apply=True)
            self.assertFalse(path.exists())
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE unrelated(value TEXT)')
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                retire_legacy(path, apply=True)
            self.assertEqual(path.read_bytes(), before)

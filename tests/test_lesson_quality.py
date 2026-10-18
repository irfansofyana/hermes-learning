"""Offline benchmark pairing and reviewer blinding, not model quality tests."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'dev/lesson_quality.py'


class LessonQualityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cases = self.root / 'cases.json'
        self.cases.write_text(json.dumps({'version': 1, 'cases': [
            {'id': 'retry', 'request': 'Explain retry safety', 'review_checks': ['Distinguish timeout from failure']}
        ]}))
        self.run = {'provider': 'fixture-provider', 'model': 'fixture-model', 'revision': 'fixture-revision',
                    'authoring_sha256': 'a' * 64, 'cases_sha256': hashlib.sha256(self.cases.read_bytes()).hexdigest(),
                    'settings': {'temperature': 0.2}}
        self.lesson = {'content': 'The server may have committed.', 'source_ids': [],
                       'teaching': {'outcome': 'Predict a retry', 'prerequisites': [], 'misconception': 'Timeout is not rollback.'},
                       'practice': None}

    def capture(self, filename, content, **changes):
        capture = {'run': dict(self.run), 'lessons': [{'case_id': 'retry', 'sample': sample, 'lesson': {**self.lesson, 'content': content}} for sample in (1, 2, 3)]}
        capture.update(changes)
        path = self.root / filename
        path.write_text(json.dumps(capture))
        return path

    def compare(self, baseline, candidate):
        return subprocess.run([sys.executable, '-B', str(SCRIPT), 'compare', '--cases', str(self.cases),
                               '--baseline', str(baseline), '--candidate', str(candidate), '--output', str(self.root / 'review')],
                              text=True, capture_output=True)

    def test_pairs_saved_lessons_without_exposing_run_labels_to_reviewer(self):
        baseline = self.capture('baseline.json', 'Baseline body ```text\nexample\n```')
        candidate = self.capture('candidate.json', 'Candidate body')
        result = self.compare(baseline, candidate)
        self.assertEqual(result.returncode, 0, result.stderr)
        review = (self.root / 'review/review.md').read_text()
        key = json.loads((self.root / 'review/key.json').read_text())
        self.assertIn('Distinguish timeout from failure', review)
        self.assertIn('Baseline body', review)
        self.assertIn('Candidate body', review)
        self.assertNotIn('fixture-provider', review)
        self.assertNotIn(str(baseline), review)
        self.assertEqual(set(key['pairs'][0]['variants'].values()), {'baseline', 'candidate'})
        self.assertFalse(key['learning_effectiveness_evaluated'])

    def test_different_model_or_settings_cannot_masquerade_as_prompt_comparison(self):
        baseline = self.capture('baseline.json', 'A')
        for field, value in [('model', 'other'), ('provider', 'other'), ('settings', {'temperature': 1})]:
            with self.subTest(field=field):
                candidate = self.capture('candidate.json', 'B', run={**self.run, field: value})
                result = self.compare(baseline, candidate)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(field, result.stderr)
                self.assertFalse((self.root / 'review').exists())

    def test_missing_or_duplicate_samples_are_rejected(self):
        baseline = self.capture('baseline.json', 'A')
        original = json.loads(baseline.read_text())['lessons'][0]
        for lessons in [[], [{**original, 'sample': 2}], [original, original], [{**original, 'sample': True}]]:
            with self.subTest(lessons=lessons):
                candidate = self.capture('candidate.json', 'B', lessons=lessons)
                result = self.compare(baseline, candidate)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.root / 'review').exists())

    def test_changed_source_cases_are_rejected_before_creating_output(self):
        baseline = self.capture('baseline.json', 'A')
        candidate = self.capture('candidate.json', 'B', run={**self.run, 'cases_sha256': 'b' * 64})
        result = self.compare(baseline, candidate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('cases_sha256', result.stderr)
        self.assertFalse((self.root / 'review').exists())

    def test_existing_review_is_never_overwritten(self):
        baseline = self.capture('baseline.json', 'A')
        candidate = self.capture('candidate.json', 'B')
        self.assertEqual(self.compare(baseline, candidate).returncode, 0)
        before = (self.root / 'review/key.json').read_bytes()
        self.assertNotEqual(self.compare(baseline, candidate).returncode, 0)
        self.assertEqual((self.root / 'review/key.json').read_bytes(), before)

    def test_incomplete_lesson_is_rejected_instead_of_reviewed_as_complete(self):
        baseline = self.capture('baseline.json', 'A')
        for lesson in [{}, {**self.lesson, 'content': ''}, {**self.lesson, 'teaching': {}}, {**self.lesson, 'practice': {}}]:
            candidate = self.capture('candidate.json', 'B', lessons=[{'case_id': 'retry', 'sample': 1, 'lesson': lesson}])
            self.assertNotEqual(self.compare(baseline, candidate).returncode, 0)

    def test_fingerprint_captures_authoring_inputs_and_exact_source_cases(self):
        command = [sys.executable, '-B', str(SCRIPT), 'fingerprint', '--cases', str(self.cases)]
        result = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        fingerprint = json.loads(result.stdout)
        self.assertEqual(fingerprint['cases_sha256'], self.run['cases_sha256'])
        self.assertEqual(fingerprint['authoring_files']['skills/teach/SKILL.md'],
                         hashlib.sha256((ROOT / 'skills/teach/SKILL.md').read_bytes()).hexdigest())
        self.assertEqual(json.loads(subprocess.run(command, text=True, capture_output=True).stdout), fingerprint)
        self.cases.write_text(self.cases.read_text() + '\n')
        changed = json.loads(subprocess.run(command, text=True, capture_output=True).stdout)
        self.assertNotEqual(fingerprint['cases_sha256'], changed['cases_sha256'])

    def test_both_variants_omitting_replicates_cannot_pass_as_complete(self):
        baseline = self.capture('baseline.json', 'A')
        candidate = self.capture('candidate.json', 'B')
        for path in (baseline, candidate):
            data = json.loads(path.read_text())
            data['lessons'] = data['lessons'][:1]
            path.write_text(json.dumps(data))
        result = self.compare(baseline, candidate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('three', result.stderr)


if __name__ == '__main__':
    unittest.main()

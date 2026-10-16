import concurrent.futures
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

SPEC = importlib.util.find_spec('plugin.learning_store')
if SPEC:
    from plugin.learning_store import Store, LearningError


class LearningStoreTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(SPEC, 'learning store must be implemented')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'learning.db'
        self.store = Store(self.path, clock=lambda: datetime(2026, 10, 16, 12, tzinfo=timezone.utc))
        self.context = self.store.dispatch('start', {'title': 'Consensus', 'interest': 'Why replicas agree'})

    def call(self, action, channel='ui_direct', **params):
        return self.store.dispatch(action, {'context_id': self.context['context_id'], **params}, channel=channel)

    def activity(self, **extra):
        return self.call('activity', title='Predict', kind='prediction', prompt='Which node responds?', criteria='Identify quorum', solution='SECRET: majority', hints={'nudge': 'Count nodes', 'targeted-hint': 'Count votes', 'worked-step': 'Two of three'}, source_ids=[], **extra)['activity']

    def attempt(self):
        a = self.activity()
        r = self.call('run', activity_id=a['id'])
        return self.call('submit', run_id=r['run_id'], answer='Two nodes')['attempt']

    def test_reading_does_not_issue_context_and_leave_revokes(self):
        state = self.store.dispatch('state', {})
        self.assertNotIn('contexts', state)
        self.assertNotIn(self.context['context_id'], json.dumps(state))
        self.call('leave')
        with self.assertRaises(LearningError):
            self.call('brief', revision=1, brief='Changed', objectives=[])
        fresh = self.store.dispatch('resume', {'track_id': self.context['track_id']})
        self.assertNotEqual(fresh['context_id'], self.context['context_id'])

    def test_revision_and_cross_track_guards(self):
        self.call('brief', revision=1, brief='Understand quorum', objectives=['Explain votes'])
        with self.assertRaises(LearningError):
            self.call('approve', revision=1)
        self.call('approve', revision=2)
        a = self.activity()
        other = self.store.dispatch('start', {'title': 'Other'})
        with self.assertRaises(LearningError):
            self.store.dispatch('run', {**other, 'activity_id': a['id']})
        self.call('track_status', revision=3, status='paused')
        with self.assertRaises(LearningError):
            self.call('run', activity_id=a['id'])

    def test_keys_gated_and_attempt_is_immutable(self):
        a = self.activity(visual={'schema_version': 1, 'type': 'sequence', 'title': 'Votes', 'participants': [{'id': 'a', 'label': 'A'}, {'id': 'b', 'label': 'B'}], 'steps': [{'from': 'a', 'to': 'b', 'label': 'Question', 'explanation': 'Send'}, {'from': 'b', 'to': 'a', 'label': 'SECRET visual', 'explanation': 'Answer'}], 'visible_steps': 1})
        for action, params in [('state', {}), ('track', {'track_id': a['track_id']}), ('resume_brief', {'track_id': a['track_id']}), ('activity_read', {'activity_id': a['id']})]:
            self.assertNotIn('SECRET', json.dumps(self.store.dispatch(action, params)))
        run = self.call('run', activity_id=a['id'])
        first = self.call('submit', run_id=run['run_id'], answer='My answer')
        retry = self.call('submit', run_id=run['run_id'], answer='My answer')
        self.assertEqual(first['attempt'], retry['attempt'])
        self.assertTrue(retry['duplicate'])
        with self.assertRaises(LearningError):
            self.call('submit', run_id=run['run_id'], answer='Changed')
        unlocked = self.call('activity_read', activity_id=a['id'])
        self.assertEqual(unlocked['activity']['solution'], 'SECRET: majority')
        self.assertEqual(first['attempt']['status'], 'awaiting_assessment')
        self.assertEqual(first['attempt']['activity_version'], 1)

    def test_assistance_and_channel_are_preserved(self):
        a = self.activity()
        run = self.call('run', activity_id=a['id'])
        self.call('help', channel='chat_relayed', run_id=run['run_id'], level='targeted-hint')
        attempt = self.call('submit', run_id=run['run_id'], answer='Answer')['attempt']
        self.assertEqual(attempt['assistance'], 'targeted-hint')
        self.assertEqual(attempt['channel'], 'ui_direct')
        with self.assertRaises(LearningError):
            self.call('help', run_id=run['run_id'], level='full-solution-shown')
        run2 = self.call('run', activity_id=a['id'])
        attempt2 = self.call('submit', channel='chat_relayed', run_id=run2['run_id'], answer='Answer')['attempt']
        self.assertEqual(attempt2['assistance'], 'targeted-hint')
        self.assertTrue(attempt2['prior_help_exposure'])
        self.assertEqual(attempt2['channel'], 'chat_relayed')

    def test_source_policy_covers_derived_visual_and_export(self):
        s = self.call('source', title='Private', kind='notes', excerpt='PRIVATE TEXT', sharing='metadata-only')['source']
        self.assertEqual(self.store.dispatch('source_read', {'source_id': s['id']})['source']['excerpt'], 'PRIVATE TEXT')
        model = self.store.dispatch('source_read', {'source_id': s['id']}, channel='chat_relayed')
        self.assertNotIn('PRIVATE TEXT', json.dumps(model))
        a = self.call('activity', title='Private example', kind='explanation', prompt='PRIVATE TEXT', criteria='PRIVATE TEXT', solution='PRIVATE TEXT', hints=[], source_ids=[s['id']])['activity']
        for action, params in [('state', {}), ('track', {'track_id': a['track_id']}), ('activity_read', {'activity_id': a['id']}), ('resume_brief', {'track_id': a['track_id']}), ('export', {})]:
            self.assertNotIn('PRIVATE TEXT', json.dumps(self.store.dispatch(action, params, channel='chat_relayed')))

    def test_assessments_dispute_correction_and_review(self):
        attempt = self.attempt()
        self_a = self.call('assess', attempt_id=attempt['id'], method='self', feedback='My check', outcome='developing')['assessment']
        agent_a = self.call('assess', channel='chat_relayed', attempt_id=attempt['id'], method='agent', feedback='Check quorum', outcome='needs-work')['assessment']
        with self.assertRaises(LearningError):
            self.call('assess', attempt_id=attempt['id'], method='agent', feedback='Forged', outcome='demonstrated')
        self.call('dispute', assessment_id=agent_a['id'], reason='Incorrect assumption')
        corrected = self.call('assess', channel='chat_relayed', attempt_id=attempt['id'], method='agent', feedback='Correction', outcome='demonstrated', supersedes=agent_a['id'])['assessment']
        state = self.store.dispatch('state', {})
        self.assertEqual(len(state['assessments']), 3)
        self.assertIn(self_a['id'], [x['id'] for x in state['assessments']])
        review = state['reviews'][0]
        self.assertEqual(review['due_at'], '2026-10-23T12:00:00Z')
        self.assertEqual(review['assessment_id'], corrected['id'])
        self.assertEqual(review['policy_version'], 1)
        with self.assertRaises(LearningError):
            self.call('assess', channel='chat_relayed', attempt_id=attempt['id'], method='agent', feedback='Stale', outcome='needs-work', supersedes=agent_a['id'])
        self.call('review', review_id=review['id'], due_at='2026-11-01T12:00:00Z')
        self.assertEqual(self.store.dispatch('state', {})['reviews'][0]['due_at'], '2026-11-01T12:00:00Z')

    def test_concurrent_startup_and_submission_and_backup(self):
        a = self.activity()
        run = self.call('run', activity_id=a['id'])
        def submit(_):
            return Store(self.path).dispatch('submit', {'context_id': self.context['context_id'], 'run_id': run['run_id'], 'answer': 'Same'})
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(submit, range(12)))
        self.assertEqual(sum(not r['duplicate'] for r in results), 1)
        backup = Path(self.temp.name) / 'backup.db'
        self.store.backup(backup)
        restored = Store(backup).dispatch('state', {})
        self.assertEqual(restored, self.store.dispatch('state', {}))

    def test_future_schema_refused_without_modification(self):
        with sqlite3.connect(self.path) as db:
            db.execute('PRAGMA user_version=99')
        with self.assertRaises(LearningError):
            Store(self.path)
        with self.assertRaises(LearningError):
            self.call('brief', revision=1, brief='Bad migration', objectives=[])

    def test_independent_processes_initialize_once(self):
        fresh = str(Path(self.temp.name) / 'fresh.db')
        code = "from plugin.learning_store import Store; import sys; print(Store(sys.argv[1]).dispatch('state', {})['store_id'])"
        processes = [subprocess.Popen([sys.executable, '-B', '-c', code, fresh], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(6)]
        results = [p.communicate(timeout=20) for p in processes]
        self.assertTrue(all(p.returncode == 0 for p in processes), results)
        self.assertEqual(len({out.strip() for out, err in results}), 1)

    def test_cross_track_source_and_evidence_references_are_rejected(self):
        attempt = self.attempt()
        assessment = self.call('assess', attempt_id=attempt['id'], method='self', feedback='Check', outcome='developing')['assessment']
        review = self.store.dispatch('state', {})['reviews'][0]
        source = self.call('source', title='Text', excerpt='Source', kind='notes')['source']
        other = self.store.dispatch('start', {'title': 'Separate'})
        cases = [('assess', {'attempt_id': attempt['id'], 'method': 'self', 'feedback': 'Check', 'outcome': 'developing'}), ('dispute', {'assessment_id': assessment['id'], 'reason': 'No'}), ('review', {'review_id': review['id'], 'due_at': '2026-11-01T00:00:00Z'}), ('activity', {'title': 'Bad', 'kind': 'trace', 'prompt': 'p', 'criteria': ['c'], 'solution': 's', 'source_ids': [source['id']]})]
        before = self.store.dispatch('state', {})
        for action, params in cases:
            with self.assertRaises(LearningError):
                self.store.dispatch(action, {'context_id': other['context_id'], **params})
        self.assertEqual(before, self.store.dispatch('state', {}))

    def test_malformed_visual_returns_domain_error(self):
        with self.assertRaises(LearningError):
            self.activity(visual={'type': 'sequence', 'participants': [{'id': 'a', 'label': 'A'}], 'steps': [{'from': [], 'to': 'a', 'label': 'x'}]})

    def test_sources_default_to_curated_excerpts(self):
        source = self.call('source', title='Paper', kind='paper', excerpt='Curated paragraph')['source']
        self.assertEqual(source['sharing'], 'selected-excerpts')
        self.assertEqual(len(source['excerpt_hash']), 64)
        read = self.store.dispatch('source_read', {'source_id': source['id']}, channel='chat_relayed')
        self.assertEqual(read['source']['excerpt'], 'Curated paragraph')
        self.assertNotIn('excerpt', self.store.dispatch('state', {})['sources'][0])

    def test_recommendations_remain_separate_until_explicit_decision(self):
        recommendation = self.call('recommendation', channel='chat_relayed', title='Paper', url='https://example.com/paper', reason='Introduces quorum', prerequisites=['Basic networking'], verification='unverified', locator='Learner supplied section 2')['recommendation']
        self.assertEqual(recommendation['status'], 'candidate')
        state = self.store.dispatch('state', {})
        self.assertEqual(state['sources'], [])
        self.assertEqual(state['recommendations'][0]['id'], recommendation['id'])
        with self.assertRaises(LearningError):
            self.call('recommendation_decide', channel='chat_relayed', recommendation_id=recommendation['id'], status='accepted')
        decided = self.call('recommendation_decide', recommendation_id=recommendation['id'], status='accepted')['recommendation']
        self.assertEqual(decided['status'], 'accepted')
        self.assertEqual(self.store.dispatch('state', {})['sources'], [])
        with self.assertRaises(LearningError):
            self.call('recommendation', title='Unsafe', url='file:///secret', reason='x', prerequisites=[], verification='unverified')

    def test_quote_check_uses_conservative_whitespace_and_policy(self):
        source = self.call('source', title='Paper', excerpt='A quorum\n  needs votes.')['source']
        matched = self.store.dispatch('quote_check', {'source_id': source['id'], 'quote': 'quorum needs votes.'}, channel='chat_relayed')
        self.assertTrue(matched['verified'])
        self.assertFalse(matched['entailment_verified'])
        mismatched = self.store.dispatch('quote_check', {'source_id': source['id'], 'quote': 'Quorum needs votes.'})
        self.assertFalse(mismatched['verified'])
        private = self.call('source', title='Private', excerpt='Secret', sharing='metadata-only')['source']
        with self.assertRaises(LearningError):
            self.store.dispatch('quote_check', {'source_id': private['id'], 'quote': 'Secret'}, channel='chat_relayed')

    def test_activity_revision_preserves_old_keys_and_attempt_version(self):
        original = self.activity()
        run = self.call('run', activity_id=original['id'])
        first = self.call('submit', run_id=run['run_id'], answer='Two')['attempt']
        revised = self.call('activity_revision', activity_id=original['id'], title='Revised', kind='prediction', prompt='New prompt', criteria=['New criterion'], solution='NEW SECRET', hints=[], source_ids=[])['activity']
        self.assertNotEqual(revised['id'], original['id'])
        self.assertEqual(revised['version'], 2)
        self.assertEqual(first['activity_version'], 1)
        self.assertEqual(self.call('activity_read', activity_id=original['id'])['activity']['solution'], 'SECRET: majority')
        self.assertNotIn('solution', self.call('activity_read', activity_id=revised['id'])['activity'])
        with self.assertRaises(LearningError):
            self.call('activity_revision', activity_id=original['id'], title='Stale', kind='trace', prompt='p', criteria=['c'], solution='s', source_ids=[])

    def test_discovery_assumptions_and_questions_survive_resume(self):
        self.call('brief', revision=1, brief='Explore consensus', objectives=['Understand quorum'], assumptions=['Learner may know networking'], open_questions=['Desired depth?'])
        self.call('brief', revision=2, brief='Explore consensus slowly', objectives=['Understand quorum'])
        brief = self.store.dispatch('resume_brief', {'track_id': self.context['track_id']})
        self.assertEqual(brief['track']['assumptions'], ['Learner may know networking'])
        self.assertEqual(brief['track']['open_questions'], ['Desired depth?'])

    def test_model_cannot_archive_or_override_schedule(self):
        with self.assertRaises(LearningError):
            self.call('track_status', channel='chat_relayed', revision=1, status='archived')
        attempt = self.attempt()
        review = self.call('assess', attempt_id=attempt['id'], method='self', outcome='developing', feedback='Check')['review']
        with self.assertRaises(LearningError):
            self.call('review', channel='chat_relayed', review_id=review['id'], due_at='2026-01-01T00:00:00Z')
        # A learner can intentionally mark an item overdue.
        adjusted = self.call('review', review_id=review['id'], due_at='2026-01-01T00:00:00Z')['review']
        self.assertEqual(adjusted['due_at'], '2026-01-01T00:00:00Z')

    def test_new_run_does_not_erase_prior_solution_exposure(self):
        activity = self.activity()
        first_run = self.call('run', activity_id=activity['id'])
        self.call('help', run_id=first_run['run_id'], level='full-solution-shown')
        second_run = self.call('run', activity_id=activity['id'])
        attempt = self.call('submit', run_id=second_run['run_id'], answer='Known answer')['attempt']
        self.assertEqual(attempt['assistance'], 'full-solution-shown')
        self.assertTrue(attempt['prior_help_exposure'])
        self.assertEqual(len(attempt['assistance_events']), 1)

    def test_repeat_after_submission_does_not_claim_no_assistance(self):
        prior = self.attempt()
        repeat_run = self.call('run', activity_id=prior['activity_id'])
        repeat = self.call('submit', run_id=repeat_run['run_id'], answer='Again')['attempt']
        self.assertEqual(repeat['assistance'], 'unknown')
        self.assertEqual(repeat['prior_attempt_count'], 1)

    def test_attaching_recommendation_requires_accepted_same_track(self):
        rec = self.call('recommendation', title='Paper', url='https://example.com', reason='Useful', prerequisites=[])['recommendation']
        with self.assertRaises(LearningError):
            self.call('source', title='Paper', excerpt='Curated passage', recommendation_id=rec['id'])
        self.call('recommendation_decide', recommendation_id=rec['id'], status='accepted')
        source = self.call('source', title='Paper', excerpt='Curated passage', recommendation_id=rec['id'])['source']
        self.assertEqual(source['recommendation_id'], rec['id'])
        other = self.store.dispatch('start', {'title': 'Other'})
        with self.assertRaises(LearningError):
            self.store.dispatch('source', {'context_id': other['context_id'], 'title': 'Wrong track', 'recommendation_id': rec['id']})

    def test_bounds_and_unsafe_links(self):
        for url in ('javascript:alert(1)', 'file:///etc/passwd', 'https://user:secret@example.com'):
            with self.assertRaises(LearningError):
                self.call('source', title='Bad', kind='notes', url=url, excerpt='x')
        with self.assertRaises(LearningError):
            self.call('activity', title='Bad', kind='trace', prompt='p', criteria='c', solution='s', hints=[], source_ids=[], visual={'type': 'html', 'markup': '<script>x</script>'})
        with self.assertRaises(LearningError):
            self.store.dispatch('start', {'title': 'x' * 301})


if __name__ == '__main__':
    unittest.main()

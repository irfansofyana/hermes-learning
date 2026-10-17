"""Human-owned practice attempts, scoped feedback, and lesson teaching contracts."""
import concurrent.futures
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import runtime

TEACHING = {'outcome': 'Explain FIFO order', 'prerequisites': ['Lists'], 'misconception': 'Newest item leaves first'}
PRACTICE = {'kind': 'explanation', 'prompt': 'A then B enter. Which leaves first?', 'criteria': ['Names A', 'Explains insertion order'], 'hints': ['Consider arrival order'], 'explanation': 'A arrived first, so A leaves first.'}


class LessonPracticeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.store = runtime.Store(Path(temp.name) / 'practice.db')
        patcher = patch.object(runtime, 'store', return_value=self.store)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.start = self.call('course_start', request_id='start', title='Queues', intent='topic', level='beginner', materials=[])
        self.context = self.start['context_id']
        self.call('course_plan', job_id=self.start['job_id'], summary='Queues', assumptions=[], lessons=[{'key':'first', 'title':'FIFO', 'goal':'Explain order'}])
        self.lesson = self.call('course_lesson', job_id=self.start['job_id'], lesson_key='first', content='A queue removes items in arrival order.', source_ids=[], teaching=TEACHING, practice=PRACTICE)['lesson']

    def call(self, action, channel='ui_direct', **params):
        if action not in ('course_start', 'course_read', 'course_open', 'practice_feedback', 'state'):
            params.setdefault('context_id', getattr(self, 'context', None))
        return runtime.action(action, params, channel=channel)

    def read(self, channel='ui_direct'):
        return self.call('course_read', track_id=self.start['track_id'], channel=channel)

    def submit(self, **extra):
        params = dict(lesson_key='first', lesson_version=self.lesson['version'], request_id='answer-1', answer='A, because it arrived first.', hints_used=1, explanation_shown=False)
        params.update(extra)
        return self.call('practice_submit', **params)

    def feedback(self, submitted, **extra):
        params = dict(attempt_id=submitted['attempt']['id'], evaluation_token=submitted['evaluation']['evaluation_token'], outcome='correct', feedback='You explained arrival order correctly.')
        params.update(extra)
        return self.call('practice_feedback', channel='chat_relayed', **params)

    def revise(self, **extra):
        lesson = dict(lesson_key='first', content=self.lesson['content'], source_ids=[], teaching=TEACHING, practice={**PRACTICE, 'prompt':'B then C enter. Which leaves first?'})
        lesson.update(extra)
        proposal = self.call('course_propose', request_id='edit', base_revision=1, mode='revise', summary='Revise practice', lessons=[lesson])['proposal']
        self.call('course_apply', proposal_id=proposal['id'])
        return proposal

    def test_teaching_and_practice_survive_publication_proposal_and_version_change(self):
        self.assertEqual(self.lesson['teaching'], TEACHING)
        self.assertEqual(self.read()['lessons'][0]['practice'], PRACTICE)
        proposal = self.revise()
        updated = self.read()['lessons'][0]
        self.assertEqual(updated['practice'], proposal['lessons'][0]['practice'])
        self.assertEqual(updated['version'], 2)

    def test_submit_retry_feedback_history_and_reconnection_do_not_change_progress(self):
        before = self.read()['position']
        submitted = self.submit()
        self.assertEqual(self.submit(), submitted)
        evaluation = submitted['evaluation']
        self.assertEqual(evaluation['lesson']['practice'], PRACTICE)
        self.assertEqual(evaluation['answer'], 'A, because it arrived first.')
        self.call('practice_bind', attempt_id=submitted['attempt']['id'], session_id='evaluation-session', scope='gateway/profile')
        attempts = self.call('practice_read', lesson_key='first')['attempts']
        self.assertEqual(attempts[0]['session_id'], 'evaluation-session')
        self.assertNotIn('evaluation_token', json.dumps(attempts))
        self.assertNotIn('context_id', json.dumps(attempts))
        result = self.feedback(submitted)
        self.assertEqual(result['attempt']['status'], 'completed')
        self.assertEqual(self.feedback(submitted), result)
        self.assertEqual(self.read()['position'], before)
        self.assertEqual(self.call('state')['attempts'], [])
        self.assertEqual(self.call('practice_read', lesson_key='first')['attempts'][0]['outcome'], 'correct')

    def test_scope_capability_channel_and_busy_enforcement(self):
        submitted = self.submit()
        for params in ({'evaluation_token':'wrong'}, {'evaluation_token':'学'}, {'attempt_id':'missing'}):
            with self.assertRaises(runtime.LearningError):
                self.feedback(submitted, **params)
        with self.assertRaises(runtime.LearningError):
            self.call('practice_feedback', attempt_id=submitted['attempt']['id'], evaluation_token='wrong', outcome='correct', feedback='Fabricated')
        with self.assertRaises(runtime.LearningError) as caught:
            self.submit(request_id='second')
        self.assertEqual(caught.exception.code, 'practice_busy')
        with self.assertRaises(runtime.LearningError) as caught:
            self.submit(answer='B')
        self.assertEqual(caught.exception.code, 'idempotency_conflict')
        for action, params in [('practice_read', {'lesson_key':'first'}), ('practice_submit', {'lesson_key':'first'}), ('practice_bind', {'attempt_id':submitted['attempt']['id'], 'session_id':'x', 'scope':'x'}), ('practice_status', {'attempt_id':submitted['attempt']['id'], 'status':'stopped'}), ('course_model', {'selection':None})]:
            with self.subTest(action=action), self.assertRaises(runtime.LearningError):
                self.call(action, channel='chat_relayed', **params)
        other = self.call('course_start', request_id='other', title='Other', intent='topic', level='beginner', materials=[])
        with self.assertRaises(runtime.LearningError) as caught:
            self.call('practice_status', context_id=other['context_id'], attempt_id=submitted['attempt']['id'], status='stopped')
        self.assertEqual(caught.exception.code, 'context_mismatch')

    def test_lesson_edits_reject_late_feedback_and_hide_old_version_attempts(self):
        submitted = self.submit()
        self.revise()
        with self.assertRaises(runtime.LearningError):
            self.feedback(submitted)
        self.assertEqual(self.call('practice_read', lesson_key='first')['attempts'], [])
        with self.assertRaises(runtime.LearningError):
            self.submit(request_id='stale-version')
        next_attempt = self.submit(request_id='current-version', lesson_version=2)
        self.assertNotEqual(next_attempt['attempt']['id'], submitted['attempt']['id'])

    def test_stopped_attempt_cannot_receive_feedback_and_new_attempt_preserves_history(self):
        first = self.submit()
        stopped = self.call('practice_status', attempt_id=first['attempt']['id'], status='stopped', error='Learner stopped evaluation')
        self.assertEqual(stopped['attempt']['status'], 'stopped')
        with self.assertRaises(runtime.LearningError):
            self.feedback(first)
        second = self.submit(request_id='retry')
        self.feedback(second, outcome='partial')
        self.assertEqual([a['status'] for a in self.call('practice_read', lesson_key='first')['attempts']], ['stopped','completed'])

    def test_model_selection_persists_per_path_and_can_reset(self):
        selection = {'provider':'openai', 'model':'configured-model'}
        result = self.call('course_model', selection=selection)
        self.assertEqual(result['selection'], selection)
        self.assertEqual(result['course']['model'], selection)
        self.assertEqual(self.read()['model'], selection)
        other = self.call('course_start', request_id='other', title='Other', intent='topic', level='beginner', materials=[], model={'provider':'local','model':'local-model'})
        self.assertEqual(self.call('course_read', track_id=other['track_id'])['model']['provider'], 'local')
        self.call('course_model', selection=None)
        self.assertIsNone(self.read()['model'])

    def test_binding_applied_model_is_optional_and_independent_of_preference(self):
        preferred = {'provider':'openai', 'model':'preferred'}
        applied = {'provider':'local', 'model':'active-session'}
        self.call('course_model', selection=preferred)
        binding = self.call('course_bind', session_id='session', scope='profile', model=applied)
        self.assertEqual(binding['model'], applied)
        self.assertEqual(self.read()['binding']['model'], applied)
        self.assertEqual(self.read()['model'], preferred)
        self.assertIsNone(self.read(channel='chat_relayed')['binding'])
        self.call('course_bind', session_id='default', scope='profile', model=None)
        self.assertIsNone(self.read()['binding']['model'])
        self.call('course_bind', session_id='legacy', scope='profile')
        self.assertNotIn('model', self.read()['binding'])
        self.assertEqual(self.read()['model'], preferred)

    def test_validation_rejects_bad_structured_content_and_help_exposure(self):
        for extra in ({'hints_used':True}, {'hints_used':2}, {'explanation_shown':'yes'}, {'answer':' '}, {'answer':'x'*30001}, {'lesson_version':True}):
            with self.subTest(extra=extra), self.assertRaises(runtime.LearningError):
                self.submit(**extra)
        for field, value in [('teaching', {'outcome':'x'}), ('practice', {**PRACTICE, 'kind':'quiz'}), ('practice', {**PRACTICE, 'criteria':[]})]:
            with self.subTest(field=field), self.assertRaises(runtime.LearningError):
                self.revise(**{field:value})
        self.assertEqual(self.call('practice_read', lesson_key='first')['attempts'], [])

    def test_regenerated_same_key_rejects_stale_submission_and_old_feedback(self):
        submitted = self.submit()
        proposal = self.call('course_propose', request_id='regenerate', base_revision=1, mode='regenerate', summary='Fresh course', outline=[{'key':'first','title':'New FIFO','goal':'Explain order'}], lessons=[{'lesson_key':'first','content':'Fresh example','source_ids':[], 'teaching':TEACHING,'practice':PRACTICE}])['proposal']
        self.call('course_apply', proposal_id=proposal['id'])
        self.assertEqual(self.read()['lessons'][0]['version'], 2)
        with self.assertRaises(runtime.LearningError):
            self.submit(request_id='old-screen')
        self.assertEqual(self.call('practice_read', lesson_key='first')['attempts'], [])
        with self.assertRaises(runtime.LearningError):
            self.feedback(submitted)
        self.submit(request_id='new-generation', lesson_version=2)

    def test_removed_then_reintroduced_lesson_key_does_not_reuse_version(self):
        proposal = self.call('course_propose', request_id='remove', base_revision=1, mode='revise', summary='Replace roadmap', outline=[{'key':'other','title':'Other','goal':'Other goal'}], lessons=[{'lesson_key':'other','content':'Other lesson','source_ids':[]}])['proposal']
        self.call('course_apply', proposal_id=proposal['id'])
        proposal = self.call('course_propose', request_id='restore', base_revision=2, mode='extend', summary='Add FIFO back', outline=[{'key':'other','title':'Other','goal':'Other goal'},{'key':'first','title':'FIFO','goal':'Explain order'}], lessons=[{'lesson_key':'first','content':'New example','source_ids':[],'practice':PRACTICE}])['proposal']
        self.call('course_apply', proposal_id=proposal['id'])
        restored = next(item for item in self.read()['lessons'] if item['key'] == 'first')
        self.assertEqual(restored['version'], 2)
        with self.assertRaises(runtime.LearningError):
            self.submit(request_id='stale-browser')

    def test_concurrent_submission_retries_create_one_attempt_and_bind_is_immutable(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.submit(), range(2)))
        self.assertEqual(results[0], results[1])
        attempt_id = results[0]['attempt']['id']
        self.call('practice_bind', attempt_id=attempt_id, session_id='one', scope='profile')
        with self.assertRaises(runtime.LearningError):
            self.call('practice_bind', attempt_id=attempt_id, session_id='two', scope='profile')
        self.assertEqual(len(self.call('practice_read', lesson_key='first')['attempts']), 1)
        self.feedback(results[0])
        terminal = self.submit()
        self.assertIsNone(terminal['evaluation'])
        self.assertEqual(terminal['attempt']['status'], 'completed')
        self.call('practice_status', attempt_id=attempt_id, status='failed', error='Late disconnect')
        self.assertEqual(self.call('practice_read', lesson_key='first')['attempts'][0]['status'], 'completed')

    def test_pending_attempt_in_another_path_does_not_block_new_path(self):
        self.submit()
        other = self.call('course_start', request_id='other-path', title='Other', intent='topic', level='beginner', materials=[])
        self.call('course_plan', context_id=other['context_id'], job_id=other['job_id'], summary='Other', assumptions=[], lessons=[{'key':'first','title':'First','goal':'Explain'}])
        self.call('course_lesson', context_id=other['context_id'], job_id=other['job_id'], lesson_key='first', content='Other lesson.', source_ids=[], practice=PRACTICE)
        submitted = self.submit(context_id=other['context_id'])
        self.assertEqual(submitted['attempt']['status'], 'pending')
        # The capability, rather than a UI transport label, authorizes feedback.
        result = self.call('practice_feedback', attempt_id=submitted['attempt']['id'], evaluation_token=submitted['evaluation']['evaluation_token'], outcome='correct', feedback='Correct order.')
        self.assertEqual(result['attempt']['status'], 'completed')

    def test_old_lesson_without_practice_stays_readable_and_cannot_submit(self):
        self.revise(practice=None)
        self.assertEqual(self.read()['lessons'][0]['content'], self.lesson['content'])
        with self.assertRaises(runtime.LearningError) as caught:
            self.submit(lesson_version=2)
        self.assertEqual(caught.exception.code, 'practice_unavailable')
        self.assertEqual(self.call('practice_read', lesson_key='first')['attempts'], [])

    def test_publication_retry_cannot_change_teaching_or_practice(self):
        for details in ({}, {'teaching':{**TEACHING, 'outcome':'Different outcome'},'practice':PRACTICE}, {'teaching':TEACHING,'practice':{**PRACTICE,'explanation':'Different explanation'}}):
            with self.subTest(details=details), self.assertRaises(runtime.LearningError) as caught:
                self.call('course_lesson', job_id=self.start['job_id'], lesson_key='first', content=self.lesson['content'], source_ids=[], **details)
            self.assertEqual(caught.exception.code, 'revision_conflict')
        self.assertEqual(self.read()['lessons'][0], self.lesson)

    def test_revoked_context_blocks_feedback_and_does_not_block_new_explicit_submission(self):
        submitted = self.submit()
        self.call('leave')
        with self.assertRaises(runtime.LearningError):
            self.feedback(submitted)
        self.context = self.call('course_open', track_id=self.start['track_id'])['context_id']
        self.submit(request_id='reopened')
        self.assertEqual([a['status'] for a in self.call('practice_read', lesson_key='first')['attempts']], ['stopped','pending'])

    def test_private_derived_content_cannot_be_sent_for_evaluation(self):
        source = self.call('source', title='Private', kind='text', excerpt='SECRET', sharing='metadata-only')['source']
        self.revise(content='SECRET', source_ids=[source['id']], teaching={**TEACHING,'outcome':'SECRET outcome'}, practice={**PRACTICE,'prompt':'SECRET prompt'})
        self.assertNotIn('SECRET', json.dumps(self.read(channel='chat_relayed')))
        with self.assertRaises(runtime.LearningError) as caught:
            self.submit(lesson_version=2)
        self.assertEqual(caught.exception.code, 'source_restricted')


if __name__ == '__main__':
    unittest.main()

"""Conversational proposal contracts against the real transactional service."""
import concurrent.futures
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import runtime


class CourseUpdateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.store = runtime.Store(Path(temp.name) / 'updates.db')
        patcher = patch.object(runtime, 'store', return_value=self.store)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.start = self.call('course_start', request_id='start', title='Queues', intent='topic', level='beginner', materials=[])
        self.context = self.start['context_id']
        self.outline = [{'key':'first','title':'Basics','goal':'FIFO'}, {'key':'second','title':'Workers','goal':'Concurrency'}]
        self.call('course_plan', job_id=self.start['job_id'], summary='Queues', assumptions=[], lessons=self.outline)
        self.initial = self.call('course_lesson', job_id=self.start['job_id'], lesson_key='first', content='Original explanation and example.', source_ids=[])['lesson']

    def call(self, action, channel='ui_direct', **params):
        if action not in ('course_start', 'course_read', 'course_open'):
            params.setdefault('context_id', getattr(self, 'context', None))
        return runtime.action(action, params, channel=channel)

    def read(self, channel='ui_direct'):
        return self.call('course_read', track_id=self.start['track_id'], channel=channel)

    def propose(self, request_id='edit', **params):
        return self.call('course_propose', channel='chat_relayed', request_id=request_id,
                         base_revision=params.pop('base_revision', 1), mode=params.pop('mode', 'revise'),
                         summary=params.pop('summary', 'Clarify the example'),
                         **({'lessons':[{'lesson_key':'first','content':'Rewritten explanation with code example.','source_ids':[]}]} if not params else params))['proposal']

    def test_revise_is_pending_until_human_atomic_apply_and_retries_are_stable(self):
        self.call('course_bind', session_id='tutor', scope='scope')
        self.call('course_position', lesson_key='first', completed=['first'])
        self.assertEqual(self.read()['revision'], 1)
        proposal = self.propose()
        self.assertEqual(self.read()['lessons'][0], self.initial)
        self.assertEqual(self.read()['proposals'][0]['id'], proposal['id'])
        self.assertEqual(proposal['status'], 'pending')
        self.assertNotIn('context_id', json.dumps(self.read(channel='chat_relayed')['proposals']))
        with self.assertRaises(runtime.LearningError):
            self.call('course_apply', channel='chat_relayed', proposal_id=proposal['id'])
        result = self.call('course_apply', proposal_id=proposal['id'])
        self.assertEqual(result['proposal']['status'], 'applied')
        current = self.read()
        self.assertEqual(current['revision'], 2)
        self.assertEqual(current['lessons'][0]['version'], 2)
        self.assertEqual(current['lessons'][0]['content'], proposal['lessons'][0]['content'])
        self.assertEqual(current['position'], {'lesson_key':'first','completed':[]})
        self.assertEqual(current['binding'], {'session_id':'tutor','scope':'scope'})
        self.assertEqual(self.call('course_apply', proposal_id=proposal['id']), result)
        self.assertEqual(self.propose()['id'], proposal['id'])
        with self.assertRaises(runtime.LearningError) as caught:
            self.propose(summary='Different request')
        self.assertEqual(caught.exception.code, 'idempotency_conflict')
        with self.assertRaises(runtime.LearningError) as caught:
            self.call('course_lesson', job_id=self.start['job_id'], lesson_key='first', content=self.initial['content'], source_ids=[])
        self.assertEqual(caught.exception.status, 409)
        self.assertEqual(self.read()['lessons'], current['lessons'])

    def test_extend_preserves_records_and_progress_and_revise_removes_only_removed(self):
        self.call('course_position', lesson_key='first', completed=['first'])
        new = {'key':'third','title':'Durability','goal':'Persist jobs'}
        proposal = self.propose(mode='extend', outline=self.outline + [new], lessons=[{'lesson_key':'third','content':'Persist jobs, for example write to disk.','source_ids':[]}])
        self.call('course_apply', proposal_id=proposal['id'])
        current = self.read()
        self.assertEqual(current['lessons'][0], self.initial)
        self.assertEqual(current['position']['completed'], ['first'])
        third = current['lessons'][1]
        proposal = self.propose('remove', base_revision=2, outline=[new], lessons=[])
        self.call('course_apply', proposal_id=proposal['id'])
        self.assertEqual(self.read()['lessons'], [third])
        self.assertEqual(self.read()['position'], {'lesson_key':'third','completed':[]})

    def test_regenerate_discards_old_records_and_progress_even_when_keys_match(self):
        self.call('course_position', lesson_key='first', completed=['first'])
        proposal = self.propose(mode='regenerate', outline=[self.outline[0]], lessons=[{'lesson_key':'first','content':'A fresh full course opening and worked example.','source_ids':[]}])
        self.call('course_apply', proposal_id=proposal['id'])
        current = self.read()
        self.assertEqual(len(current['lessons']), 1)
        self.assertNotEqual(current['lessons'][0]['id'], self.initial['id'])
        self.assertEqual(current['position'], {'lesson_key':'first','completed':[]})

    def test_stale_dismissal_and_concurrent_acceptance(self):
        a = self.propose('a')
        b = self.propose('b', summary='Another edit')
        with concurrent.futures.ThreadPoolExecutor() as pool:
            results = list(pool.map(lambda _: self.call('course_apply', proposal_id=a['id']), range(2)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(self.read()['revision'], 2)
        self.assertEqual(self.read()['proposals'][1]['status'], 'stale')
        with self.assertRaises(runtime.LearningError) as caught:
            self.call('course_apply', proposal_id=b['id'])
        self.assertEqual(caught.exception.code, 'revision_conflict')
        c = self.propose('c', base_revision=2, lessons=[{'lesson_key':'first','content':'A further distinct lesson explanation.','source_ids':[]}])
        self.assertEqual(self.call('course_dismiss', proposal_id=c['id'])['proposal']['status'], 'dismissed')
        self.assertEqual(self.call('course_dismiss', proposal_id=c['id'])['proposal']['status'], 'dismissed')
        with self.assertRaises(runtime.LearningError):
            self.call('course_apply', proposal_id=c['id'])

    def test_rejects_noop_invalid_modes_duplicates_and_incomplete_regeneration(self):
        bad = [
            {'outline':self.outline,'lessons':[]},
            {'lessons':[{'lesson_key':'first','content':self.initial['content'],'source_ids':[]}]},
            {'mode':'extend','outline':list(reversed(self.outline)),'lessons':[]},
            {'mode':'extend','outline':self.outline + [{'key':'third','title':'Third','goal':'Goal'}], 'lessons':[{'lesson_key':'first','content':'Replace','source_ids':[]}]},
            {'mode':'regenerate','outline':[self.outline[0]],'lessons':[]},
            {'outline':[self.outline[0],self.outline[0]],'lessons':[]},
            {'lessons':[{'lesson_key':'missing','content':'x','source_ids':[]}]},
            {'lessons':[{'lesson_key':'first','content':'\ue200cite bad','source_ids':[]}]},
        ]
        for index, params in enumerate(bad):
            with self.subTest(params=params), self.assertRaises(runtime.LearningError):
                self.propose(str(index), **params)
        self.assertEqual(self.read()['proposals'], [])

    def test_generation_busy_blocks_propose_and_apply_then_failed_job_allows_edit(self):
        proposal = self.propose()
        job = self.call('course_generate', request_id='second', lesson_key='second')
        for action, params in [('course_apply', {'proposal_id':proposal['id']}), ('course_propose', {'request_id':'busy','base_revision':1,'mode':'revise','summary':'Busy','lessons':[{'lesson_key':'first','content':'Changed','source_ids':[]}]})]:
            with self.assertRaises(runtime.LearningError) as caught:
                self.call(action, **params)
            self.assertEqual(caught.exception.code, 'generation_busy')
        self.call('course_job_status', job_id=job['job_id'], status='failed', error='Unavailable')
        self.call('course_apply', proposal_id=proposal['id'])
        self.assertEqual(self.read()['revision'], 2)

    def test_source_boundaries_visuals_capacity_and_context_revocation(self):
        restricted = self.call('source', title='Private', kind='notes', sharing='metadata-only', excerpt='PRIVATE')['source']
        unread = self.call('source', title='Link', kind='url', sharing='selected-excerpts', url='https://example.com')['source']
        for source in [restricted, unread]:
            with self.assertRaises(runtime.LearningError):
                self.propose(source['id'], lessons=[{'lesson_key':'first','content':'Changed','source_ids':[source['id']]}])
        visual = {'type':'code-trace','code':'x = 1','language':'python','steps':[{'line':1,'label':'Assign'}]}
        proposal = self.propose('visual', lessons=[{'lesson_key':'first','content':'```python\nx = 1\n```','source_ids':[],'visual':visual}])
        self.assertEqual(proposal['lessons'][0]['visual']['visible_steps'], 1)
        for i in range(4):
            self.propose(f'cap-{i}')
        with self.assertRaises(runtime.LearningError) as caught:
            self.propose('too-many')
        self.assertEqual(caught.exception.status, 409)
        self.call('leave')
        for action, params in [('course_apply', {'proposal_id':proposal['id']}), ('course_dismiss', {'proposal_id':proposal['id']})]:
            with self.assertRaises(runtime.LearningError) as caught:
                self.call(action, **params)
            self.assertEqual(caught.exception.code, 'context_revoked')

    def test_outline_title_rename_updates_retained_lesson_without_resetting_reading(self):
        self.call('course_position', lesson_key='first', completed=['first'])
        outline = copy.deepcopy(self.outline)
        outline[0].update(title='FIFO fundamentals', goal='Explain FIFO using a queue')
        proposal = self.propose(outline=outline, lessons=[])
        self.call('course_apply', proposal_id=proposal['id'])
        current = self.read()
        self.assertEqual(current['lessons'][0], {**self.initial, 'title':'FIFO fundamentals'})
        self.assertEqual(current['position'], {'lesson_key':'first', 'completed':['first']})
        self.assertEqual(current['outline'][0]['goal'], 'Explain FIFO using a queue')

    def test_regenerate_can_remove_later_published_lessons_without_rewriting_first(self):
        job = self.call('course_generate', request_id='publish-second', lesson_key='second')
        self.call('course_lesson', job_id=job['job_id'], lesson_key='second', content='A worker example.', source_ids=[])
        proposal = self.propose(mode='regenerate', outline=self.outline, lessons=[{'lesson_key':'first','content':self.initial['content'],'source_ids':[]}])
        self.call('course_apply', proposal_id=proposal['id'])
        self.assertEqual([lesson['key'] for lesson in self.read()['lessons']], ['first'])

    def test_scope_revision_and_nested_content_validation_leave_course_untouched(self):
        proposal = self.propose()
        before = self.read()
        other = self.call('course_start', request_id='other', title='Other', intent='topic', level='beginner', materials=[])
        for action in ('course_apply', 'course_dismiss'):
            with self.assertRaises(runtime.LearningError) as caught:
                self.call(action, context_id=other['context_id'], proposal_id=proposal['id'])
            self.assertEqual(caught.exception.code, 'context_mismatch')
        foreign = self.call('source', context_id=other['context_id'], title='Foreign', kind='notes', sharing='selected-excerpts', excerpt='Foreign source')['source']
        for params in [
            {'base_revision':True}, {'base_revision':0}, {'base_revision':2},
            {'lessons':[{'lesson_key':'first','content':'X','source_ids':[foreign['id']]}]},
            {'lessons':[{'lesson_key':'first','content':'X','source_ids':[],'visual':{'type':'code-trace','code':'x','steps':[{'line':2,'label':'Invalid'}]}}]},
        ]:
            with self.subTest(params=params), self.assertRaises(runtime.LearningError):
                self.propose('invalid', **params)
        self.assertEqual(self.read(), before)
        with self.assertRaises(runtime.LearningError):
            self.call('course_dismiss', channel='chat_relayed', proposal_id=proposal['id'])

    def test_restricted_proposal_projection_never_exposes_summary_outline_or_content(self):
        source = self.call('source', title='Private', kind='notes', sharing='metadata-only', excerpt='SECRET')['source']
        proposal = self.call('course_propose', request_id='human-private', base_revision=1, mode='revise', summary='SECRET summary', outline=[{'key':'first','title':'SECRET title','goal':'SECRET goal'}], lessons=[{'lesson_key':'first','content':'SECRET content','source_ids':[source['id']]}])['proposal']
        projected = self.read(channel='chat_relayed')['proposals'][0]
        self.assertNotIn('SECRET', json.dumps(projected))
        self.assertNotIn(self.context, json.dumps(projected))
        self.assertEqual(self.read()['proposals'][0]['id'], proposal['id'])


if __name__ == '__main__':
    unittest.main()

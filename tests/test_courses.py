import concurrent.futures
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import runtime


class CourseTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.store = runtime.Store(Path(temp.name) / 'courses.db')
        self.addCleanup(patch.stopall)
        patch.object(runtime, 'store', return_value=self.store).start()

    def call(self, action, channel='ui_direct', **params):
        return runtime.action(action, params, channel=channel)

    def start(self, request_id='start-1', **extra):
        return self.call('course_start', request_id=request_id, title='Learn queues', intent='project', level='beginner', materials=extra.pop('materials', []), **extra)

    def plan(self, start, **extra):
        return self.call('course_plan', channel='chat_relayed', context_id=start['context_id'], job_id=start['job_id'], summary='Build a queue', assumptions=['Local program'], lessons=extra.pop('lessons', [{'key':'first', 'title':'Queue basics', 'goal':'Build FIFO'}, {'key':'second', 'title':'Concurrency', 'goal':'Use workers'}]), **extra)

    def lesson(self, start, **extra):
        return self.call('course_lesson', channel=extra.pop('channel', 'chat_relayed'), context_id=start['context_id'], job_id=start['job_id'], lesson_key=extra.pop('lesson_key', 'first'), content=extra.pop('content', 'A queue stores work in order.\n\nFor example, push A then B; pop returns A.\n\nTry adding C.'), source_ids=extra.pop('source_ids', []), **extra)

    def read(self, start, channel='ui_direct'):
        return self.call('course_read', track_id=start['track_id'], channel=channel)

    def visuals(self):
        return [
            {'type': 'sequence', 'participants': [{'id': 'client', 'label': 'Client'}, {'id': 'queue', 'label': 'Queue'}],
             'steps': [{'from': 'client', 'to': 'queue', 'label': 'Push A'}, {'from': 'queue', 'to': 'client', 'label': 'Return A'}]},
            {'type': 'state-machine', 'states': [{'id': 'idle', 'label': 'Idle'}, {'id': 'ready', 'label': 'Ready'}], 'initial': 'idle',
             'steps': [{'from': 'idle', 'to': 'ready', 'label': 'Push'}, {'from': 'ready', 'to': 'idle', 'label': 'Pop'}]},
            {'type': 'code-trace', 'code': 'x = 1\nx += 1', 'language': 'python',
             'steps': [{'line': 1, 'label': 'Initialize', 'variables': [{'name': 'x', 'value': '1'}]},
                       {'line': 2, 'label': 'Increment', 'variables': [{'name': 'x', 'value': '2'}]}]},
        ]

    def test_lesson_visuals_publish_all_steps_and_retry_after_normalization(self):
        for visual in self.visuals():
            for visibility in (None, 0, 1, 2):
                with self.subTest(kind=visual['type'], visible_steps=visibility):
                    start = self.start(f"{visual['type']}-{visibility}")
                    self.plan(start)
                    supplied = copy.deepcopy(visual)
                    if visibility is not None:
                        supplied['visible_steps'] = visibility
                    saved = self.lesson(start, visual=supplied)
                    self.assertEqual(saved['lesson']['visual']['visible_steps'], 2)
                    self.assertEqual(len(saved['lesson']['visual']['steps']), 2)
                    self.assertEqual(self.lesson(start, visual=supplied), saved)
                    self.assertEqual(self.lesson(start, visual={**supplied, 'visible_steps': 2}), saved)
                    changed = copy.deepcopy(supplied)
                    changed['steps'][1]['label'] = 'Different explanation'
                    with self.assertRaises(runtime.LearningError):
                        self.lesson(start, visual=changed)
                    for channel in ('ui_direct', 'chat_relayed'):
                        self.assertEqual(self.read(start, channel)['lessons'], [saved['lesson']])

    def test_legacy_lesson_visuals_read_fully_without_rewriting_and_retry_identically(self):
        for visual in self.visuals():
            with self.subTest(kind=visual['type']):
                start = self.start(visual['type'])
                self.plan(start)
                lesson = self.lesson(start, visual=visual)['lesson']
                lesson['visual']['visible_steps'] = 1
                publication = {key: lesson[key] for key in ('key', 'title', 'content', 'source_ids', 'visual')}
                with self.store._connection() as db:
                    self.store._put(db, 'lesson', lesson, True)
                    job = self.store._get(db, 'course_job', start['job_id'])
                    job['lesson_hash'] = hashlib.sha256(json.dumps(publication, sort_keys=True).encode()).hexdigest()
                    self.store._put(db, 'course_job', job, True)
                    before = db.execute('SELECT id, data FROM records ORDER BY seq').fetchall()
                for channel in ('ui_direct', 'chat_relayed'):
                    projected = self.read(start, channel)['lessons'][0]
                    self.assertEqual(projected['visual']['visible_steps'], 2)
                    self.assertEqual(projected['visual']['steps'], lesson['visual']['steps'])
                self.assertEqual(self.lesson(start, visual=visual)['lesson'], projected)
                with self.assertRaises(runtime.LearningError):
                    self.lesson(start, visual=visual, content='Changed legacy lesson')
                changed = copy.deepcopy(visual)
                changed['steps'][1]['label'] = 'Changed legacy step'
                with self.assertRaises(runtime.LearningError):
                    self.lesson(start, visual=changed)
                with self.store._connection() as db:
                    self.assertEqual(db.execute('SELECT id, data FROM records ORDER BY seq').fetchall(), before)

    def test_lesson_visual_validation_preserves_bounds_and_reference_checks(self):
        for visual in self.visuals():
            with self.subTest(kind=visual['type']):
                start = self.start(visual['type'])
                self.plan(start)
                invalid = [
                    {**visual, 'visible_steps': value} for value in (-1, 3, True)
                ] + [{**visual, 'steps': []}, {**visual, 'steps': visual['steps'] * 16},
                     {**visual, 'schema_version': 2}, {**visual, 'markup': '<svg />'}]
                bad_reference = copy.deepcopy(visual)
                bad_reference['steps'][0].update({'line': 3} if visual['type'] == 'code-trace' else {'to': 'missing'})
                invalid.append(bad_reference)
                if visual['type'] == 'state-machine':
                    invalid.append({**visual, 'initial': 'missing'})
                    discontinuous = copy.deepcopy(visual)
                    discontinuous['steps'][1]['from'] = 'idle'
                    invalid.append(discontinuous)
                for payload in invalid:
                    with self.subTest(payload=payload), self.assertRaises(runtime.LearningError):
                        self.lesson(start, visual=payload)
                self.assertEqual(self.read(start)['lessons'], [])
                self.assertEqual(self.read(start)['jobs'][0]['status'], 'generating')
                self.assertEqual(self.lesson(start, visual=visual)['lesson']['visual']['visible_steps'], 2)

    def test_lesson_visibility_does_not_unlock_practice_or_restricted_sources(self):
        for visual in self.visuals():
            with self.subTest(kind=visual['type']):
                start = self.start(visual['type'], materials=[{'title': 'Private', 'kind': 'notes', 'sharing': 'metadata-only', 'excerpt': 'PRIVATE EXAMPLE'}])
                self.plan(start)
                source_id = self.read(start)['sources'][0]['id']
                lesson = self.lesson(start, channel='ui_direct', visual=visual, source_ids=[source_id])['lesson']
                self.assertEqual(lesson['visual']['visible_steps'], 2)
                restricted = self.read(start, 'chat_relayed')['lessons'][0]
                self.assertTrue(restricted['content_withheld'])
                self.assertIsNone(restricted['visual'])
                activity = self.call('activity', context_id=start['context_id'], title='Predict', kind='prediction', prompt='What happens next?', criteria=['Explain the next step'], solution='PRIVATE SOLUTION', visual=visual)['activity']
                for channel in ('ui_direct', 'chat_relayed'):
                    gated = self.call('activity_read', channel=channel, activity_id=activity['id'])['activity']
                    self.assertEqual(gated['visual']['visible_steps'], 1)
                    self.assertEqual(len(gated['visual']['steps']), 1)
                    self.assertNotIn('solution', gated)
                run = self.call('run', context_id=start['context_id'], activity_id=activity['id'])
                self.call('submit', context_id=start['context_id'], run_id=run['run_id'], answer='My prediction')
                unlocked = self.call('activity_read', context_id=start['context_id'], activity_id=activity['id'])['activity']
                self.assertEqual(unlocked['visual']['visible_steps'], 2)
                self.assertEqual(len(unlocked['visual']['steps']), 2)

    def test_start_is_atomic_and_concurrent_retry_is_idempotent(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.start(), range(4)))
        self.assertTrue(all(result == results[0] for result in results))
        self.assertEqual(len(self.call('state')['tracks']), 1)
        with self.assertRaises(runtime.LearningError):
            self.call('course_start', request_id='start-1', title='Other', intent='topic', level='beginner', materials=[])
        with self.assertRaises(runtime.LearningError):
            self.start('bad', materials=[{'title':'Good', 'kind':'notes', 'sharing':'selected-excerpts', 'excerpt':'hello'}, {'title':'Bad', 'kind':'url', 'sharing':'selected-excerpts', 'url':'file:///secret'}])
        self.assertEqual(len(self.call('state')['tracks']), 1)
        self.assertEqual(self.call('state')['sources'], [])

    def test_initial_job_publishes_outline_and_only_first_lesson_idempotently(self):
        start = self.start()
        plan = self.plan(start)
        self.assertEqual(self.plan(start), plan)
        with self.assertRaises(runtime.LearningError):
            self.plan(start, lessons=[{'key':'different', 'title':'Changed', 'goal':'Changed'}])
        with self.assertRaises(runtime.LearningError):
            self.lesson(start, lesson_key='second')
        lesson = self.lesson(start)
        self.assertEqual(self.lesson(start), lesson)
        with self.assertRaises(runtime.LearningError):
            self.lesson(start, content='Overwrite lesson')
        view = self.read(start)
        self.assertEqual(view['jobs'][0]['status'], 'completed')
        self.assertEqual(view['lessons'][0]['key'], 'first')
        self.assertEqual(view['position'], {'lesson_key':'first', 'completed':[]})
        self.assertNotIn(start['context_id'], json.dumps(view))

    def test_opaque_citations_are_rejected_without_closing_job_and_markdown_retry_saves(self):
        start = self.start()
        self.plan(start)
        for marker in ['\ue200cite\ue202turn1view0\ue201', '\ue200cite\ue202turn0search2']:
            with self.subTest(marker=marker), self.assertRaisesRegex(runtime.LearningError, 'Markdown.*URL'):
                self.lesson(start, content='Kafka retains events. ' + marker)
        self.assertEqual(self.read(start)['lessons'], [])
        self.assertEqual(self.read(start)['jobs'][0]['status'], 'generating')
        content = 'Kafka retains events. [Apache Kafka introduction](https://kafka.apache.org/intro/)'
        saved = self.lesson(start, content=content)
        self.assertEqual(saved['lesson']['content'], content)
        self.assertEqual(self.read(start)['jobs'][0]['status'], 'completed')

    def test_chat_cannot_authorize_or_bind_and_other_contexts_cannot_publish(self):
        start = self.start()
        for action, params in [('course_start', {'request_id':'x','title':'X','intent':'topic','level':'beginner','materials':[]}), ('course_open', {'track_id':start['track_id']}), ('course_generate', {'context_id':start['context_id'],'request_id':'x'}), ('course_bind', {'context_id':start['context_id'],'session_id':'s','scope':'backend/profile/store'}), ('course_position', {'context_id':start['context_id'],'lesson_key':'first'}), ('course_job_status', {'context_id':start['context_id'],'job_id':start['job_id'],'status':'failed'})]:
            with self.subTest(action=action), self.assertRaises(runtime.LearningError):
                self.store.dispatch(action, params, channel='chat_relayed')
        other = self.start('other')
        for context in (other['context_id'], self.call('resume', track_id=start['track_id'])['context_id']):
            with self.assertRaises(runtime.LearningError):
                self.plan({**start, 'context_id':context})
        self.call('leave', context_id=start['context_id'])
        with self.assertRaises(runtime.LearningError):
            self.plan(start)
        with self.assertRaises(runtime.LearningError):
            self.start()

    def test_sources_are_bounded_truthful_and_respect_disclosure(self):
        materials = [{'title':'Private', 'kind':'notes', 'sharing':'metadata-only', 'excerpt':'PRIVATE SECRET'}, {'title':'Public', 'kind':'notes', 'sharing':'selected-excerpts', 'excerpt':'FIFO'}, {'title':'Link', 'kind':'url', 'sharing':'selected-excerpts', 'url':'https://example.org'}]
        start = self.start(materials=materials)
        view = self.read(start)
        self.assertEqual([s['read_status'] for s in view['sources']], ['provided','provided','unread'])
        self.assertNotIn('PRIVATE SECRET', json.dumps(self.read(start, 'chat_relayed')))
        self.plan(start)
        for source in (view['sources'][0], view['sources'][2]):
            with self.assertRaises(runtime.LearningError):
                self.lesson(start, source_ids=[source['id']])
        other = self.start('other', materials=[materials[1]])
        with self.assertRaises(runtime.LearningError):
            self.lesson(start, source_ids=[self.read(other)['sources'][0]['id']])
        self.lesson(start, source_ids=[view['sources'][1]['id']])
        self.assertIn('FIFO', json.dumps(self.read(start, 'chat_relayed')))
        with self.assertRaises(runtime.LearningError):
            self.start('huge', materials=[{**materials[1], 'excerpt':'x' * 50001}])

    def test_stopped_jobs_require_new_authorization_and_binding_is_private(self):
        start = self.start()
        self.plan(start)
        self.call('course_job_status', context_id=start['context_id'], job_id=start['job_id'], status='stopped')
        with self.assertRaises(runtime.LearningError):
            self.lesson(start)
        context = self.call('course_open', track_id=start['track_id'])['context_id']
        generated = self.call('course_generate', context_id=context, request_id='retry', lesson_key='first')
        self.assertEqual(self.call('course_generate', context_id=context, request_id='retry', lesson_key='first'), generated)
        self.lesson({**start, **generated, 'context_id':context})
        self.call('course_bind', context_id=context, session_id='durable-session', scope='backend/profile/store')
        self.assertEqual(self.read(start)['binding']['session_id'], 'durable-session')
        self.assertIsNone(self.read(start, 'chat_relayed')['binding'])
        self.call('course_position', context_id=context, lesson_key='first', completed=['first'])
        self.assertEqual(self.read(start)['position']['completed'], ['first'])
        self.assertEqual(self.call('state')['attempts'], [])
        with self.assertRaises(runtime.LearningError):
            self.call('course_position', context_id=context, lesson_key='second', completed=['second'])

    def test_invalid_publication_is_rejected_without_partial_records(self):
        start = self.start()
        for lessons in ([], [{'key':'first','title':'One','goal':'Goal'}, {'key':'first','title':'Two','goal':'Goal'}], [{'key':'bad key','title':'One','goal':'Goal'}]):
            with self.assertRaises(runtime.LearningError):
                self.plan(start, lessons=lessons)
        self.assertEqual(self.read(start)['outline'], [])
        self.plan(start)
        for extra in ({'content':' '}, {'visual':{'type':'sequence','participants':[{'id':'x','label':'X'}],'steps':[{'from':'x','to':'missing','label':'Bad'}]}}, {'source_ids':['missing']}):
            with self.assertRaises(runtime.LearningError):
                self.lesson(start, **extra)
        self.assertEqual(self.read(start)['lessons'], [])
        with self.assertRaises(runtime.LearningError):
            self.call('course_job_status', context_id=start['context_id'], job_id=start['job_id'], status='completed')

    def test_generation_preserves_full_interest_and_bounds_aggregate_sources(self):
        interest = 'A detailed project request. ' * 100
        start = self.start(interest=interest)
        self.assertEqual(self.read(start)['track']['interest'], interest)
        material = {'title':'Notes','kind':'text','sharing':'selected-excerpts','excerpt':'x' * 40000}
        with self.assertRaises(runtime.LearningError):
            self.start('too-many-chars', materials=[material] * 3)
        material['excerpt'] = '学' * 40000
        with self.assertRaises(runtime.LearningError):
            self.start('too-many-bytes', materials=[material] * 2)
        self.assertEqual(len(self.call('state')['tracks']), 1)

    def test_new_request_supersedes_old_publication_and_next_lesson_is_bounded(self):
        start = self.start()
        replacement = self.call('course_generate', context_id=start['context_id'], request_id='replacement')
        with self.assertRaises(runtime.LearningError):
            self.plan(start)
        current = {**start, **replacement}
        self.plan(current)
        self.lesson(current)
        next_job = self.call('course_generate', context_id=start['context_id'], request_id='next', lesson_key='second')
        next_start = {**start, **next_job}
        with self.assertRaises(runtime.LearningError):
            self.plan(next_start)
        with self.assertRaises(runtime.LearningError):
            self.lesson(next_start)
        self.lesson(next_start, lesson_key='second')
        self.assertEqual([lesson['key'] for lesson in self.read(start)['lessons']], ['first', 'second'])

    def test_private_derived_lesson_is_withheld_and_binding_survives_reopen(self):
        start = self.start(materials=[{'title':'Private','kind':'notes','sharing':'metadata-only','excerpt':'TOP SECRET'}])
        self.plan(start)
        sid = self.read(start)['sources'][0]['id']
        self.lesson(start, channel='ui_direct', content='TOP SECRET', source_ids=[sid])
        self.call('course_bind', context_id=start['context_id'], session_id='durable', scope='profile')
        self.store = runtime.Store(self.store.path)
        patch.object(runtime, 'store', return_value=self.store).start()
        self.assertEqual(self.read(start)['binding']['session_id'], 'durable')
        self.assertNotIn('TOP SECRET', json.dumps(self.read(start, 'chat_relayed')))
        self.assertNotIn('durable', json.dumps(self.read(start, 'chat_relayed')))

    def test_link_results_remain_scoped_and_do_not_claim_independent_verification(self):
        start = self.start(materials=[{'title':'Repository','kind':'url','url':'https://example.org/repo','sharing':'selected-excerpts'}, {'title':'Private','kind':'url','url':'https://example.org/private','sharing':'metadata-only'}, {'title':'Notes','kind':'text','excerpt':'Original','sharing':'selected-excerpts'}])
        sources = self.read(start)['sources']
        def result(source_id, **fields):
            return self.call('course_source', channel='chat_relayed', context_id=start['context_id'], job_id=start['job_id'], source_id=source_id, **fields)
        with self.assertRaises(runtime.LearningError):
            result(sources[0]['id'], status='read')
        with self.assertRaises(runtime.LearningError):
            result(sources[1]['id'], status='read', excerpt='Private')
        with self.assertRaises(runtime.LearningError):
            result(sources[2]['id'], status='read', excerpt='Rewritten notes')
        failed = result(sources[0]['id'], status='failed', error='Access denied')
        self.assertEqual(failed['source']['read_status'], 'failed')
        read = result(sources[0]['id'], status='read', excerpt='The repository contains a FIFO queue.')
        self.assertEqual(read['source']['read_status'], 'read')
        self.assertEqual(read['source']['verification'], 'agent-reported retrieval; not independently verified')
        self.assertEqual(result(sources[0]['id'], status='read', excerpt='The repository contains a FIFO queue.'), read)
        with self.assertRaises(runtime.LearningError):
            result(sources[0]['id'], status='read', excerpt='Overwrite evidence')
        self.plan(start)
        self.lesson(start, source_ids=[sources[0]['id']])
        with self.assertRaises(runtime.LearningError):
            result(sources[0]['id'], status='failed', error='Late reply')

    def test_reopen_recovers_active_job_authority_for_publication_and_stop(self):
        start = self.start()
        opened = self.call('course_open', track_id=start['track_id'])
        self.assertEqual(opened, {**start, 'lesson_key': None})
        self.plan(opened)
        reopened = self.call('course_open', track_id=start['track_id'])
        self.assertEqual(reopened, {**start, 'lesson_key': 'first'})
        self.lesson(reopened)
        completed = self.call('course_open', track_id=start['track_id'])
        self.assertNotEqual(completed['context_id'], start['context_id'])
        self.assertNotIn('job_id', completed)
        next_job = self.call('course_generate', context_id=completed['context_id'], request_id='next', lesson_key='second')
        restored = self.call('course_open', track_id=start['track_id'])
        self.assertEqual(restored, {**completed, **next_job, 'lesson_key': 'second'})
        self.call('course_job_status', context_id=restored['context_id'], job_id=restored['job_id'], status='stopped')
        self.assertEqual(self.read(start)['jobs'][-1]['status'], 'stopped')
        with self.assertRaises(runtime.LearningError):
            self.lesson(restored, lesson_key='second')

    def test_reopen_stops_unpublishable_jobs_without_reactivating_old_context(self):
        for reason in ('revoked', 'paused', 'archived'):
            with self.subTest(reason=reason):
                start = self.start(reason)
                if reason == 'revoked':
                    self.call('leave', context_id=start['context_id'])
                else:
                    self.call('track_status', context_id=start['context_id'], revision=1, status=reason)
                opened = self.call('course_open', track_id=start['track_id'])
                self.assertNotEqual(opened['context_id'], start['context_id'])
                self.assertNotIn('job_id', opened)
                self.assertEqual(self.read(start)['jobs'][0]['status'], 'stopped')
                with self.assertRaises(runtime.LearningError):
                    self.plan(start)
                replacement = self.call('course_generate', context_id=opened['context_id'], request_id='replacement')
                self.plan({**opened, **replacement})
                self.lesson({**opened, **replacement})

    def test_legacy_course_generation_preserves_assessed_objectives_and_brief(self):
        old = self.call('start', title='Existing learning')
        context = old['context_id']
        self.call('brief', context_id=context, revision=1, brief='Original agreed brief', objectives=['Explain FIFO'], assumptions=['Original assumption'])
        track = self.call('approve', context_id=context, revision=2)['track']
        objective_id = track['objective_details'][0]['id']
        activity = self.call('activity', context_id=context, title='FIFO', kind='prediction', prompt='Which item leaves first?', criteria=['Identify first item'], solution='A', objective_ids=[objective_id])['activity']
        run = self.call('run', context_id=context, activity_id=activity['id'])
        attempt = self.call('submit', context_id=context, run_id=run['run_id'], answer='A')['attempt']
        self.call('assess', context_id=context, attempt_id=attempt['id'], method='self', outcome='demonstrated', feedback='A entered first.')
        previous_progress = self.call('state')['objective_progress']
        opened = self.call('course_open', track_id=old['track_id'])
        job = self.call('course_generate', context_id=opened['context_id'], request_id='legacy-outline')
        self.plan({**opened, **job})
        current = self.read(old)['track']
        self.assertEqual(current['objective_details'], track['objective_details'])
        self.assertEqual(current['brief'], 'Original agreed brief')
        self.assertEqual(current['assumptions'], ['Original assumption'])
        self.assertEqual(self.call('state')['objective_progress'], previous_progress)
        followup = self.call('activity', context_id=opened['context_id'], title='Another FIFO', kind='prediction', prompt='Which item?', criteria=['Identify first item'], solution='B', objective_ids=[objective_id])['activity']
        self.assertEqual(followup['objective_ids'], [objective_id])

    def test_existing_track_can_continue_without_rewriting_old_records(self):
        old = self.call('start', title='Old track')
        view = self.read(old)
        self.assertEqual(view['outline'], [])
        context = self.call('course_open', track_id=old['track_id'])['context_id']
        job = self.call('course_generate', context_id=context, request_id='legacy')
        self.plan({**old, **job, 'context_id':context})
        self.lesson({**old, **job, 'context_id':context})
        self.assertEqual(len(self.call('state')['tracks']), 1)


if __name__ == '__main__':
    unittest.main()

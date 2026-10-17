"""Continuity across on-demand publication and human-approved revisions."""
import tempfile
import unittest
from pathlib import Path
from learning_store import Store, LearningError

class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.s=Store(Path(self.temp.name)/'data.db')
        self.start=self.s.dispatch('course_start',dict(request_id='start',title='Kafka',intent='topic',level='beginner',materials=[]))
        self.outline=[dict(key=k,title=k.upper(),goal='Learn '+k) for k in ['one','two','three']]
        self.call('course_plan',job_id=self.start['job_id'],summary='Kafka',assumptions=[],lessons=self.outline)
        self.call('course_lesson',job_id=self.start['job_id'],lesson_key='one',content='Orders use order_id as the partition key.',source_ids=[])
        self.publish('two','Consumers read the same orders topic.')
    def call(self,action,**params):
        return self.s.dispatch(action,{'context_id':self.start['context_id'],**params})
    def read(self):return self.s.dispatch('course_read',{'track_id':self.start['track_id']})
    def publish(self,key,content):
        job=self.call('course_generate',request_id=key,lesson_key=key)
        return self.call('course_lesson',job_id=job['job_id'],lesson_key=key,content=content,source_ids=[])
    def revise(self,content,extra=None):
        p=self.call('course_propose',request_id='edit'+str(self.read()['revision']),base_revision=self.read()['revision'],mode='revise',summary='Update example',lessons=[dict(lesson_key='one',content=content,source_ids=[])]+(extra or []))['proposal']
        self.call('course_apply',proposal_id=p['id'])
    def test_context_has_saved_content_in_order_without_future_lessons(self):
        context=self.call('course_context',lesson_key='three')
        self.assertEqual([l['key'] for l in context['earlier_lessons']],['one','two'])
        self.assertIn('order_id',context['earlier_lessons'][0]['content'])
        self.assertEqual(context['revision'],1)
        second=self.call('course_context',lesson_key='two')
        self.assertEqual([l['key'] for l in second['earlier_lessons']],['one'])
    def test_applied_change_flags_only_saved_later_lessons_and_keep_is_persistent(self):
        self.call('course_position',lesson_key='two',completed=['two'])
        self.revise('Payments use payment_id as the partition key.')
        course=self.read();self.assertEqual(set(course['continuity_flags']),{'two'})
        self.assertEqual(course['position']['completed'],['two'])
        self.assertEqual(next(l for l in course['lessons'] if l['key']=='two')['content'],'Consumers read the same orders topic.')
        self.call('course_continuity_keep',lesson_key='two',expected_revision=2,warning_id=course['continuity_flags']['two']['warning_id'])
        self.assertEqual(self.read()['continuity_flags'],{})
        self.revise('Payments now use account_id as the partition key.')
        self.assertIn('two',self.read()['continuity_flags'])
        with self.assertRaises(LearningError):self.call('course_continuity_keep',lesson_key='two',expected_revision=2,warning_id=course['continuity_flags']['two']['warning_id'])
    def test_formatting_change_does_not_flag_and_coordinated_revision_clears_flag(self):
        self.revise('**Orders** use order_id as the partition key.')
        self.assertEqual(self.read()['continuity_flags'],{})
        self.revise('Payments use payment_id as the partition key.')
        self.assertIn('two',self.read()['continuity_flags'])
        self.revise('Payments use account_id as the partition key.',[dict(lesson_key='two',content='Consumers read payments.',source_ids=[])])
        self.assertEqual(self.read()['continuity_flags'],{})
    def test_generation_uses_revised_content_and_marks_unpublished_prerequisites(self):
        self.revise('Payments use payment_id.')
        context=self.call('course_context',lesson_key='three')
        self.assertIn('payment_id',context['earlier_lessons'][0]['content'])
        self.assertTrue(context['earlier_lessons'][1]['may_need_update'])
        self.assertEqual(context['selected_lesson'],None)
    def test_context_is_bounded_and_sharing_filtered_even_for_ui_request(self):
        self.revise('x'*50000)
        context=self.call('course_context',lesson_key='three')
        self.assertLessEqual(sum(len(l['content']) for l in context['earlier_lessons']),24000)
        self.assertTrue(context['earlier_lessons'][0]['truncated'])
        private=self.call('source',title='Private',kind='notes',sharing='metadata-only',excerpt='SECRET')['source']
        p=self.call('course_propose',request_id='private',base_revision=2,mode='revise',summary='Private',lessons=[dict(lesson_key='one',content='SECRET LESSON',source_ids=[private['id']])])['proposal']
        self.call('course_apply',proposal_id=p['id'])
        context=self.call('course_context',lesson_key='three')
        self.assertNotIn('SECRET',str(context));self.assertTrue(context['earlier_lessons'][0]['content_withheld'])
    def test_keep_requires_human_and_active_context(self):
        with self.assertRaises(LearningError):self.s.dispatch('course_continuity_keep',dict(context_id=self.start['context_id'],lesson_key='two',expected_revision=1),channel='chat_relayed')

    def test_out_of_order_context_and_publish_race(self):
        # Add a future outline slot, then start its generation before its predecessor exists.
        outline=self.outline+[dict(key='four',title='Four',goal='Later')]
        p=self.call('course_propose',request_id='extend',base_revision=1,mode='extend',summary='Extend',outline=outline,lessons=[])['proposal']
        self.call('course_apply',proposal_id=p['id'])
        context=self.call('course_context',lesson_key='four')
        self.assertEqual(context['missing_earlier_lessons'],['three'])
        job=self.call('course_generate',request_id='four',lesson_key='four')
        self.publish('three','New prerequisite')
        with self.assertRaisesRegex(LearningError,'earlier lesson changed'):
            self.call('course_lesson',job_id=job['job_id'],lesson_key='four',content='Stale foundation',source_ids=[])

    def test_removed_or_reordered_foundation_flags_retained_lesson(self):
        p=self.call('course_propose',request_id='remove',base_revision=1,mode='revise',summary='Remove foundation',outline=self.outline[1:],lessons=[])['proposal']
        self.call('course_apply',proposal_id=p['id'])
        self.assertIn('two',self.read()['continuity_flags'])
        self.assertNotIn('three',self.read()['continuity_flags'])

    def test_code_and_negation_changes_are_not_treated_as_formatting(self):
        self.assertNotEqual(self.s._continuity_text('Use `a*b`.'),self.s._continuity_text('Use `ab`.'))
        self.assertNotEqual(self.s._continuity_text('Reading deletes events.'),self.s._continuity_text('Reading does not delete events.'))

    def test_new_earlier_publication_reflags_without_allowing_stale_keep(self):
        outline=self.outline+[dict(key='four',title='Four',goal='Later')]
        p=self.call('course_propose',request_id='extend',base_revision=1,mode='extend',summary='Extend',outline=outline,lessons=[])['proposal']
        self.call('course_apply',proposal_id=p['id'])
        self.publish('four','Based on planned prerequisites.')
        self.revise('Payments now use account_id.')
        old=self.read()['continuity_flags']['four']['warning_id']
        self.publish('three','New saved prerequisite.')
        current=self.read()['continuity_flags']['four']['warning_id']
        self.assertNotEqual(old,current)
        with self.assertRaisesRegex(LearningError,'warning changed'):
            self.call('course_continuity_keep',lesson_key='four',expected_revision=3,warning_id=old)
        self.call('course_continuity_keep',lesson_key='four',expected_revision=3,warning_id=current)
        reopened=Store(Path(self.temp.name)/'data.db')
        self.assertNotIn('four',reopened.dispatch('course_read',{'track_id':self.start['track_id']})['continuity_flags'])

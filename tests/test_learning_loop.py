"""Contracts for the evidence-linked learning loop, using real persisted records."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from learning_store import Store, LearningError


class LearningLoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'data.db'
        self.store = Store(self.path, clock=lambda: datetime(2026, 10, 16, tzinfo=timezone.utc))
        self.entry = self.store.dispatch('start', {'title': 'Retries'})
        self.context = self.entry['context_id']
        self.track_id = self.entry['track_id']

    def call(self, action, channel='ui_direct', **params):
        return self.store.dispatch(action, {'context_id': self.context, **params}, channel=channel)

    def setup_path(self):
        track = self.call('brief', revision=1, brief='Understand and implement retries', objectives=['Explain idempotency', 'Implement retry handling'])['track']
        self.call('approve', revision=2)
        return track.get('objective_details', [])

    def activity(self, **changes):
        fields = dict(title='Retry once', kind='prediction', prompt='What happens on retry?', criteria=['Reason about duplicates', 'Explain the fix'], solution='CANONICAL SOLUTION', hints={'nudge': 'Count the writes'}, source_ids=[])
        fields.update(changes)
        return self.call('activity', **fields)['activity']

    def submit(self, activity, **changes):
        run = self.call('run', activity_id=activity['id'])
        return self.call('submit', run_id=run['run_id'], answer='The second request must reuse the first result.', **changes)['attempt']

    def assess(self, attempt, **changes):
        params = dict(attempt_id=attempt['id'], method='self', outcome='developing', feedback='The duplicate effect is clear; specify the storage boundary.')
        params.update(changes)
        return self.call('assess', **params)

    def state(self, channel='ui_direct'):
        return self.store.dispatch('state', {}, channel=channel)

    def test_objective_ids_survive_reordering_and_legacy_reads_do_not_write(self):
        objectives = self.setup_path()
        self.assertEqual(len(objectives), 2)
        before = sqlite3.connect(self.path).execute('SELECT id,data FROM records ORDER BY seq').fetchall()
        first = self.state()
        self.assertIn('objective-evidence-v1', first['capabilities'])
        self.store.dispatch('resume_brief', {'track_id': self.track_id})
        self.assertEqual(before, sqlite3.connect(self.path).execute('SELECT id,data FROM records ORDER BY seq').fetchall())
        changed = self.call('brief', revision=3, brief='Reorder', objectives=['Implement retry handling', 'Explain idempotency'])['track']
        self.assertEqual(changed['objective_details'], objectives[::-1])
        renamed = self.call('brief', revision=4, brief='Rename', objectives=['Explain retry safety'])['track']
        self.assertNotIn(renamed['objective_details'][0]['id'], [o['id'] for o in objectives])

    def test_profile_partial_update_validation_and_empty_profile(self):
        entry = self.store.dispatch('start', {'title':'Profile', 'learner_profile': {'background':'Python', 'goal':'Safer APIs', 'minutes':30}})
        result = self.store.dispatch('brief', {'context_id':entry['context_id'], 'revision':1, 'brief':'Plan', 'objectives':[], 'learner_profile':{'minutes':15}})
        self.assertEqual(result['track']['learner_profile'], {'background':'Python', 'goal':'Safer APIs', 'minutes':15})
        for profile in ({'minutes':0}, {'minutes':True}, {'minutes':241}, {'goal':'x'*2001}, {'extra':'x'}, []):
            with self.subTest(profile=profile), self.assertRaises(LearningError):
                self.store.dispatch('start', {'title':'Bad', 'learner_profile':profile})
        self.store.dispatch('start', {'title':'Empty', 'learner_profile':{}})

    def test_objective_links_are_track_scoped_and_revision_preserves_snapshot(self):
        objectives = self.setup_path()
        self.assertTrue(objectives)
        activity = self.activity(objective_ids=[objectives[0]['id']], competency='practical', purpose='diagnostic')
        self.assertEqual(activity['objective_snapshots'], [objectives[0]])
        other = self.store.dispatch('start', {'title':'Other'})
        with self.assertRaises(LearningError):
            self.store.dispatch('activity', {'context_id':other['context_id'], 'title':'Bad','kind':'trace','prompt':'x','criteria':['x'],'solution':'x','objective_ids':[objectives[0]['id']]})
        revised = self.call('activity_revision', activity_id=activity['id'], title='Changed', kind='build', prompt='Implement it', criteria=['One effect'], solution='Use a key')['activity']
        self.assertEqual(revised['objective_ids'], activity['objective_ids'])
        self.assertEqual((revised['competency'], revised['purpose']), ('practical', 'diagnostic'))
        self.call('brief', revision=3, brief='Renamed', objectives=['New objective'])
        historical = self.call('activity_read', activity_id=activity['id'])['activity']
        self.assertEqual(historical['objective_snapshots'], [objectives[0]])
        for fields in ({'objective_ids':['missing']}, {'competency':'unknown'}, {'purpose':'unknown'}):
            with self.assertRaises(LearningError): self.activity(**fields)

    def test_generated_help_exact_content_retry_conflict_and_no_solution_unlock(self):
        activity = self.activity()
        run = self.call('run', activity_id=activity['id'])
        params = dict(run_id=run['run_id'], level='full-solution-shown', content='  GENERATED\nanswer  ', request_id='help-1')
        first = self.call('help', channel='chat_relayed', **params)
        self.assertEqual(first['content'], params['content'])
        self.assertEqual(first['help']['content'], params['content'])
        self.assertEqual(first['help']['origin'], 'generated')
        self.assertEqual(first['help']['author_kind'], 'chat-agent')
        self.assertNotIn('CANONICAL', json.dumps(first))
        self.assertNotIn('solution', self.call('activity_read', activity_id=activity['id'])['activity'])
        duplicate = self.call('help', channel='chat_relayed', **params)
        self.assertEqual(first['help'], duplicate['help'])
        self.assertTrue(duplicate['duplicate'])
        for changes in ({'content':'different'}, {'level':'nudge'}):
            with self.assertRaises(LearningError): self.call('help', channel='chat_relayed', **{**params, **changes})
        with self.assertRaises(LearningError): self.call('help', **params)
        attempt = self.call('submit', run_id=run['run_id'], answer='My answer')['attempt']
        self.assertEqual(len(attempt['assistance_events']), 1)
        self.assertTrue(self.call('help', channel='chat_relayed', **params)['duplicate'])

    def test_generated_help_requires_key_and_preserves_help_across_revision(self):
        activity = self.activity()
        run = self.call('run', activity_id=activity['id'])
        with self.assertRaises(LearningError): self.call('help', run_id=run['run_id'], level='nudge', content='Generated')
        self.call('help', run_id=run['run_id'], level='nudge')
        revised = self.call('activity_revision', activity_id=activity['id'], title='Revision', kind='build', prompt='Implement', criteria=['Safe'], solution='Key')['activity']
        attempt = self.submit(revised)
        self.assertEqual(attempt['assistance'], 'nudge')
        self.assertTrue(attempt['prior_help_exposure'])
        self.assertEqual(attempt['assistance_events'][0]['content'], 'Count the writes')

    def test_metadata_only_help_and_nested_feedback_never_reach_model(self):
        objectives = self.setup_path()
        self.assertTrue(objectives)
        source = self.call('source', title='Private', excerpt='PRIVATE', sharing='metadata-only')['source']
        activity = self.activity(source_ids=[source['id']], objective_ids=[objectives[0]['id']])
        run = self.call('run', activity_id=activity['id'])
        self.call('help', run_id=run['run_id'], level='nudge', content='SECRET HELP', request_id='secret')
        attempt = self.call('submit', run_id=run['run_id'], answer='SECRET ANSWER')['attempt']
        self.assess(attempt, feedback='SECRET FEEDBACK', uncertainty='SECRET UNCERTAINTY', criterion_results=[{'index':0,'outcome':'developing','feedback':'SECRET CRITERION'}, {'index':1,'outcome':'demonstrated','feedback':'SECRET SECOND'}])
        for action, params in [('state', {}), ('export', {}), ('track', {'track_id':self.track_id}), ('resume_brief', {'track_id':self.track_id}), ('activity_read', {'activity_id':activity['id'], 'context_id':self.context})]:
            result = self.store.dispatch(action, params, channel='chat_relayed')
            self.assertNotIn('SECRET', json.dumps(result), action)
        events = self.state('chat_relayed')['attempts'][0]['assistance_events']
        self.assertEqual(events[0]['level'], 'nudge')
        self.assertEqual(len(events), 1)
        self.assertEqual(self.state()['attempts'][0]['assistance_events'][0]['content'], 'SECRET HELP')

    def test_criterion_results_must_cover_rubric_and_match_weakest(self):
        attempt = self.submit(self.activity())
        valid = [{'index':0,'outcome':'developing','feedback':'Missing persistence'}, {'index':1,'outcome':'demonstrated','feedback':'Good'}]
        for results, outcome in [(valid[:1],'developing'), ([valid[0], valid[0]],'developing'), (valid,'demonstrated'), ([{**valid[0],'index':True}, valid[1]],'developing')]:
            with self.subTest(results=results), self.assertRaises(LearningError): self.assess(attempt, criterion_results=results, outcome=outcome)
        assessment = self.assess(attempt, criterion_results=valid, uncertainty='No runtime trace available')['assessment']
        self.assertEqual(assessment['criterion_results'], valid)
        self.assertEqual(assessment['uncertainty'], 'No runtime trace available')

    def test_progress_counts_pending_disputed_and_superseded_evidence(self):
        objectives = self.setup_path()
        self.assertTrue(objectives)
        activity = self.activity(objective_ids=[objectives[0]['id']], competency='both')
        attempt = self.submit(activity)
        progress = self.state()['objective_progress'][0]
        self.assertEqual(progress['status'], 'awaiting-assessment')
        self.assertEqual(progress['practical']['attempt_count'], 1)
        first = self.assess(attempt)['assessment']
        self.call('dispute', assessment_id=first['id'], reason='The key was in my answer')
        self.assertEqual(self.state()['objective_progress'][0]['status'], 'disputed')
        correction = self.assess(attempt, supersedes=first['id'], outcome='demonstrated', uncertainty='Self report only')['assessment']
        progress = self.state()['objective_progress'][0]
        self.assertEqual((progress['status'], progress['attempt_count'], progress['assessment_count']), ('demonstrated',1,1))
        self.assertEqual(progress['latest_assessment']['id'], correction['id'])
        self.assertEqual(progress['latest_assessment']['method'], 'self')
        self.assertEqual(progress['latest_assessment']['uncertainty'], 'Self report only')
        self.assertEqual(self.state()['objective_progress'][1]['status'], 'not-started')

    def test_next_actions_prioritize_disputes_assessment_and_objective_reviews(self):
        self.assertEqual(self.state()['next_actions'][0]['kind'], 'proposal')
        objectives = self.setup_path()
        self.assertTrue(objectives)
        original = self.activity(objective_ids=[objectives[0]['id']])
        retired = self.activity(title='Alternative', objective_ids=[objectives[0]['id']])
        alternative = self.call('activity_revision', activity_id=retired['id'], title='New alternative',kind='trace',prompt='Trace another key',criteria=['Result'],solution='One write')['activity']
        attempt = self.submit(original)
        self.assertEqual(self.state()['next_actions'][0]['kind'], 'assessment')
        result = self.assess(attempt)
        self.assertEqual(result['review']['objective_id'], objectives[0]['id'])
        self.assertEqual(result['review']['policy_version'], 2)
        self.assertEqual(result['review']['due_at'], '2026-10-19T00:00:00Z')
        self.call('review', review_id=result['review']['id'], due_at='2026-10-15T00:00:00Z')
        state = self.state()
        self.assertEqual(state['next_actions'][0]['kind'], 'review')
        self.assertEqual(state['next_actions'][0]['activity_id'], alternative['id'])
        self.assertEqual(state['reviews'][0]['suggested_activity_id'], alternative['id'])
        self.call('dispute', assessment_id=result['assessment']['id'], reason='Check')
        self.assertEqual(self.state()['next_actions'][0]['kind'], 'dispute')
        self.call('track_status', revision=3, status='paused')
        self.assertEqual(self.state()['next_actions'][0]['kind'], 'resume')

    def test_all_objectives_receive_one_review_and_reassessment_updates_them(self):
        objectives = self.setup_path()
        self.assertTrue(objectives)
        activity = self.activity(objective_ids=[o['id'] for o in objectives])
        attempt = self.submit(activity)
        first = self.assess(attempt)
        self.assertEqual(len(first['reviews']), 2)
        self.assess(attempt, supersedes=first['assessment']['id'], outcome='demonstrated')
        self.assertEqual(len(self.state()['reviews']), 2)
        self.assertTrue(all(r['due_at']=='2026-10-23T00:00:00Z' for r in self.state()['reviews']))

    def test_success_in_practical_work_does_not_erase_conceptual_gap(self):
        objective = self.setup_path()[0]['id']
        conceptual = self.activity(objective_ids=[objective], competency='conceptual')
        self.assess(self.submit(conceptual), outcome='needs-work')
        practical = self.activity(objective_ids=[objective], competency='practical')
        self.assess(self.submit(practical), outcome='demonstrated')
        progress = self.state()['objective_progress'][0]
        self.assertEqual(progress['conceptual']['status'], 'needs-work')
        self.assertEqual(progress['practical']['status'], 'demonstrated')
        self.assertEqual(progress['status'], 'needs-work')

    def test_objective_review_keeps_weaker_competency_date_and_trigger_provenance(self):
        objective = self.setup_path()[0]['id']
        conceptual = self.activity(objective_ids=[objective], competency='conceptual')
        first = self.assess(self.submit(conceptual), outcome='needs-work')
        self.store.clock = lambda: datetime(2026, 10, 18, tzinfo=timezone.utc)
        practical = self.activity(objective_ids=[objective], competency='practical')
        latest = self.assess(self.submit(practical), outcome='demonstrated')
        review = latest['review']
        self.assertEqual(review['due_at'], '2026-10-17T00:00:00Z')
        self.assertEqual(review['assessment_id'], latest['assessment']['id'])
        self.assertIn(first['assessment']['id'], review['basis_assessment_ids'])
        self.assertEqual(review['basis_status'], 'needs-work')

    def test_late_correction_cannot_delay_newer_weak_evidence(self):
        objective = self.setup_path()[0]['id']
        activity = self.activity(objective_ids=[objective])
        first_attempt = self.submit(activity)
        first = self.assess(first_attempt, outcome='developing')
        self.store.clock = lambda: datetime(2026, 10, 18, tzinfo=timezone.utc)
        second = self.assess(self.submit(activity), outcome='needs-work')
        self.store.clock = lambda: datetime(2026, 10, 20, tzinfo=timezone.utc)
        corrected = self.assess(first_attempt, outcome='demonstrated', supersedes=first['assessment']['id'])
        self.assertEqual(corrected['review']['due_at'], '2026-10-19T00:00:00Z')
        self.assertEqual(corrected['review']['basis_assessment_ids'], [second['assessment']['id']])

    def test_self_success_cannot_override_weaker_agent_schedule(self):
        objective = self.setup_path()[0]['id']
        attempt = self.submit(self.activity(objective_ids=[objective]))
        agent = self.assess(attempt, channel='chat_relayed', method='agent', outcome='needs-work')
        success = self.assess(attempt, outcome='demonstrated')
        self.assertEqual(success['review']['due_at'], '2026-10-17T00:00:00Z')
        self.assertIn(agent['assessment']['id'], success['review']['basis_assessment_ids'])

    def test_pending_and_disputed_objective_evidence_survives_other_feedback(self):
        objective = self.setup_path()[0]['id']
        conceptual = self.activity(objective_ids=[objective], competency='conceptual')
        attempt = self.submit(conceptual)
        first = self.assess(attempt, outcome='needs-work')
        practical = self.activity(objective_ids=[objective], competency='practical')
        pending = self.submit(practical)
        self.assertTrue(self.state()['reviews'][0]['pending_assessment'])
        corrected = self.assess(attempt, outcome='demonstrated', supersedes=first['assessment']['id'])
        self.assertTrue(corrected['review']['pending_assessment'])
        self.assertEqual(corrected['review']['due_at'], first['review']['due_at'])
        self.call('dispute', assessment_id=corrected['assessment']['id'], reason='Still incorrect')
        reviewed = self.assess(pending, outcome='demonstrated')['review']
        self.assertTrue(reviewed['disputed'])
        self.assertFalse(reviewed['pending_assessment'])
        self.assertEqual(reviewed['due_at'], first['review']['due_at'])
        self.assertIn('disput', reviewed['reason'].lower())

    def test_objective_manual_schedule_remains_explicit_through_feedback(self):
        objective = self.setup_path()[0]['id']
        attempt = self.submit(self.activity(objective_ids=[objective]))
        first = self.assess(attempt)
        self.call('review', review_id=first['review']['id'], due_at='2026-11-01T00:00:00Z')
        correction = self.assess(attempt, outcome='demonstrated', supersedes=first['assessment']['id'])
        self.assertEqual(correction['review']['due_at'], '2026-11-01T00:00:00Z')
        self.assertTrue(correction['review']['manual'])

    def test_new_attempt_feedback_resumes_automatic_objective_schedule(self):
        objective = self.setup_path()[0]['id']
        activity = self.activity(objective_ids=[objective])
        first = self.assess(self.submit(activity))
        self.call('review', review_id=first['review']['id'], due_at='2026-11-01T00:00:00Z')
        next_review = self.assess(self.submit(activity), outcome='needs-work')['review']
        self.assertFalse(next_review['manual'])
        self.assertEqual(next_review['due_at'], '2026-10-17T00:00:00Z')

    def test_objective_review_does_not_suggest_revision_relinked_elsewhere(self):
        objectives = self.setup_path()
        original = self.activity(objective_ids=[objectives[0]['id']])
        first = self.assess(self.submit(original))
        revised = self.call('activity_revision', activity_id=original['id'], title='Different target',kind='trace',prompt='Trace another thing',criteria=['Other'],solution='Other',objective_ids=[objectives[1]['id']])['activity']
        self.call('review', review_id=first['review']['id'], due_at='2026-10-15T00:00:00Z')
        state = self.state()
        self.assertIsNone(state['reviews'][0]['suggested_activity_id'])
        self.assertEqual(state['next_actions'][0]['kind'], 'author')
        self.assertEqual(state['next_actions'][0]['objective_id'], objectives[0]['id'])
        self.assertNotEqual(state['next_actions'][0].get('activity_id'), revised['id'])

    def test_restricted_revision_withholds_all_lineage_help_content(self):
        activity = self.activity()
        run = self.call('run', activity_id=activity['id'])
        self.call('help', run_id=run['run_id'], level='nudge', content='PRIOR HELP CONTENT', request_id='prior')
        private = self.call('source', title='Private notes', excerpt='Private', sharing='metadata-only')['source']
        revised = self.call('activity_revision', activity_id=activity['id'], title='Private revision', kind='build', prompt='Try', criteria=['Safe'], solution='Result', source_ids=[private['id']])['activity']
        self.submit(revised)
        for action, params in [('state',{}), ('activity_read',{'activity_id':revised['id'], 'context_id':self.context})]:
            result = self.store.dispatch(action, params, channel='chat_relayed')
            self.assertNotIn('PRIOR HELP CONTENT', json.dumps(result))
        self.assertEqual(self.state('chat_relayed')['attempts'][0]['assistance_events'][0]['level'], 'nudge')

    def test_legacy_records_without_additive_fields_remain_read_only(self):
        objectives = self.setup_path()
        activity = self.activity()
        run = self.call('run', activity_id=activity['id'])
        self.call('help', run_id=run['run_id'], level='nudge')
        attempt = self.call('submit', run_id=run['run_id'], answer='Original legacy answer')['attempt']
        self.assess(attempt)
        new_fields = {'learner_profile', 'objective_ids', 'objective_snapshots', 'competency', 'purpose', 'content', 'origin', 'author_kind', 'request_id'}
        with sqlite3.connect(self.path) as db:
            for ident, kind, raw in db.execute('SELECT id,kind,data FROM records').fetchall():
                record = json.loads(raw)
                remove = new_fields - {'author_kind'} if kind != 'help' else new_fields
                record = {key:value for key,value in record.items() if key not in remove}
                if kind == 'attempt':
                    record['assistance_events'] = [{key:value for key,value in event.items() if key not in new_fields} for event in record['assistance_events']]
                db.execute('UPDATE records SET data=? WHERE id=?', (json.dumps(record), ident))
            before = db.execute('SELECT id,data FROM records ORDER BY seq').fetchall()
        restored = Store(self.path, clock=self.store.clock)
        state = restored.dispatch('state', {})
        restored.dispatch('resume_brief', {'track_id':self.track_id})
        self.assertEqual(state['tracks'][0]['objective_details'], objectives)
        self.assertEqual(state['tracks'][0]['learner_profile'], {})
        self.assertEqual(state['activities'][0]['competency'], 'conceptual')
        self.assertEqual(state['activities'][0]['objective_ids'], [])
        self.assertEqual(state['attempts'][0]['answer'], 'Original legacy answer')
        with sqlite3.connect(self.path) as db:
            self.assertEqual(before, db.execute('SELECT id,data FROM records ORDER BY seq').fetchall())

    def test_structured_visuals_validate_references_and_gate_future_steps(self):
        visuals = [
            {'type':'state-machine','states':[{'id':'idle','label':'Idle'},{'id':'done','label':'Done'}], 'initial':'idle','steps':[{'from':'idle','to':'done','label':'Write','explanation':'First'}, {'from':'done','to':'done','label':'HIDDEN','explanation':'Return cached'}], 'visible_steps':1},
            {'type':'code-trace','code':'x = 1\nx += 1','language':'python','steps':[{'line':1,'label':'Set','explanation':'First','variables':[{'name':'x','value':'1'}]}, {'line':2,'label':'HIDDEN','explanation':'Increment','variables':[{'name':'x','value':'2'}]}], 'visible_steps':1},
        ]
        for visual in visuals:
            with self.subTest(kind=visual['type']):
                activity = self.activity(visual=visual)
                self.assertNotIn('HIDDEN', json.dumps(activity))
                self.submit(activity)
                self.assertIn('HIDDEN', json.dumps(self.call('activity_read', activity_id=activity['id'])))
                for invalid in ({**visual,'schema_version':2}, {**visual,'visible_steps':True}, {**visual,'steps':[]}):
                    with self.assertRaises(LearningError): self.activity(visual=invalid)
        invalid = copy.deepcopy(visuals[0]); invalid['steps'][1]['from']='idle'
        with self.assertRaises(LearningError): self.activity(visual=invalid)
        invalid = copy.deepcopy(visuals[1]); invalid['steps'][1]['line']=3
        with self.assertRaises(LearningError): self.activity(visual=invalid)
        invalid = copy.deepcopy(visuals[1]); invalid['steps'][0]['variables']=[{'name':'x','value':'1'}]*21
        with self.assertRaises(LearningError): self.activity(visual=invalid)


if __name__ == '__main__': unittest.main()

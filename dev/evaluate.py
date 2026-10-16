#!/usr/bin/env python3
"""Exercise learning contracts in temporary stores; does not evaluate an LLM."""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('learning_evaluation_runtime', ROOT / 'plugin/runtime.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


def require(condition, description):
    if not condition:
        raise AssertionError(description)


def session(store):
    # Use the actual adapter validation as well as the store, without resolving a host profile.
    runtime.store = lambda: store
    return lambda action, params=None, channel='ui_direct': runtime.action(action, params or {}, channel=channel)


def begin(call):
    entry = call('start', {'title': 'Retry safety', 'learner_profile': {'background': 'I write HTTP clients', 'goal': 'Explain duplicate writes', 'minutes': 20}})
    context = {'context_id': entry['context_id']}
    track = call('brief', {**context, 'revision': 1, 'brief': 'Distinguish a timeout from a failed write.', 'objectives': ['Explain duplicate writes']})['track']
    call('approve', {**context, 'revision': track['revision']})
    return context, entry['track_id'], track['objective_details'][0]['id']


def activity(call, context, objective, **extra):
    params = {**context, 'title': 'Lost response', 'kind': 'prediction', 'prompt': 'The response is lost after commit. What can a retry do?', 'criteria': ['Separate observation from server state', 'Explain duplicate effect'], 'solution': 'The write may have committed, so an unprotected retry may duplicate it.', 'hints': ['Trace the server before the timeout.'], 'objective_ids': [objective], 'competency': 'conceptual', 'purpose': 'diagnostic', **extra}
    return call('activity', params)['activity']


def read_only(call, store):
    before = store.path.read_bytes()
    first = call('state')
    require(first['tracks'] == [], 'An empty store must have no learning tracks')
    call('state')
    require(store.path.read_bytes() == before, 'Read-only browsing must not create records')
    try:
        call('start', {'title': 'Unauthorized'}, 'chat_relayed')
    except runtime.LearningError:
        pass
    else:
        raise AssertionError('Model tools must not enroll the learner')
    require(call('state')['tracks'] == [], 'Rejected enrollment must leave the store empty')


def learning_loop(call, store):
    context, track_id, objective = begin(call)
    first = activity(call, context, objective)
    alternate = activity(call, context, objective, title='Another operation', purpose='transfer', prompt='An email send times out. What must a safe retry account for?')
    run = call('run', {**context, 'activity_id': first['id']})['run_id']
    help_params = {**context, 'run_id': run, 'level': 'targeted-hint', 'content': 'A timeout reports what the client saw. What did the server already do?', 'request_id': 'eval-generated-hint-1'}
    help_event = call('help', help_params, 'chat_relayed')['help']
    require(call('help', help_params, 'chat_relayed')['help']['id'] == help_event['id'], 'Retrying help must not duplicate assistance')
    answer = 'The client saw no response. The first write may already exist; retrying could repeat it.'
    attempt = call('submit', {**context, 'run_id': run, 'answer': answer})['attempt']
    require(attempt['answer'] == answer, 'Answer text must be verbatim')
    require(attempt['assistance_events'][0]['content'] == help_params['content'], 'Actual generated help must survive submission')
    pending = next(a for a in call('state')['next_actions'] if a['track_id'] == track_id)
    require(pending['kind'] == 'assessment', 'Pending evidence needs assessment before further practice')
    result = call('assess', {**context, 'attempt_id': attempt['id'], 'method': 'agent', 'feedback': 'You separated observations and server state. Explain how the key is recorded next.', 'outcome': 'developing', 'uncertainty': 'This answer does not demonstrate an implementation.', 'criterion_results': [{'index': 0, 'outcome': 'demonstrated', 'feedback': 'Correctly identifies the missing response.'}, {'index': 1, 'outcome': 'developing', 'feedback': 'Needs the atomic storage condition.'}]}, 'chat_relayed')
    require(result['review']['policy_version'] == 2, 'Linked activities must schedule objective review')
    require(result['review']['objective_id'] == objective, 'Review must retain the objective identity')
    state = call('state')
    progress = next(p for p in state['objective_progress'] if p['objective_id'] == objective)
    require(progress['status'] == 'developing', 'Objective status must reflect the evidence')
    require(progress['assisted_attempt_count'] == 1, 'Progress must expose assisted evidence')
    next_action = next(a for a in state['next_actions'] if a['track_id'] == track_id)
    require(next_action.get('activity_id') == alternate['id'], 'Recommend a different linked example')
    call('leave', context)
    try:
        call('run', {**context, 'activity_id': alternate['id']})
    except runtime.LearningError:
        pass
    else:
        raise AssertionError('Leaving tracking must revoke future writes')


def private_material(call, store):
    context, track_id, objective = begin(call)
    secret = 'PRIVATE_EVALUATION_SOURCE'
    source = call('source', {**context, 'title': 'Private reference', 'kind': 'notes', 'excerpt': secret, 'sharing': 'metadata-only'})['source']
    item = activity(call, context, objective, source_ids=[source['id']], prompt=secret, solution=secret)
    run = call('run', {**context, 'activity_id': item['id']})['run_id']
    call('help', {**context, 'run_id': run, 'level': 'nudge', 'content': secret, 'request_id': 'private-help'})
    attempt = call('submit', {**context, 'run_id': run, 'answer': secret})['attempt']
    call('assess', {**context, 'attempt_id': attempt['id'], 'method': 'self', 'feedback': secret, 'outcome': 'developing', 'uncertainty': secret, 'criterion_results': [{'index': 0, 'outcome': 'developing', 'feedback': secret}, {'index': 1, 'outcome': 'developing', 'feedback': secret}]})
    for name, params in [('state', {}), ('track', {'track_id': track_id}), ('resume_brief', {'track_id': track_id})]:
        require(secret not in json.dumps(call(name, params, 'chat_relayed')), f'{name} must redact nested restricted material')
    require(secret in json.dumps(call('export')), 'Human export must retain the actual evidence')


SCENARIOS = [('ad-hoc-and-explicit-entry', read_only), ('diagnosis-help-feedback-next-activity', learning_loop), ('nested-source-sharing', private_material)]


def evaluate():
    results = []
    with tempfile.TemporaryDirectory(prefix='hermes-learning-eval-') as directory:
        for index, (name, scenario) in enumerate(SCENARIOS):
            try:
                store = runtime.Store(Path(directory) / f'{index}.db', clock=lambda: datetime(2026, 10, 16, 12, tzinfo=timezone.utc))
                scenario(session(store), store)
                results.append({'scenario': name, 'passed': True})
            except Exception as exc:
                results.append({'scenario': name, 'passed': False, 'error': f'{type(exc).__name__}: {exc}'})
    return {'kind': 'deterministic-learning-contracts', 'live_model_evaluated': False, 'teaching_quality_evaluated': False, 'passed': all(r['passed'] for r in results), 'scenarios': results, 'next_evaluation': 'Run the conversation cases in docs/evaluations/tutoring.md with an actual model and review the transcript and saved records.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Optional report JSON path; only synthetic evaluation data is written.')
    args = parser.parse_args()
    result = evaluate()
    output = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.write_text(output, encoding='utf-8')
    print(output, end='')
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())

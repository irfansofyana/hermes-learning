"""Profile-local adapters and strict versioned action contracts.

The HTTP module is loaded without package context by Hermes. Keep storage
resolution lazy and per-operation so switching profiles cannot retain a store.
"""
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('hermes_learning_service', ROOT / 'learning_store.py')
if _spec is None or _spec.loader is None:
    raise RuntimeError('Cannot load the learning service')
_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)
Store, LearningError = _module.Store, _module.LearningError


def string(maximum=20000, minimum=1):
    return {'type': 'string', 'minLength': minimum, 'maxLength': maximum}


def enum(*values):
    return {'type': 'string', 'enum': list(values)}


def array(items, maximum=100):
    return {'type': 'array', 'items': items, 'maxItems': maximum}


ID = string(100)
CONTEXT = {'context_id': ID}
REVISION = {'revision': {'type': 'integer', 'minimum': 0}}
def object_schema(properties, required=()):
    return {'type': 'object', 'properties': properties, 'required': list(required), 'additionalProperties': False}


LEARNER_PROFILE = object_schema({'background': string(2000, 0), 'goal': string(2000, 0), 'minutes': {'type': 'integer', 'minimum': 1, 'maximum': 240}})
VISUAL_NODE = object_schema({'id': string(60), 'label': string(150)}, ['id', 'label'])
VISUAL_COMMON = {'schema_version': {'type': 'integer', 'minimum': 1, 'maximum': 1}, 'title': string(300, 0), 'visible_steps': {'type': 'integer', 'minimum': 0, 'maximum': 30}}
TRANSITION = object_schema({'from': string(60), 'to': string(60), 'label': string(300), 'explanation': string(2000, 0)}, ['from', 'to', 'label'])
TRACE_STEP = object_schema({'line': {'type': 'integer', 'minimum': 1, 'maximum': 12000}, 'label': string(300), 'explanation': string(2000, 0), 'variables': array(object_schema({'name': string(150), 'value': string(2000, 0)}, ['name', 'value']), 20)}, ['line', 'label'])
VISUAL = {'anyOf': [
    {'type': 'null'},
    object_schema({**VISUAL_COMMON, 'type': enum('sequence'), 'participants': array(VISUAL_NODE, 10), 'steps': array(TRANSITION, 30)}, ['type', 'participants', 'steps']),
    object_schema({**VISUAL_COMMON, 'type': enum('state-machine'), 'states': array(VISUAL_NODE, 20), 'initial': string(60), 'steps': array(TRANSITION, 30)}, ['type', 'states', 'initial', 'steps']),
    object_schema({**VISUAL_COMMON, 'type': enum('code-trace'), 'code': string(12000), 'language': string(40, 0), 'steps': array(TRACE_STEP, 30)}, ['type', 'code', 'steps']),
]}
CRITERION_RESULT = object_schema({'index': {'type': 'integer', 'minimum': 0, 'maximum': 29}, 'outcome': enum('needs-work', 'developing', 'demonstrated'), 'feedback': string(2000)}, ['index', 'outcome', 'feedback'])


# Optional parameters are omitted from required; service applies their defaults.
SPECS = {
    'state': ({}, []),
    'start': ({'title': string(300), 'interest': string(12000, 0), 'learner_profile': LEARNER_PROFILE}, ['title']),
    'resume': ({'track_id': ID}, ['track_id']),
    'leave': (CONTEXT, ['context_id']),
    'track': ({'track_id': ID}, ['track_id']),
    'brief': ({**CONTEXT, **REVISION, 'brief': string(12000), 'learner_profile': LEARNER_PROFILE, 'objectives': array(string(1000), 30), 'assumptions': array(string(1000), 30), 'open_questions': array(string(1000), 30)}, ['context_id', 'revision', 'brief', 'objectives']),
    'approve': ({**CONTEXT, **REVISION}, ['context_id', 'revision']),
    'track_status': ({**CONTEXT, **REVISION, 'status': enum('active', 'paused', 'archived')}, ['context_id', 'revision', 'status']),
    'source': ({**CONTEXT, 'recommendation_id': ID, 'title': string(300), 'kind': string(100), 'url': string(2000, 0), 'locator': string(2000, 0), 'excerpt': string(50000, 0), 'sharing': enum('metadata-only', 'selected-excerpts', 'full-text'), 'verification': string(1000)}, ['context_id', 'title', 'kind', 'sharing']),
    'source_read': ({'source_id': ID}, ['source_id']),
    'activity': ({**CONTEXT, 'title': string(300), 'kind': enum('explanation', 'prediction', 'trace', 'build'), 'prompt': string(12000), 'description': string(12000, 0), 'criteria': {'anyOf': [string(2000), array(string(2000), 30)]}, 'solution': string(12000), 'hints': {'anyOf': [array(string(5000), 3), {'type': 'object', 'properties': {key: string(5000) for key in ('nudge', 'targeted-hint', 'worked-step')}, 'required': [], 'additionalProperties': False}]}, 'source_ids': array(ID, 30), 'objective_ids': array(ID, 30), 'competency': enum('conceptual', 'practical', 'both'), 'purpose': enum('diagnostic', 'practice', 'transfer'), 'visual': VISUAL}, ['context_id', 'title', 'kind', 'prompt', 'criteria', 'solution']),
    'activity_read': ({'activity_id': ID, **CONTEXT}, ['activity_id']),
    'run': ({**CONTEXT, 'activity_id': ID}, ['context_id', 'activity_id']),
    'help': ({**CONTEXT, 'run_id': ID, 'level': enum('nudge', 'targeted-hint', 'worked-step', 'full-solution-shown'), 'content': string(5000), 'request_id': string(100)}, ['context_id', 'run_id', 'level']),
    'submit': ({**CONTEXT, 'run_id': ID, 'answer': string(30000)}, ['context_id', 'run_id', 'answer']),
    'assess': ({**CONTEXT, 'attempt_id': ID, 'method': enum('self', 'agent'), 'feedback': string(12000), 'outcome': enum('needs-work', 'developing', 'demonstrated'), 'supersedes': ID, 'criterion_results': array(CRITERION_RESULT, 30), 'uncertainty': string(2000, 0)}, ['context_id', 'attempt_id', 'method', 'feedback', 'outcome']),
    'dispute': ({**CONTEXT, 'assessment_id': ID, 'reason': string(4000)}, ['context_id', 'assessment_id', 'reason']),
    'review': ({**CONTEXT, 'review_id': ID, 'due_at': string(80)}, ['context_id', 'review_id', 'due_at']),
    'resume_brief': ({'track_id': ID}, ['track_id']),
    'export': ({}, []),
}


SPECS['recommendation'] = ({**CONTEXT, 'title': string(300), 'url': string(2000, 0), 'reason': string(4000), 'prerequisites': array(string(1000), 30), 'verification': string(1000), 'locator': string(2000, 0)}, ['context_id', 'title', 'reason'])
SPECS['recommendation_decide'] = ({**CONTEXT, 'recommendation_id': ID, 'status': enum('accepted', 'declined')}, ['context_id', 'recommendation_id', 'status'])
SPECS['quote_check'] = ({'source_id': ID, 'quote': string(12000)}, ['source_id', 'quote'])
SPECS['activity_revision'] = ({**SPECS['activity'][0], 'activity_id': ID}, [*SPECS['activity'][1], 'activity_id'])


MATERIAL = object_schema({'title': string(300), 'kind': string(100), 'url': string(2000, 0), 'locator': string(2000, 0), 'excerpt': string(50000, 0), 'sharing': enum('metadata-only', 'selected-excerpts', 'full-text')}, ['title', 'kind', 'sharing'])
LESSON_OUTLINE = object_schema({'key': string(80), 'title': string(300), 'goal': string(2000)}, ['key', 'title', 'goal'])
SPECS.update({
    'course_source': ({**CONTEXT, 'job_id': ID, 'source_id': ID, 'status': enum('read', 'failed', 'unsupported'), 'excerpt': string(50000, 0), 'error': string(2000, 0)}, ['context_id', 'job_id', 'source_id', 'status']),
    'course_start': ({'request_id': ID, 'title': string(300), 'interest': string(12000), 'intent': enum('topic', 'project', 'sources'), 'level': enum('beginner', 'intermediate', 'advanced'), 'materials': array(MATERIAL, 20)}, ['request_id', 'title', 'intent', 'level', 'materials']),
    'course_open': ({'track_id': ID}, ['track_id']),
    'course_read': ({'track_id': ID}, ['track_id']),
    'course_generate': ({**CONTEXT, 'request_id': ID, 'lesson_key': string(80)}, ['context_id', 'request_id']),
    'course_bind': ({**CONTEXT, 'session_id': string(200), 'scope': string(2000)}, ['context_id', 'session_id', 'scope']),
    'course_position': ({**CONTEXT, 'lesson_key': string(80), 'completed': array(string(80), 50)}, ['context_id', 'lesson_key']),
    'course_plan': ({**CONTEXT, 'job_id': ID, 'summary': string(12000), 'assumptions': array(string(1000), 30), 'lessons': array(LESSON_OUTLINE, 50)}, ['context_id', 'job_id', 'summary', 'assumptions', 'lessons']),
    'course_lesson': ({**CONTEXT, 'job_id': ID, 'lesson_key': string(80), 'content': string(50000), 'source_ids': array(ID, 30), 'visual': VISUAL}, ['context_id', 'job_id', 'lesson_key', 'content', 'source_ids']),
    'course_job_status': ({**CONTEXT, 'job_id': ID, 'status': enum('stopped', 'failed'), 'error': string(2000, 0)}, ['context_id', 'job_id', 'status']),
})


def parameters(name):
    properties, required = SPECS[name]
    return {'type': 'object', 'properties': properties, 'required': required, 'additionalProperties': False}


def _validate(value, schema, label='params'):
    if 'anyOf' in schema:
        for variant in schema['anyOf']:
            try:
                _validate(value, variant, label)
                return
            except LearningError:
                pass
        raise LearningError(f'{label} does not match a supported shape')
    kind = schema['type']
    valid = {'object': type(value) is dict, 'string': type(value) is str,
             'array': type(value) is list, 'integer': type(value) is int, 'null': value is None}[kind]
    if not valid:
        raise LearningError(f'{label} must be {kind}')
    if kind == 'object' and 'properties' in schema:
        if set(value) - set(schema['properties']):
            raise LearningError(f'{label} contains unsupported fields')
        if set(schema['required']) - set(value):
            raise LearningError(f'{label} is missing required fields')
        for key, item in value.items():
            _validate(item, schema['properties'][key], f'{label}.{key}')
    if kind == 'string' and not schema.get('minLength', 0) <= len(value) <= schema.get('maxLength', 100000):
        raise LearningError(f'{label} length is outside supported limits')
    if kind == 'array':
        if len(value) > schema['maxItems']:
            raise LearningError(f'{label} contains too many items')
        for item in value:
            _validate(item, schema['items'], label)
    if kind == 'integer' and (value < schema.get('minimum', 0) or value > schema.get('maximum', 2**53)):
        raise LearningError(f'{label} is outside supported limits')
    if 'enum' in schema and value not in schema['enum']:
        raise LearningError(f'{label} has an unsupported value')


def store():
    from plugins.plugin_storage import plugin_data_dir
    return Store(plugin_data_dir('hermes-learning') / 'data.db')


def action(name, params, *, channel='ui_direct', api_version=1):
    if type(api_version) is not int or api_version != 1:
        raise LearningError('Unsupported learning API version; reload compatible clients')
    if channel not in ('ui_direct', 'chat_relayed'):
        raise LearningError('Unsupported adapter channel')
    if not isinstance(name, str) or name not in SPECS:
        raise LearningError('Unknown learning action')
    if channel == 'chat_relayed' and name in ('course_start', 'course_open', 'course_generate', 'course_bind', 'course_position', 'course_job_status', 'start', 'resume', 'approve', 'recommendation_decide', 'track_status', 'review', 'export'):
        raise LearningError('This action requires the human workspace or explicit slash command')
    _validate(params, parameters(name))
    try:
        size = len(json.dumps(params, allow_nan=False, ensure_ascii=False).encode('utf-8'))
    except (TypeError, ValueError, RecursionError) as exc:
        raise LearningError('Parameters must be finite JSON values') from exc
    if size > 256000:
        raise LearningError('Learning request exceeds 256000 bytes')
    return store().dispatch(name, params, channel=channel)

"""Transactional, model-aware learning records. No model calls or content execution.

Schema 1 stores typed JSON records in SQLite. Every mutation holds BEGIN
IMMEDIATE, validates the context and references before writing, then commits.
Activity records and evidence are append-only; mutable proposals/reviews are
revision guarded or derived in the same transaction. Review policy v1 uses
1/3/7 days; these are explicit product heuristics, not mastery estimates.
"""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import uuid
from urllib.parse import urlsplit

API_VERSION = SCHEMA_VERSION = 1
LEVELS = ['none', 'nudge', 'targeted-hint', 'worked-step', 'full-solution-shown']
OUTCOMES = ['needs-work', 'developing', 'demonstrated']
CAPABILITIES = ['integrated-courses-v1', 'objective-evidence-v1', 'generated-help-v1', 'structured-visuals-v1']
WITHHELD = 'Content withheld by source-sharing policy.'
READS = {'course_read', 'state', 'track', 'source_read', 'activity_read', 'resume_brief', 'export', 'quote_check'}
WRITES = {'course_source', 'course_start', 'course_open', 'course_generate', 'course_bind', 'course_position', 'course_plan', 'course_lesson', 'course_job_status', 'start', 'resume', 'leave', 'brief', 'approve', 'track_status', 'source', 'activity', 'run', 'help', 'submit', 'assess', 'dispute', 'review', 'recommendation', 'recommendation_decide', 'activity_revision'}
KINDS = ('track', 'source', 'activity', 'attempt', 'assessment', 'review', 'dispute', 'help', 'run', 'context', 'recommendation')


class LearningError(Exception):
    def __init__(self, message, code='invalid_request', status=400):
        super().__init__(message)
        self.code = code
        self.status = self.status_code = status


def fail(message, code='invalid_request', status=400):
    raise LearningError(message, code, status)


def text(value, name, limit=12000, required=False):
    if not isinstance(value, str) or len(value) > limit or '\x00' in value or (required and not value.strip()):
        fail(f'{name} must be {"nonempty " if required else ""}text of at most {limit} characters')
    return value


def strings(value, name, limit=30, width=1000):
    if not isinstance(value, list) or len(value) > limit:
        fail(f'{name} must be a list of at most {limit} strings')
    return [text(v, name, width, True) for v in value]


def safe_url(value):
    value = text(value, 'url', 2000)
    if value:
        try:
            parsed = urlsplit(value)
            valid = parsed.scheme in ('https', 'http') and parsed.hostname and not parsed.username and not parsed.password and not any(c.isspace() for c in value)
        except ValueError:
            valid = False
        if not valid:
            fail('Source URL must be a credential-free HTTP(S) URL')
    return value


def iso(value):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            fail('Expected an ISO 8601 date with timezone')
    if not isinstance(value, datetime) or value.tzinfo is None:
        fail('Expected an ISO 8601 date with timezone')
    return value.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


class Store:
    def __init__(self, path, clock=None):
        self.path = Path(path).expanduser().resolve()
        if str(path) == ':memory:' or not self.path.parent.is_dir() or self.path.is_dir():
            fail('Store must be a file in an existing data directory', 'invalid_path')
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        with self._connection() as db:
            # Simultaneous first connections can fail this journal transition
            # immediately without invoking SQLite's busy timeout. Retry only
            # lock contention, before any transaction or records are created.
            deadline = time.monotonic() + 15
            while True:
                try:
                    db.execute('PRAGMA journal_mode=WAL')
                    break
                except sqlite3.OperationalError as exc:
                    if str(exc) != 'database is locked' or time.monotonic() >= deadline:
                        raise
                    time.sleep(0.025)
            db.execute('BEGIN IMMEDIATE')
            try:
                version = db.execute('PRAGMA user_version').fetchone()[0]
                if version not in (0, SCHEMA_VERSION):
                    fail('Unsupported learning schema', 'incompatible_schema', 409)
                if version == 0:
                    if db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone():
                        fail('Refusing to initialize an unrelated database', 'incompatible_schema', 409)
                    db.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
                    db.execute('CREATE TABLE records (seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL UNIQUE, kind TEXT NOT NULL, track_id TEXT, data TEXT NOT NULL)')
                    db.execute('CREATE INDEX records_track_kind ON records(track_id,kind)')
                    db.execute('INSERT INTO metadata VALUES (?,?)', ('store_id', str(uuid.uuid4())))
                    db.execute(f'PRAGMA user_version={SCHEMA_VERSION}')
                self.store_id = db.execute("SELECT value FROM metadata WHERE key='store_id'").fetchone()[0]
                db.commit()
            except BaseException:
                db.rollback()
                raise

    @contextmanager
    def _connection(self):
        db = sqlite3.connect(str(self.path), timeout=15, isolation_level=None)
        try:
            db.execute('PRAGMA busy_timeout=15000')
            db.execute('PRAGMA foreign_keys=ON')
            yield db
        finally:
            db.close()

    def _all(self, db, kind, track_id=None):
        if track_id is None:
            rows = db.execute('SELECT data FROM records WHERE kind=? ORDER BY seq', (kind,))
        else:
            rows = db.execute('SELECT data FROM records WHERE kind=? AND track_id=? ORDER BY seq', (kind, track_id))
        return [json.loads(row[0]) for row in rows]

    def _get(self, db, kind, ident, track_id=None):
        text(ident, f'{kind}_id', 100, True)
        row = db.execute('SELECT data FROM records WHERE id=? AND kind=?', (ident, kind)).fetchone()
        if not row:
            fail(f'{kind} not found', 'not_found', 404)
        record = json.loads(row[0])
        if track_id is not None and record.get('track_id', record['id']) != track_id:
            fail('Record belongs to another track', 'context_mismatch', 403)
        return record

    def _put(self, db, kind, record, update=False):
        data = json.dumps(record, ensure_ascii=False, separators=(',', ':'))
        if update:
            db.execute('UPDATE records SET data=? WHERE id=? AND kind=?', (data, record['id'], kind))
        else:
            db.execute('INSERT INTO records(id,kind,track_id,data) VALUES (?,?,?,?)', (record['id'], kind, record.get('track_id', record['id'] if kind == 'track' else None), data))
        return record

    def _new(self, **values):
        return {'id': str(uuid.uuid4()), **values}

    def _context(self, db, ident):
        context = self._get(db, 'context', ident)
        if not context['active']:
            fail('Tracking context has ended. Explicitly resume to continue.', 'context_revoked', 403)
        track = self._get(db, 'track', context['track_id'])
        if track['status'] in ('paused', 'archived'):
            fail('Track must be explicitly resumed', 'context_revoked', 403)
        return context, track

    def _protected(self, db, activity, channel):
        return channel == 'chat_relayed' and any(self._get(db, 'source', s)['sharing'] == 'metadata-only' for s in activity['source_ids'])

    def _track_view(self, track):
        # Derivation works for old schema-1 records without migrating on reads.
        details = []
        seen = set()
        for title in track['objectives']:
            ident = str(uuid.uuid5(uuid.NAMESPACE_URL, json.dumps([track['id'], title], ensure_ascii=False)))
            if ident not in seen:
                details.append({'id': ident, 'title': title})
                seen.add(ident)
        return {**track, 'objective_details': details, 'learner_profile': track.get('learner_profile', {})}

    def _profile(self, value, previous=None):
        if not isinstance(value, dict) or set(value) - {'background', 'goal', 'minutes'}:
            fail('learner_profile accepts only background, goal and minutes')
        profile = dict(previous or {})
        for field in ('background', 'goal'):
            if field in value:
                profile[field] = text(value[field], field, 2000)
        if 'minutes' in value:
            if type(value['minutes']) is not int or not 1 <= value['minutes'] <= 240:
                fail('Session minutes must be an integer from 1 to 240')
            profile['minutes'] = value['minutes']
        return profile

    def _lineage_ids(self, db, activity):
        root = activity.get('root_activity_id', activity['id'])
        return {a['id'] for a in self._all(db, 'activity', activity['track_id']) if a.get('root_activity_id', a['id']) == root}

    def _safe_help(self, db, event, channel, restricted=False):
        result = dict(event)
        if restricted or self._protected(db, self._get(db, 'activity', event['activity_id']), channel):
            result.pop('content', None)
            result['content_withheld'] = True
        return result

    def _safe_evidence(self, db, record, kind, channel):
        result = dict(record)
        attempt = record if kind == 'attempt' else self._get(db, 'attempt', record['attempt_id'])
        restricted = self._protected(db, self._get(db, 'activity', attempt['activity_id']), channel)
        if kind == 'attempt':
            result['assistance_events'] = [self._safe_help(db, e, channel, restricted) for e in record.get('assistance_events', [])]
        if restricted:
            for key in ('answer', 'feedback', 'reason', 'uncertainty'):
                if key in result:
                    result[key] = WITHHELD
            if 'criterion_results' in result:
                result['criterion_results'] = [{**item, 'feedback': WITHHELD} for item in result['criterion_results']]
            result['content_withheld'] = True
        return result

    def _safe_activity(self, db, activity, channel, unlocked=False):
        result = {k: activity[k] for k in ('id', 'track_id', 'title', 'kind', 'prompt', 'description', 'source_ids', 'version', 'author_kind', 'created_at')}
        result.update(previous_version_id=activity.get('previous_version_id'), root_activity_id=activity.get('root_activity_id', activity['id']))
        result.update(objective_ids=activity.get('objective_ids', []), objective_snapshots=activity.get('objective_snapshots', []), competency=activity.get('competency', 'conceptual'), purpose=activity.get('purpose', 'practice'))
        visual = activity['visual']
        if visual:
            count = len(visual['steps']) if unlocked else visual['visible_steps']
            result['visual'] = {**visual, 'steps': visual['steps'][:count], 'total_steps': len(visual['steps']), 'visible_steps': count}
        else:
            result['visual'] = None
        if unlocked:
            result.update(criteria=activity['criteria'], solution=activity['solution'])
        if self._protected(db, activity, channel):
            result.update(title='Activity with restricted source', prompt='Content withheld by source-sharing policy.', description='', visual=None, content_withheld=True)
            result.pop('criteria', None)
            result.pop('solution', None)
        return result

    def _safe_source(self, source, channel, content=False):
        result = dict(source)
        result.pop('excerpt', None)
        if content and (channel == 'ui_direct' or source['sharing'] != 'metadata-only'):
            result['excerpt'] = source['excerpt']
        result['content_withheld'] = content and channel == 'chat_relayed' and source['sharing'] == 'metadata-only'
        return result

    def _snapshot(self, db, channel, track_id=None):
        result = {}
        for kind in ('track', 'source', 'activity', 'attempt', 'assessment', 'review', 'dispute', 'recommendation'):
            rows = self._all(db, kind, track_id)
            if kind == 'source':
                rows = [self._safe_source(r, channel) for r in rows]
            elif kind == 'track':
                rows = [self._track_view(r) for r in rows]
            elif kind == 'activity':
                rows = [self._safe_activity(db, r, channel) for r in rows]
            elif kind in ('attempt', 'assessment', 'dispute'):
                rows = [self._safe_evidence(db, r, kind, channel) for r in rows]
            result[{'activity': 'activities'}.get(kind, kind + 's')] = rows
        self._project_learning(result)
        return result

    def _summarize_attempts(self, attempts, assessments, disputed):
        ids = {a['id'] for a in attempts}
        judgments = [a for a in assessments if a['attempt_id'] in ids]
        assessed = {a['attempt_id'] for a in judgments}
        latest = [a for a in judgments if attempts and a['attempt_id'] == attempts[-1]['id']]
        if any(a['id'] in disputed for a in judgments):
            status = 'disputed'
        elif ids - assessed:
            status = 'awaiting-assessment'
        elif latest:
            status = min((a['outcome'] for a in latest), key=OUTCOMES.index)
        else:
            status = 'not-started'
        return {'status': status, 'attempt_count': len(attempts), 'assessment_count': len(judgments)}, judgments, latest

    def _objective_evidence(self, objective_id, activities, attempts, assessments, disputed):
        linked = [a for a in attempts if objective_id in activities[a['activity_id']].get('objective_ids', [])]
        summary, judgments, _ = self._summarize_attempts(linked, assessments, disputed)
        dimensions = {}
        basis_ids = set()
        for dimension in ('conceptual', 'practical'):
            subset = [a for a in linked if activities[a['activity_id']].get('competency', 'conceptual') in (dimension, 'both')]
            dimensions[dimension], _, latest = self._summarize_attempts(subset, assessments, disputed)
            basis_ids.update(a['id'] for a in latest)
        if summary['status'] in OUTCOMES:
            summary['status'] = min((d['status'] for d in dimensions.values() if d['status'] in OUTCOMES), key=OUTCOMES.index)
        return summary, judgments, dimensions, [a for a in judgments if a['id'] in basis_ids]

    def _objective_review(self, db, review, now):
        """Update a policy-2 schedule from the same evidence used by progress.

        assessment_id/activity_id remain the triggering event; basis IDs explain
        the schedule, which may be governed by weaker evidence from another task.
        """
        tid = review['track_id']
        activities = {a['id']: a for a in self._all(db, 'activity', tid)}
        attempts = self._all(db, 'attempt', tid)
        assessments = self._all(db, 'assessment', tid)
        superseded = {a['supersedes'] for a in assessments if a.get('supersedes')}
        effective = [a for a in assessments if a['id'] not in superseded]
        disputed = {d['assessment_id'] for d in self._all(db, 'dispute', tid)} - superseded
        summary, judgments, _, basis = self._objective_evidence(review['objective_id'], activities, attempts, effective, disputed)
        linked_ids = {a['id'] for a in attempts if review['objective_id'] in activities[a['activity_id']].get('objective_ids', [])}
        pending = bool(linked_ids - {a['attempt_id'] for a in judgments})
        has_dispute = any(a['id'] in disputed for a in judgments)
        weakest = min((a['outcome'] for a in basis), key=OUTCOMES.index) if basis else None
        driving = [a for a in basis if a['outcome'] == weakest]
        review.update(basis_status=summary['status'], basis_assessment_ids=[a['id'] for a in driving], pending_assessment=pending, disputed=has_dispute)
        if has_dispute or pending:
            detail = 'Unresolved disputed feedback' if has_dispute else 'Answers awaiting assessment'
            reason = f'Policy v2: {detail}; resolve the evidence before relying on the retained review date.'
            review.setdefault('due_at', now)
        elif driving:
            days = {'needs-work': 1, 'developing': 3, 'demonstrated': 7}[weakest]
            anchor = min(a['created_at'] for a in driving)
            methods = '/'.join(sorted({a['method'] for a in driving}))
            due = iso(datetime.fromisoformat(anchor.replace('Z', '+00:00')) + timedelta(days=days))
            reason = f'Policy v2: objective {weakest}; the weakest current evidence across competencies ({methods} feedback) sets a {days}-day interval from {anchor}. Fixed heuristic, not a mastery estimate.'
            if not review.get('manual'):
                review['due_at'] = due
        else:
            reason = 'Policy v2: no assessed objective evidence; choose an activity and review its answer.'
            review.setdefault('due_at', now)
        if review.get('manual'):
            reason = 'Learner-set review date retained until feedback on a new attempted task. ' + reason
        review.update(reason=reason, updated_at=now)
        return review

    def _project_learning(self, snapshot):
        """Read-only projections. Counts describe evidence, never mastery."""
        activities = {a['id']: a for a in snapshot['activities']}
        retired = {a['previous_version_id'] for a in activities.values() if a.get('previous_version_id')}
        superseded = {a['supersedes'] for a in snapshot['assessments'] if a.get('supersedes')}
        assessments = [a for a in snapshot['assessments'] if a['id'] not in superseded]
        disputed = {d['assessment_id'] for d in snapshot['disputes']} - superseded
        attempted = {a['activity_id'] for a in snapshot['attempts']}
        assessed = {a['attempt_id'] for a in assessments}
        now = iso(self.clock())

        progress = []
        actions = []
        for review in snapshot['reviews']:
            objective = review.get('objective_id')
            options = [a for a in activities.values() if objective and a['track_id'] == review['track_id'] and objective in a['objective_ids'] and a['id'] not in attempted and a['id'] not in retired]
            fallback = [a for a in activities.values() if a['root_activity_id'] == activities[review['activity_id']]['root_activity_id'] and a['id'] not in retired and (not objective or objective in a['objective_ids'])]
            review['suggested_activity_id'] = options[0]['id'] if options else (fallback[-1]['id'] if fallback else None)

        for track in snapshot['tracks']:
            tid = track['id']
            track_attempts = [a for a in snapshot['attempts'] if a['track_id'] == tid]
            for objective in track['objective_details']:
                summary, judgments, dimensions, _ = self._objective_evidence(objective['id'], activities, track_attempts, assessments, disputed)
                linked = [a for a in track_attempts if objective['id'] in activities[a['activity_id']]['objective_ids']]
                progress.append({'track_id': tid, 'objective_id': objective['id'], 'title': objective['title'], **summary, 'status_basis': 'Latest attempted task per competency; the weaker judgment applies when feedback differs. Pending answers and unresolved disputes take precedence. Latest feedback may concern an earlier task.', 'assisted_attempt_count': sum(a.get('assistance', 'unknown') not in ('none', 'unknown') for a in linked), 'latest_assessment': judgments[-1] if judgments else None, **dimensions})

            def action(kind, title, reason, **context):
                return {'track_id': tid, 'kind': kind, 'title': title, 'reason': reason, **context}

            pending = [a for a in track_attempts if a['id'] not in assessed]
            disputes = [a for a in assessments if a['track_id'] == tid and a['id'] in disputed]
            reviews = sorted((r for r in snapshot['reviews'] if r['track_id'] == tid and r['due_at'] <= now), key=lambda r: r['due_at'])
            fresh = [a for a in activities.values() if a['track_id'] == tid and a['id'] not in attempted and a['id'] not in retired]
            if track['status'] in ('paused', 'archived'):
                chosen = action('resume', 'Resume this track', 'Explicitly resume tracking before continuing.')
            elif track['status'] in ('exploring', 'proposed'):
                chosen = action('proposal', 'Set your learning direction', 'Review and approve a concrete learning brief before continuing.')
            elif disputes:
                evidence = disputes[-1]
                chosen = action('dispute', 'Resolve disputed feedback', 'Review the saved answer and criteria, then append a correction if needed.', activity_id=evidence['activity_id'], attempt_id=evidence['attempt_id'])
            elif pending:
                chosen = action('assessment', 'Review your answer', 'This saved answer is waiting for feedback against its criteria.', activity_id=pending[0]['activity_id'], attempt_id=pending[0]['id'])
            elif reviews:
                review = reviews[0]
                if review.get('objective_id') and not review['suggested_activity_id']:
                    chosen = action('author', 'Create an objective review activity', 'This objective is due for review, but no current activity covers it. Create a different example.', objective_id=review['objective_id'])
                else:
                    chosen = action('review', 'Revisit this objective' if review.get('objective_id') else 'Revisit this activity', review['reason'], activity_id=review['suggested_activity_id'] or review['activity_id'])
                    if review.get('objective_id'):
                        chosen['objective_id'] = review['objective_id']
            elif fresh:
                chosen = action('practice', 'Try the next activity', 'This activity version has no saved answer yet.', activity_id=fresh[0]['id'])
                if fresh[0]['objective_ids']:
                    chosen['objective_id'] = fresh[0]['objective_ids'][0]
            else:
                rows = [row for row in progress if row['track_id'] == tid]
                priority = {'not-started':0, 'needs-work':1, 'developing':2, 'demonstrated':3, 'awaiting-assessment':0, 'disputed':0}
                target = min(rows, key=lambda row: priority[row['status']]) if rows else None
                chosen = action('author', 'Create a transfer activity' if track_attempts else 'Create a first activity', 'Use a different example to test this objective.' if track_attempts else 'Start with a short diagnostic tied to your learning objectives.')
                if target:
                    chosen['objective_id'] = target['objective_id']
            actions.append(chosen)
        snapshot['objective_progress'] = progress
        snapshot['next_actions'] = actions

    def _visual(self, visual):
        if visual is None:
            return None
        types = ('sequence', 'state-machine', 'code-trace')
        if not isinstance(visual, dict) or visual.get('type') not in types or type(visual.get('schema_version', 1)) is not int or visual.get('schema_version', 1) != 1:
            fail('Only schema 1 sequence, state-machine and code-trace visuals are supported')
        kind = visual['type']
        allowed = {'type', 'schema_version', 'title', 'steps', 'visible_steps'}
        allowed.update({'sequence': {'participants'}, 'state-machine': {'states', 'initial'}, 'code-trace': {'code', 'language'}}[kind])
        if set(visual) - allowed:
            fail('Unsupported visual fields')
        steps = visual.get('steps')
        if not isinstance(steps, list) or not 1 <= len(steps) <= 30:
            fail('A visual requires 1–30 steps')
        result = {'schema_version': 1, 'type': kind, 'title': text(visual.get('title', ''), 'visual title', 300)}
        ids = set()
        if kind in ('sequence', 'state-machine'):
            field = 'participants' if kind == 'sequence' else 'states'
            nodes = visual.get(field)
            maximum = 10 if kind == 'sequence' else 20
            if not isinstance(nodes, list) or not 1 <= len(nodes) <= maximum:
                fail(f'{field} requires 1–{maximum} entries')
            cleaned = []
            for node in nodes:
                if not isinstance(node, dict) or set(node) != {'id', 'label'}:
                    fail('Each visual node requires only id and label')
                ident = text(node['id'], 'visual node id', 60, True)
                if ident in ids:
                    fail('Duplicate visual node id')
                ids.add(ident)
                cleaned.append({'id': ident, 'label': text(node['label'], 'visual node label', 150, True)})
            result[field] = cleaned
            if kind == 'state-machine':
                initial = text(visual.get('initial'), 'initial state', 60, True)
                if initial not in ids:
                    fail('Initial state must exist')
                result['initial'] = initial
                previous = initial
        else:
            result.update(code=text(visual.get('code'), 'code', 12000, True), language=text(visual.get('language', ''), 'language', 40))
            line_count = len(result['code'].split('\n'))
        clean_steps = []
        for step in steps:
            fields = {'label', 'explanation'} | ({'line', 'variables'} if kind == 'code-trace' else {'from', 'to'})
            if not isinstance(step, dict) or set(step) - fields:
                fail('Unsupported visual step')
            clean = {'label': text(step.get('label', ''), 'step label', 300, True), 'explanation': text(step.get('explanation', ''), 'step explanation', 2000)}
            if kind == 'code-trace':
                line = step.get('line')
                if type(line) is not int or not 1 <= line <= line_count:
                    fail('Code trace line must reference a line of code')
                variables = step.get('variables', [])
                if not isinstance(variables, list) or len(variables) > 20:
                    fail('A trace step supports at most 20 variables')
                clean_variables = []
                names = set()
                for variable in variables:
                    if not isinstance(variable, dict) or set(variable) != {'name', 'value'}:
                        fail('Trace variables require only name and value')
                    name = text(variable['name'], 'variable name', 150, True)
                    if name in names:
                        fail('Duplicate variable in trace step')
                    names.add(name)
                    clean_variables.append({'name': name, 'value': text(variable['value'], 'variable value', 2000)})
                clean.update(line=line, variables=clean_variables)
            else:
                if not isinstance(step.get('from'), str) or not isinstance(step.get('to'), str) or step['from'] not in ids or step['to'] not in ids:
                    fail('Step references must exist')
                if kind == 'state-machine':
                    if step['from'] != previous:
                        fail('State-machine steps must follow the previous state')
                    previous = step['to']
                clean.update({'from': step['from'], 'to': step['to']})
            clean_steps.append(clean)
        visible = visual.get('visible_steps', 1)
        if type(visible) is not int or not 0 <= visible <= len(steps):
            fail('visible_steps is outside the visual')
        return {**result, 'steps': clean_steps, 'visible_steps': visible}

    def _lesson_visual(self, visual):
        visual = self._visual(visual)
        # Lesson walkthroughs are fully published explanations. The same schema
        # uses visible_steps to withhold answers only in assessed activities.
        return {**visual, 'visible_steps': len(visual['steps'])} if visual else None

    def _lesson_view(self, lesson):
        return {**lesson, 'visual': self._lesson_visual(lesson.get('visual'))}

    def _course_job_view(self, job):
        return {key: value for key, value in job.items() if key not in ('context_id', 'request_hash')}

    def _course_data(self, db, tid):
        records = self._all(db, 'course', tid)
        return records[0] if records else None

    def _course_dispatch(self, db, action, p, channel):
        now = iso(self.clock())
        ui_actions = {'course_start', 'course_open', 'course_generate', 'course_bind', 'course_position', 'course_job_status'}
        if action in ui_actions and channel != 'ui_direct':
            fail('This course action requires the human workspace', 'explicit_entry_required', 403)
        if action == 'course_read':
            track = self._get(db, 'track', p.get('track_id'))
            tid = track['id']
            course = self._course_data(db, tid) or {}
            lessons = [self._lesson_view(lesson) for lesson in self._all(db, 'lesson', tid)]
            for lesson in lessons:
                if channel == 'chat_relayed' and any(self._get(db, 'source', sid, tid)['sharing'] == 'metadata-only' for sid in lesson['source_ids']):
                    lesson.update(content=WITHHELD, title='Lesson with restricted source', visual=None, content_withheld=True)
            return {'track': self._track_view(track), 'outline': course.get('outline', []),
                    'lessons': lessons, 'position': course.get('position', {'lesson_key': None, 'completed': []}),
                    'binding': course.get('binding') if channel == 'ui_direct' else None,
                    'jobs': [self._course_job_view(job) for job in self._all(db, 'course_job', tid)],
                    'sources': [{**self._safe_source(source, channel, content=True),
                                 'read_status': source.get('read_status', 'provided' if source['excerpt'] else 'unread')}
                                for source in self._all(db, 'source', tid)]}
        if action == 'course_start':
            request_id = text(p.get('request_id'), 'request_id', 100, True)
            title = text(p.get('title'), 'title', 300, True)
            interest = text(p.get('interest', title), 'interest', 12000, True)
            intent, level = p.get('intent'), p.get('level')
            if intent not in ('topic', 'project', 'sources') or level not in ('beginner', 'intermediate', 'advanced'):
                fail('Unsupported course intent or level')
            materials = p.get('materials', [])
            if not isinstance(materials, list) or len(materials) > 20:
                fail('Provide at most 20 source materials')
            size = 0
            byte_size = 0
            for material in materials:
                if not isinstance(material, dict) or set(material) - {'title', 'kind', 'url', 'locator', 'excerpt', 'sharing'}:
                    fail('Unsupported material fields')
                excerpt = text(material.get('excerpt', ''), 'excerpt', 50000)
                size += len(excerpt)
                byte_size += len(excerpt.encode('utf-8'))
            if size > 100000 or byte_size > 200000:
                fail('Materials exceed 100000 characters or 200000 UTF-8 bytes', 'too_large', 413)
            payload = {'title': title, 'interest': interest, 'intent': intent, 'level': level, 'materials': materials}
            digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            existing = next((r for r in self._all(db, 'course_request') if r['request_id'] == request_id), None)
            if existing:
                if existing['request_hash'] != digest:
                    fail('Request ID already used with different input', 'idempotency_conflict', 409)
                self._context(db, existing['context_id'])
                return {key: existing[key] for key in ('track_id', 'context_id', 'job_id')}
            started = self._dispatch(db, 'start', {'title': title, 'interest': interest}, channel)
            tid, context_id = started['track_id'], started['context_id']
            track = self._get(db, 'track', tid)
            track.update(status='active', intent=intent, level=level)
            self._put(db, 'track', track, True)
            self._put(db, 'course', self._new(track_id=tid, outline=[], summary='', assumptions=[], binding=None,
                                             position={'lesson_key': None, 'completed': []}, created_at=now))
            for material in materials:
                self._dispatch(db, 'source', {**material, 'context_id': context_id}, channel)
            job = self._course_new_job(db, track, context_id, request_id, None, now)
            self._put(db, 'course_request', self._new(**started, job_id=job['id'], request_id=request_id, request_hash=digest))
            return {**started, 'job_id': job['id']}
        if action == 'course_open':
            track = self._get(db, 'track', p.get('track_id'))
            recoverable = []
            for job in self._all(db, 'course_job', track['id']):
                if job['status'] not in ('queued', 'generating'):
                    continue
                context = self._get(db, 'context', job['context_id'], track['id'])
                if context['active'] and track['status'] not in ('paused', 'archived'):
                    recoverable.append(job)
                else:
                    job.update(status='stopped', error='Generation context ended; explicitly generate again', updated_at=now)
                    self._put(db, 'course_job', job, True)
            if recoverable:
                # Explicit Continue recovers the latest unfinished request's
                # authority, including Stop, without starting another model turn.
                job = recoverable[-1]
                return {'track_id': track['id'], 'context_id': job['context_id'],
                        'job_id': job['id'], 'lesson_key': job['lesson_key']}
            return self._dispatch(db, 'resume', p, channel)
        context, track = self._context(db, p.get('context_id'))
        tid = track['id']
        course = self._course_data(db, tid)
        if course is None:
            course = self._new(track_id=tid, outline=[], summary='', assumptions=[], binding=None,
                               position={'lesson_key': None, 'completed': []}, created_at=now)
            self._put(db, 'course', course)
        if action == 'course_generate':
            request_id = text(p.get('request_id'), 'request_id', 100, True)
            lesson_key = p.get('lesson_key')
            if lesson_key is not None:
                text(lesson_key, 'lesson_key', 80, True)
                if lesson_key not in {item['key'] for item in course['outline']}:
                    fail('Lesson must belong to the saved outline')
            existing = next((job for job in self._all(db, 'course_job', tid) if job['request_id'] == request_id), None)
            if existing:
                if existing['context_id'] != context['id'] or existing['requested_lesson_key'] != lesson_key:
                    fail('Request ID already used with different context or lesson', 'idempotency_conflict', 409)
                return {'job_id': existing['id']}
            target = lesson_key or (course['outline'][0]['key'] if course['outline'] else None)
            if target and any(lesson['key'] == target for lesson in self._all(db, 'lesson', tid)):
                fail('Lesson is already published', 'revision_conflict', 409)
            # A new explicit request supersedes unfinished work for this same target.
            for job in self._all(db, 'course_job', tid):
                if job['status'] in ('queued', 'generating') and job['lesson_key'] == target:
                    job.update(status='stopped', error='Superseded by a new generation request', updated_at=now)
                    self._put(db, 'course_job', job, True)
            job = self._course_new_job(db, track, context['id'], request_id, lesson_key, now)
            return {'job_id': job['id']}
        if action == 'course_bind':
            binding = {'session_id': text(p.get('session_id'), 'session_id', 200, True),
                       'scope': text(p.get('scope'), 'scope', 2000, True)}
            course['binding'] = binding
            self._put(db, 'course', course, True)
            return binding
        if action == 'course_position':
            keys = {lesson['key'] for lesson in self._all(db, 'lesson', tid)}
            key = text(p.get('lesson_key'), 'lesson_key', 80, True)
            completed = strings(p.get('completed', course['position']['completed']), 'completed', 50, 80)
            if key not in keys or len(set(completed)) != len(completed) or set(completed) - keys:
                fail('Reading position and completion must refer to published lessons')
            course['position'] = {'lesson_key': key, 'completed': completed}
            self._put(db, 'course', course, True)
            return course['position']
        job = self._get(db, 'course_job', p.get('job_id'), tid)
        if job['context_id'] != context['id']:
            fail('Generation job belongs to another context', 'context_mismatch', 403)
        if action == 'course_source':
            if job['status'] not in ('queued', 'generating'):
                fail('Generation job has ended', 'job_closed', 409)
            source = self._get(db, 'source', p.get('source_id'), tid)
            if source['sharing'] == 'metadata-only':
                fail('Metadata-only sources do not authorize retrieval', 'source_restricted', 403)
            if not source['url'] or (source['excerpt'] and not source.get('retrieval_job_id')):
                fail('Only an explicitly supplied unread URL supports retrieval results')
            status = p.get('status')
            if status not in ('read', 'failed', 'unsupported'):
                fail('Unsupported source retrieval status')
            excerpt = text(p.get('excerpt', ''), 'retrieved excerpt', 50000, status == 'read')
            error = text(p.get('error', ''), 'retrieval error', 2000, status != 'read')
            if status != 'read' and excerpt:
                fail('Failed or unsupported retrieval must not include source text')
            if status == 'read' and error:
                fail('Successful retrieval must not include an error')
            if source.get('read_status') == 'read':
                if status != 'read' or excerpt != source['excerpt']:
                    fail('Retrieved source content is immutable', 'revision_conflict', 409)
                return {'source': self._safe_source(source, channel, content=True)}
            others = [item['excerpt'] for item in self._all(db, 'source', tid) if item['id'] != source['id']]
            if sum(map(len, others)) + len(excerpt) > 100000 or sum(len(item.encode('utf-8')) for item in others) + len(excerpt.encode('utf-8')) > 200000:
                fail('Retrieved material exceeds course source limits', 'too_large', 413)
            source.update(read_status=status, retrieval_error=error, excerpt=excerpt,
                          excerpt_hash=hashlib.sha256(excerpt.encode()).hexdigest(), retrieval_job_id=job['id'],
                          verification='agent-reported retrieval; not independently verified' if status == 'read' else 'unverified',
                          updated_at=now)
            self._put(db, 'source', source, True)
            return {'source': self._safe_source(source, channel, content=True)}
        if action == 'course_job_status':
            status = p.get('status')
            if status not in ('stopped', 'failed'):
                fail('Only stopped or failed may be set explicitly')
            if job['status'] == 'completed':
                return self._course_job_view(job)
            job.update(status=status, error=text(p.get('error', ''), 'error', 2000), updated_at=now)
            self._put(db, 'course_job', job, True)
            return self._course_job_view(job)
        if action == 'course_plan':
            if not job['allow_outline']:
                fail('This generation request does not authorize a new outline', 'job_scope', 403)
            lessons = p.get('lessons')
            if not isinstance(lessons, list) or not 1 <= len(lessons) <= 50:
                fail('An outline requires 1–50 lessons')
            cleaned = []
            seen = set()
            for item in lessons:
                if not isinstance(item, dict) or set(item) != {'key', 'title', 'goal'}:
                    fail('Outline entries require key, title and goal')
                key = text(item['key'], 'lesson key', 80, True)
                if not all(c.isascii() and (c.isalnum() or c in '_-') for c in key) or key in seen:
                    fail('Lesson keys must be unique ASCII letters, numbers, underscores or hyphens')
                seen.add(key)
                cleaned.append({'key': key, 'title': text(item['title'], 'lesson title', 300, True),
                                'goal': text(item['goal'], 'lesson goal', 2000, True)})
            publication = {'outline': cleaned, 'summary': text(p.get('summary'), 'summary', 12000, True),
                           'assumptions': strings(p.get('assumptions', []), 'assumptions')}
            digest = hashlib.sha256(json.dumps(publication, sort_keys=True).encode()).hexdigest()
            if job.get('plan_hash'):
                if job['plan_hash'] != digest:
                    fail('Outline already published with different content', 'revision_conflict', 409)
                return {'outline': course['outline']}
            if job['status'] not in ('queued', 'generating') or course['outline']:
                fail('Generation job no longer authorizes this outline', 'job_closed', 409)
            course.update(publication)
            self._put(db, 'course', course, True)
            job.update(plan_hash=digest, lesson_key=cleaned[0]['key'], status='generating', updated_at=now)
            self._put(db, 'course_job', job, True)
            # Legacy objective IDs derive from their titles. Replacing them
            # would orphan progress and prevent new practice using old evidence.
            # The course record already owns its generated summary and outline.
            if track.get('intent') in ('topic', 'project', 'sources'):
                track.update(brief=publication['summary'], assumptions=publication['assumptions'], objectives=[item['goal'] for item in cleaned],
                             status='active', revision=track['revision'] + 1, updated_at=now)
                self._put(db, 'track', track, True)
            return {'outline': cleaned}
        if action == 'course_lesson':
            key = text(p.get('lesson_key'), 'lesson_key', 80, True)
            item = next((item for item in course['outline'] if item['key'] == key), None)
            if item is None or key != job['lesson_key']:
                fail('Lesson is outside the authorized generation request', 'job_scope', 403)
            source_ids = strings(p.get('source_ids', []), 'source_ids', 30, 100)
            if len(set(source_ids)) != len(source_ids):
                fail('Source references must be unique')
            for sid in source_ids:
                source = self._get(db, 'source', sid, tid)
                if channel == 'chat_relayed' and source['sharing'] == 'metadata-only':
                    fail('Model cannot author from a metadata-only source', 'source_restricted', 403)
                if not source['excerpt'].strip():
                    fail('An unread reference cannot be cited as source material', 'source_unread', 409)
            content = text(p.get('content'), 'lesson content', 50000, True)
            if '\ue200cite' in content:
                fail('Use Markdown source links with the actual URL, not internal citation markers. Correct the content and retry this same job.', 'invalid_citation')
            publication = {'key': key, 'title': item['title'], 'content': content,
                           'source_ids': source_ids, 'visual': self._lesson_visual(p.get('visual'))}
            digest = hashlib.sha256(json.dumps(publication, sort_keys=True).encode()).hexdigest()
            if job.get('lesson_hash'):
                saved = self._lesson_view(self._get(db, 'lesson', job['lesson_id'], tid))
                if job['lesson_hash'] != digest:
                    # Old lessons hashed activity-style visibility. Accept only
                    # the identical normalized publication, without rewriting it.
                    if {key: saved[key] for key in publication} != publication:
                        fail('Lesson already published with different content', 'revision_conflict', 409)
                return {'lesson': saved}
            if job['status'] not in ('queued', 'generating'):
                fail('Generation job has ended; explicitly generate again', 'job_closed', 409)
            if any(lesson['key'] == key for lesson in self._all(db, 'lesson', tid)):
                fail('Lesson is already published', 'revision_conflict', 409)
            lesson = self._new(track_id=tid, **publication, version=1, job_id=job['id'], created_at=now)
            self._put(db, 'lesson', lesson)
            job.update(status='completed', lesson_hash=digest, lesson_id=lesson['id'], updated_at=now)
            self._put(db, 'course_job', job, True)
            if course['position']['lesson_key'] is None:
                course['position']['lesson_key'] = key
                self._put(db, 'course', course, True)
            return {'lesson': lesson}
        fail('Unknown course action')

    def _course_new_job(self, db, track, context_id, request_id, lesson_key, now):
        course = self._course_data(db, track['id'])
        outline = course['outline'] if course else []
        job = self._new(track_id=track['id'], context_id=context_id, request_id=request_id,
                        requested_lesson_key=lesson_key, lesson_key=lesson_key or (outline[0]['key'] if outline else None),
                        allow_outline=lesson_key is None and not outline, status='queued', error='', created_at=now, updated_at=now)
        self._put(db, 'course_job', job)
        return job

    def dispatch(self, action, params, *, channel='ui_direct'):
        if not isinstance(action, str) or action not in READS | WRITES or not isinstance(params, dict):
            fail('Unknown action or invalid parameters')
        if channel not in ('ui_direct', 'chat_relayed'):
            fail('Unsupported channel')
        try:
            encoded = json.dumps(params, allow_nan=False, ensure_ascii=False)
        except (TypeError, ValueError):
            fail('Parameters must be JSON data')
        if len(encoded) > 150000:
            fail('Request exceeds 150000 characters', 'too_large', 413)
        with self._connection() as db:
            db.execute('BEGIN IMMEDIATE' if action in WRITES else 'BEGIN')
            try:
                if db.execute('PRAGMA user_version').fetchone()[0] != SCHEMA_VERSION:
                    fail('Unsupported learning schema', 'incompatible_schema', 409)
                if db.execute("SELECT value FROM metadata WHERE key='store_id'").fetchone()[0] != self.store_id:
                    fail('Store identity changed; reconnect before continuing', 'store_changed', 409)
                result = self._dispatch(db, action, params, channel)
                db.commit()
                return result
            except BaseException:
                db.rollback()
                raise

    def _dispatch(self, db, action, p, channel):
        if action.startswith('course_'):
            return self._course_dispatch(db, action, p, channel)
        now = iso(self.clock())
        if action in ('state', 'export'):
            result = {'api_version': 1, 'schema_version': 1, 'store_id': self.store_id, 'compatible_client_versions': [1], 'capabilities': CAPABILITIES, **self._snapshot(db, channel)}
            if action == 'export':
                result.update(export_version=1, exported_at=now)
                # This export is a shareable view. Full private recovery uses backup().
                result['sources'] = [self._safe_source(s, channel, content=True) for s in self._all(db, 'source')]
            return result
        if action in ('track', 'resume_brief'):
            track = self._get(db, 'track', p.get('track_id'))
            snapshot = self._snapshot(db, channel, track['id'])
            snapshot.pop('tracks')
            result = {'track': self._track_view(track), 'capabilities': CAPABILITIES, **snapshot}
            if action == 'resume_brief':
                recommendation = snapshot['next_actions'][0]
                objective = next((o['title'] for o in self._track_view(track)['objective_details'] if o['id'] == recommendation.get('objective_id')), next(iter(track['objectives']), None))
                current = next((a for a in snapshot['activities'] if a['id'] == recommendation.get('activity_id')), None)
                result.update(current_objective=objective, current_activity=current, last_attempt=next(iter(snapshot['attempts'][-1:]), None), last_assessment=next(iter(snapshot['assessments'][-1:]), None), next_action=recommendation['title'], text=f"{track['title']}: {track['status']}. {recommendation['reason']}")
            return result
        if action == 'quote_check':
            source = self._get(db, 'source', p.get('source_id'))
            if channel == 'chat_relayed' and source['sharing'] == 'metadata-only':
                fail('Source-sharing policy blocks quote checking', 'source_restricted', 403)
            quote = text(p.get('quote'), 'quote', 12000, True)
            normalized_quote = ' '.join(quote.split())
            normalized_excerpt = ' '.join(source['excerpt'].split())
            return {'source_id': source['id'], 'verified': normalized_quote in normalized_excerpt, 'entailment_verified': False, 'normalization': 'whitespace-v1', 'explanation': 'Collapses whitespace only; case, punctuation, and wording must match. Matching text does not establish entailment or correctness.'}
        if action == 'source_read':
            return {'source': self._safe_source(self._get(db, 'source', p.get('source_id')), channel, content=True)}
        if action == 'activity_read':
            activity = self._get(db, 'activity', p.get('activity_id'))
            unlocked = False
            if p.get('context_id'):
                _, track = self._context(db, p['context_id'])
                if activity['track_id'] != track['id']:
                    fail('Activity belongs to another track', 'context_mismatch', 403)
                unlocked = any(a['activity_id'] == activity['id'] for a in self._all(db, 'attempt', track['id'])) or any(h['activity_id'] == activity['id'] and h['level'] == 'full-solution-shown' and h.get('origin', 'authored') == 'authored' for h in self._all(db, 'help', track['id']))
            result = self._safe_activity(db, activity, channel, unlocked)
            if p.get('context_id'):
                lineage = self._lineage_ids(db, activity)
                result['help_events'] = [self._safe_help(db, h, channel, self._protected(db, activity, channel)) for h in self._all(db, 'help', activity['track_id']) if h['activity_id'] in lineage]
            return {'activity': result}
        if action in ('start', 'resume'):
            # Adapters own explicit human entry; model-facing dispatch cannot enroll.
            if channel != 'ui_direct':
                fail('Explicit user entry is required', 'explicit_entry_required', 403)
            if action == 'start':
                track = self._new(title=text(p.get('title'), 'title', 300, True), interest=text(p.get('interest', ''), 'interest'), status='exploring', brief='', objectives=[], assumptions=[], open_questions=[], revision=1, created_at=now, updated_at=now)
                track['learner_profile'] = self._profile(p.get('learner_profile', {}))
                self._put(db, 'track', track)
            else:
                track = self._get(db, 'track', p.get('track_id'))
                if track['status'] in ('paused', 'archived'):
                    track.update(status=track.get('resume_status', 'exploring'), revision=track['revision'] + 1, updated_at=now)
                    self._put(db, 'track', track, True)
            context = self._new(track_id=track['id'], active=True, created_at=now)
            self._put(db, 'context', context)
            return {'context_id': context['id'], 'track_id': track['id']}
        context, track = self._context(db, p.get('context_id'))
        tid = track['id']
        if action == 'leave':
            context.update(active=False, ended_at=now)
            self._put(db, 'context', context, True)
            return {'left': True, 'track_id': tid}
        if action == 'track_status' and channel != 'ui_direct':
            fail('Track status changes require an explicit learner action', 'explicit_approval_required', 403)
        if action in ('brief', 'approve', 'track_status'):
            if type(p.get('revision')) is not int or p['revision'] != track['revision']:
                fail('Track changed. Reload before editing.', 'revision_conflict', 409)
            if action == 'brief':
                track.update(brief=text(p.get('brief'), 'brief', required=True), objectives=strings(p.get('objectives', []), 'objectives'), status='proposed')
                if 'learner_profile' in p:
                    track['learner_profile'] = self._profile(p['learner_profile'], track.get('learner_profile'))
                for field in ('assumptions', 'open_questions'):
                    if field in p:
                        track[field] = strings(p[field], field)
            elif action == 'approve':
                if track['status'] != 'proposed' or not track['brief']:
                    fail('Propose a learning brief before approval', 'invalid_transition', 409)
                if channel != 'ui_direct':
                    fail('Path approval requires an explicit learner action', 'explicit_approval_required', 403)
                track['status'] = 'active'
            else:
                status = p.get('status')
                if status not in ('active', 'paused', 'archived'):
                    fail('Unsupported track status')
                if status == 'active' and track['status'] != 'active':
                    fail('Approve a proposal before activating it', 'invalid_transition', 409)
                if status != 'active':
                    track['resume_status'] = track['status']
                    for ctx in self._all(db, 'context', tid):
                        ctx.update(active=False, ended_at=now)
                        self._put(db, 'context', ctx, True)
                track['status'] = status
            track.update(revision=track['revision'] + 1, updated_at=now)
            self._put(db, 'track', track, True)
            return {'track': self._track_view(track)}
        if action == 'source':
            recommendation_id = p.get('recommendation_id')
            if recommendation_id is not None:
                recommendation = self._get(db, 'recommendation', recommendation_id, tid)
                if recommendation['status'] != 'accepted':
                    fail('Accept the recommendation before attaching its content', 'recommendation_not_accepted', 409)
            sharing = p.get('sharing', 'selected-excerpts')
            if sharing not in ('metadata-only', 'selected-excerpts', 'full-text'):
                fail('Unsupported source sharing policy')
            url = safe_url(p.get('url', ''))
            excerpt = text(p.get('excerpt', ''), 'excerpt', 50000)
            source = self._new(track_id=tid, title=text(p.get('title'), 'title', 300, True), kind=text(p.get('kind', 'notes'), 'kind', 100, True), url=url, locator=text(p.get('locator', ''), 'locator', 2000), excerpt=excerpt, excerpt_hash=hashlib.sha256(excerpt.encode()).hexdigest(), sharing=sharing, verification=text(p.get('verification', 'unverified'), 'verification', 1000), author_kind='learner' if channel == 'ui_direct' else 'chat-agent', created_at=now)
            if recommendation_id is not None:
                source['recommendation_id'] = recommendation_id
            self._put(db, 'source', source)
            return {'source': self._safe_source(source, channel)}
        if action == 'recommendation':
            if p.get('status', 'candidate') != 'candidate':
                fail('New recommendations must remain candidates pending learner choice')
            recommendation = self._new(track_id=tid, title=text(p.get('title'), 'title', 300, True), url=safe_url(p.get('url', '')), reason=text(p.get('reason'), 'reason', 4000, True), prerequisites=strings(p.get('prerequisites', []), 'prerequisites'), verification=text(p.get('verification', 'unverified'), 'verification', 1000), locator=text(p.get('locator', ''), 'locator', 2000), status='candidate', author_kind='learner' if channel == 'ui_direct' else 'chat-agent', created_at=now, updated_at=now)
            self._put(db, 'recommendation', recommendation)
            return {'recommendation': recommendation}
        if action == 'recommendation_decide':
            if channel != 'ui_direct':
                fail('Recommendation decisions require an explicit learner action', 'explicit_approval_required', 403)
            recommendation = self._get(db, 'recommendation', p.get('recommendation_id'), tid)
            if p.get('status') not in ('accepted', 'declined'):
                fail('Recommendation decision must be accepted or declined')
            recommendation.update(status=p['status'], updated_at=now)
            self._put(db, 'recommendation', recommendation, True)
            return {'recommendation': recommendation}
        if action in ('activity', 'activity_revision'):
            previous = None
            if action == 'activity_revision':
                previous = self._get(db, 'activity', p.get('activity_id'), tid)
                if any(a.get('previous_version_id') == previous['id'] for a in self._all(db, 'activity', tid)):
                    fail('Activity already revised; use its latest version', 'revision_conflict', 409)
            source_ids = strings(p.get('source_ids', []), 'source_ids', 30, 100)
            for ident in source_ids:
                source = self._get(db, 'source', ident, tid)
                if channel == 'chat_relayed' and source['sharing'] == 'metadata-only':
                    fail('Model cannot author from a metadata-only source', 'source_restricted', 403)
            kind = p.get('kind')
            if kind not in ('explanation', 'prediction', 'trace', 'build'):
                fail('Activity kind must be explanation, prediction, trace, or build')
            criteria = p.get('criteria')
            if isinstance(criteria, str):
                criteria = [criteria]
            criteria = strings(criteria, 'criteria', 30, 2000)
            if not criteria:
                fail('Activity needs precommitted criteria')
            hints = p.get('hints', [])
            if isinstance(hints, list):
                hints = dict(zip(LEVELS[1:4], strings(hints, 'hints', 3, 5000)))
            if not isinstance(hints, dict) or set(hints) - set(LEVELS[1:4]):
                fail('Hints use nudge, targeted-hint, or worked-step')
            hints = {k: text(v, 'hint', 5000, True) for k, v in hints.items()}
            activity = self._new(track_id=tid, title=text(p.get('title'), 'title', 300, True), kind=kind, prompt=text(p.get('prompt'), 'prompt', required=True), description=text(p.get('description', ''), 'description'), criteria=criteria, solution=text(p.get('solution'), 'solution', required=True), hints=hints, source_ids=source_ids, visual=self._visual(p.get('visual')), version=1, author_kind='learner' if channel == 'ui_direct' else 'chat-agent', created_at=now)
            details = {o['id']: o for o in self._track_view(track)['objective_details']}
            if previous and 'objective_ids' not in p:
                objective_ids = previous.get('objective_ids', [])
                snapshots = previous.get('objective_snapshots', [])
            else:
                objective_ids = strings(p.get('objective_ids', []), 'objective_ids', 30, 100)
                if len(set(objective_ids)) != len(objective_ids) or any(ident not in details for ident in objective_ids):
                    fail('Objective IDs must be distinct objectives on the current track')
                snapshots = [details[ident] for ident in objective_ids]
            competency = p.get('competency', (previous or {}).get('competency', 'conceptual'))
            purpose = p.get('purpose', (previous or {}).get('purpose', 'practice'))
            if competency not in ('conceptual', 'practical', 'both') or purpose not in ('diagnostic', 'practice', 'transfer'):
                fail('Unsupported competency or activity purpose')
            activity.update(objective_ids=objective_ids, objective_snapshots=snapshots, competency=competency, purpose=purpose)
            if previous:
                activity.update(version=previous['version'] + 1, previous_version_id=previous['id'], root_activity_id=previous.get('root_activity_id', previous['id']))
            self._put(db, 'activity', activity)
            return {'activity': self._safe_activity(db, activity, channel)}
        if action == 'run':
            activity = self._get(db, 'activity', p.get('activity_id'), tid)
            run = self._new(track_id=tid, activity_id=activity['id'], activity_version=activity['version'], created_at=now)
            self._put(db, 'run', run)
            return {'run_id': run['id'], 'activity_id': activity['id']}
        if action in ('help', 'submit'):
            run = self._get(db, 'run', p.get('run_id'), tid)
            activity = self._get(db, 'activity', run['activity_id'], tid)
            attempts = [a for a in self._all(db, 'attempt', tid) if a['run_id'] == run['id']]
            if action == 'submit':
                answer = text(p.get('answer'), 'answer', 30000, True)
                if attempts:
                    if attempts[0]['answer'] != answer or attempts[0]['channel'] != channel:
                        fail('Run already submitted with a different payload or channel', 'submission_conflict', 409)
                    return {'attempt': self._safe_evidence(db, attempts[0], 'attempt', channel), 'duplicate': True}
                lineage = self._lineage_ids(db, activity)
                events = [h for h in self._all(db, 'help', tid) if h['activity_id'] in lineage]
                prior_attempts = [a for a in self._all(db, 'attempt', tid) if a['activity_id'] in lineage]
                assistance = max((h['level'] for h in events), key=LEVELS.index, default='unknown' if channel == 'chat_relayed' or prior_attempts else 'none')
                attempt = self._new(track_id=tid, activity_id=activity['id'], activity_version=activity['version'], run_id=run['id'], answer=answer, channel=channel, assistance=assistance, assistance_events=events, prior_help_exposure=any(h['run_id'] != run['id'] for h in events), prior_attempt_count=len(prior_attempts), status='awaiting_assessment', created_at=now)
                self._put(db, 'attempt', attempt)
                for review in self._all(db, 'review', tid):
                    if review.get('objective_id') in activity.get('objective_ids', []):
                        self._objective_review(db, review, now)
                        self._put(db, 'review', review, True)
                return {'attempt': self._safe_evidence(db, attempt, 'attempt', channel), 'duplicate': False}
            level = p.get('level')
            if level not in LEVELS[1:]:
                fail('Unsupported help level')
            if self._protected(db, activity, channel):
                fail('Source-sharing policy blocks this help', 'source_restricted', 403)
            generated = 'content' in p
            request_id = text(p['request_id'], 'request_id', 100, True) if 'request_id' in p else None
            if generated and request_id is None:
                fail('Generated help requires request_id for safe retries')
            content = text(p['content'], 'content', 5000, True) if generated else (activity['solution'] if level == 'full-solution-shown' else activity['hints'].get(level))
            if content is None:
                fail('No authored help at this level', 'help_unavailable', 404)
            origin = 'generated' if generated else 'authored'
            duplicate = False
            event = next((h for h in self._all(db, 'help', tid) if request_id is not None and h['run_id'] == run['id'] and h.get('request_id') == request_id), None)
            if event:
                if (event['level'], event.get('content'), event['channel'], event.get('origin', 'authored')) != (level, content, channel, origin):
                    fail('Help request ID already used with different content, level or channel', 'help_conflict', 409)
                duplicate = True
            else:
                if attempts:
                    fail('Submitted attempts are immutable; start a new run for further help', 'run_submitted', 409)
                event = self._new(track_id=tid, run_id=run['id'], activity_id=activity['id'], level=level, channel=channel, content=content, author_kind=('learner' if channel == 'ui_direct' else 'chat-agent') if generated else activity['author_kind'], origin=origin, created_at=now)
                if request_id is not None:
                    event['request_id'] = request_id
                self._put(db, 'help', event)
            result = {'help': event, 'level': level, 'content': content, 'duplicate': duplicate}
            if level == 'full-solution-shown' and not generated:
                result['activity'] = self._safe_activity(db, activity, channel, True)
            return result
        if action == 'assess':
            attempt = self._get(db, 'attempt', p.get('attempt_id'), tid)
            method = 'self' if channel == 'ui_direct' else 'agent'
            if p.get('method') != method:
                fail('Assessment method must match its authenticated channel', 'method_mismatch', 403)
            outcome = p.get('outcome')
            if outcome not in ('needs-work', 'developing', 'demonstrated'):
                fail('Unsupported assessment outcome')
            supersedes = p.get('supersedes')
            if supersedes:
                previous = self._get(db, 'assessment', supersedes, tid)
                if previous['attempt_id'] != attempt['id'] or previous['method'] != method:
                    fail('Correction must retain attempt and assessment method', 'assessment_conflict', 409)
                if any(a['supersedes'] == supersedes for a in self._all(db, 'assessment', tid)):
                    fail('Assessment already superseded', 'assessment_conflict', 409)
            assessment = self._new(track_id=tid, attempt_id=attempt['id'], activity_id=attempt['activity_id'], activity_version=attempt['activity_version'], rubric_version=attempt['activity_version'], method=method, author_kind='self-assessment' if method == 'self' else 'chat-agent', feedback=text(p.get('feedback'), 'feedback', required=True), outcome=outcome, supersedes=supersedes, created_at=now)
            if 'uncertainty' in p:
                assessment['uncertainty'] = text(p['uncertainty'], 'uncertainty', 2000)
            if 'criterion_results' in p:
                results = p['criterion_results']
                criteria = self._get(db, 'activity', attempt['activity_id'], tid)['criteria']
                if not isinstance(results, list) or len(results) != len(criteria):
                    fail('Provide exactly one result per immutable criterion')
                clean = []
                indices = set()
                for item in results:
                    if not isinstance(item, dict) or set(item) != {'index', 'outcome', 'feedback'}:
                        fail('Criterion result requires index, outcome and feedback')
                    index = item['index']
                    if type(index) is not int or not 0 <= index < len(criteria) or index in indices or item['outcome'] not in OUTCOMES:
                        fail('Criterion results must cover each criterion once with a supported outcome')
                    indices.add(index)
                    clean.append({'index': index, 'outcome': item['outcome'], 'feedback': text(item['feedback'], 'criterion feedback', 2000, True)})
                if min((item['outcome'] for item in clean), key=OUTCOMES.index) != outcome:
                    fail('Overall outcome must match the weakest criterion result')
                assessment['criterion_results'] = sorted(clean, key=lambda item: item['index'])
            self._put(db, 'assessment', assessment)
            days = {'needs-work': 1, 'developing': 3, 'demonstrated': 7}[outcome]
            activity = self._get(db, 'activity', attempt['activity_id'], tid)
            objectives = activity.get('objective_ids', [])
            reviews = []
            for objective_id in objectives or [None]:
                review = next((r for r in self._all(db, 'review', tid) if (r.get('objective_id') == objective_id if objective_id else not r.get('objective_id') and r['activity_id'] == attempt['activity_id'])), None)
                exists = review is not None
                if not exists:
                    review = self._new(track_id=tid, activity_id=attempt['activity_id'])
                policy = 2 if objective_id else 1
                if objective_id:
                    review['objective_id'] = objective_id
                    # Corrections and extra judgments on already-known tasks
                    # retain a learner's date; feedback on new work restarts the
                    # automatic policy, as it does for legacy activity reviews.
                    if review.get('manual') and attempt['id'] not in review.get('manual_attempt_ids', [review.get('attempt_id')]):
                        review['manual'] = False
                        review.pop('manual_attempt_ids', None)
                review.update(activity_id=attempt['activity_id'], attempt_id=attempt['id'], assessment_id=assessment['id'], policy_version=policy, updated_at=now)
                if objective_id:
                    review.setdefault('manual', False)
                    self._objective_review(db, review, now)
                else:
                    review.update(due_at=iso(datetime.fromisoformat(now.replace('Z', '+00:00')) + timedelta(days=days)), reason=f'Policy v1: {method} assessment {outcome}; revisit in {days} day(s). Fixed heuristic, not a mastery estimate.', manual=False, disputed=False)
                self._put(db, 'review', review, exists)
                reviews.append(review)
            return {'assessment': self._safe_evidence(db, assessment, 'assessment', channel), 'review': reviews[0], 'reviews': reviews}
        if action == 'dispute':
            assessment = self._get(db, 'assessment', p.get('assessment_id'), tid)
            dispute = self._new(track_id=tid, assessment_id=assessment['id'], attempt_id=assessment['attempt_id'], reason=text(p.get('reason'), 'reason', 4000, True), created_at=now)
            self._put(db, 'dispute', dispute)
            objective_ids = self._get(db, 'activity', assessment['activity_id'], tid).get('objective_ids', [])
            for review in self._all(db, 'review', tid):
                if review.get('objective_id') in objective_ids:
                    self._objective_review(db, review, now)
                    self._put(db, 'review', review, True)
                elif not review.get('objective_id') and review['assessment_id'] == assessment['id']:
                    review.update(disputed=True, reason='Assessment disputed; review the evidence before relying on this schedule.', updated_at=now)
                    self._put(db, 'review', review, True)
            return {'dispute': self._safe_evidence(db, dispute, 'dispute', channel)}
        if action == 'review':
            if channel != 'ui_direct':
                fail('Manual review date changes require an explicit learner action', 'explicit_approval_required', 403)
            review = self._get(db, 'review', p.get('review_id'), tid)
            review.update(due_at=iso(p.get('due_at')), reason=f"Learner manually adjusted the review date; policy v{review['policy_version']} interval overridden.", manual=True, updated_at=now)
            if review.get('objective_id'):
                activity_ids = {a['id'] for a in self._all(db, 'activity', tid) if review['objective_id'] in a.get('objective_ids', [])}
                review['manual_attempt_ids'] = [a['id'] for a in self._all(db, 'attempt', tid) if a['activity_id'] in activity_ids]
                self._objective_review(db, review, now)
            self._put(db, 'review', review, True)
            return {'review': review}
        fail('Unknown action')

    def backup(self, path):
        destination = Path(path).expanduser().resolve()
        if destination == self.path or not destination.parent.is_dir() or destination.exists():
            fail('Backup requires a new file in an existing directory', 'invalid_path')
        with self._connection() as source:
            target = sqlite3.connect(str(destination))
            try:
                source.backup(target)
            finally:
                target.close()
        return {'path': str(destination), 'store_id': self.store_id, 'schema_version': 1}

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
import uuid
from urllib.parse import urlsplit

API_VERSION = SCHEMA_VERSION = 1
LEVELS = ['none', 'nudge', 'targeted-hint', 'worked-step', 'full-solution-shown']
READS = {'state', 'track', 'source_read', 'activity_read', 'resume_brief', 'export', 'quote_check'}
WRITES = {'start', 'resume', 'leave', 'brief', 'approve', 'track_status', 'source', 'activity', 'run', 'help', 'submit', 'assess', 'dispute', 'review', 'recommendation', 'recommendation_decide', 'activity_revision'}
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
            db.execute('PRAGMA journal_mode=WAL')
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

    def _safe_activity(self, db, activity, channel, unlocked=False):
        result = {k: activity[k] for k in ('id', 'track_id', 'title', 'kind', 'prompt', 'description', 'source_ids', 'version', 'author_kind', 'created_at')}
        result.update(previous_version_id=activity.get('previous_version_id'), root_activity_id=activity.get('root_activity_id', activity['id']))
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
            elif kind == 'activity':
                rows = [self._safe_activity(db, r, channel) for r in rows]
            elif channel == 'chat_relayed' and kind in ('attempt', 'assessment', 'dispute'):
                for record in rows:
                    attempt = record if kind == 'attempt' else self._get(db, 'attempt', record['attempt_id'])
                    if self._protected(db, self._get(db, 'activity', attempt['activity_id']), channel):
                        for key in ('answer', 'feedback', 'reason'):
                            if key in record:
                                record[key] = 'Content withheld by source-sharing policy.'
            result[{'activity': 'activities'}.get(kind, kind + 's')] = rows
        return result

    def _visual(self, visual):
        if visual is None:
            return None
        if not isinstance(visual, dict) or visual.get('type') != 'sequence' or visual.get('schema_version', 1) != 1:
            fail('Only schema 1 structured sequence visuals are supported')
        if set(visual) - {'type', 'schema_version', 'title', 'participants', 'steps', 'visible_steps'}:
            fail('Unsupported visual fields')
        participants = visual.get('participants')
        steps = visual.get('steps')
        if not isinstance(participants, list) or not 1 <= len(participants) <= 10 or not isinstance(steps, list) or not 1 <= len(steps) <= 30:
            fail('Sequence requires 1–10 participants and 1–30 steps')
        ids = set()
        clean_participants = []
        for part in participants:
            if not isinstance(part, dict) or set(part) != {'id', 'label'}:
                fail('Each participant requires only id and label')
            ident = text(part['id'], 'participant id', 60, True)
            if ident in ids:
                fail('Duplicate participant id')
            ids.add(ident)
            clean_participants.append({'id': ident, 'label': text(part['label'], 'participant label', 150, True)})
        clean_steps = []
        for step in steps:
            if not isinstance(step, dict) or set(step) - {'from', 'to', 'label', 'explanation'}:
                fail('Unsupported sequence step')
            if not isinstance(step.get('from'), str) or not isinstance(step.get('to'), str) or step['from'] not in ids or step['to'] not in ids:
                fail('Step participants must exist')
            clean_steps.append({'from': step['from'], 'to': step['to'], 'label': text(step.get('label', ''), 'step label', 300, True), 'explanation': text(step.get('explanation', ''), 'step explanation', 2000)})
        visible = visual.get('visible_steps', 1)
        if type(visible) is not int or not 0 <= visible <= len(steps):
            fail('visible_steps is outside the sequence')
        return {'schema_version': 1, 'type': 'sequence', 'title': text(visual.get('title', ''), 'visual title', 300), 'participants': clean_participants, 'steps': clean_steps, 'visible_steps': visible}

    def dispatch(self, action, params, *, channel='ui_direct'):
        if not isinstance(action, str) or action not in READS | WRITES or not isinstance(params, dict):
            fail('Unknown action or invalid parameters')
        if channel not in ('ui_direct', 'chat_relayed'):
            fail('Unsupported channel')
        try:
            encoded = json.dumps(params, allow_nan=False)
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
        now = iso(self.clock())
        if action in ('state', 'export'):
            result = {'api_version': 1, 'schema_version': 1, 'store_id': self.store_id, 'compatible_client_versions': [1], **self._snapshot(db, channel)}
            if action == 'export':
                result.update(export_version=1, exported_at=now)
                # This export is a shareable view. Full private recovery uses backup().
                result['sources'] = [self._safe_source(s, channel, content=True) for s in self._all(db, 'source')]
            return result
        if action in ('track', 'resume_brief'):
            track = self._get(db, 'track', p.get('track_id'))
            snapshot = self._snapshot(db, channel, track['id'])
            snapshot.pop('tracks')
            result = {'track': track, **snapshot}
            if action == 'resume_brief':
                result.update(current_objective=next(iter(track['objectives']), None), current_activity=next(iter(snapshot['activities'][-1:]), None), last_attempt=next(iter(snapshot['attempts'][-1:]), None), last_assessment=next(iter(snapshot['assessments'][-1:]), None), next_action='Review your proposed direction' if track['status'] in ('exploring', 'proposed') else 'Continue studying or choose a practice activity', text=f"{track['title']}: {track['status']}. {track['brief']}")
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
                unlocked = any(a['activity_id'] == activity['id'] for a in self._all(db, 'attempt', track['id'])) or any(h['activity_id'] == activity['id'] and h['level'] == 'full-solution-shown' for h in self._all(db, 'help', track['id']))
            return {'activity': self._safe_activity(db, activity, channel, unlocked)}
        if action in ('start', 'resume'):
            # Adapters own explicit human entry; model-facing dispatch cannot enroll.
            if channel != 'ui_direct':
                fail('Explicit user entry is required', 'explicit_entry_required', 403)
            if action == 'start':
                track = self._new(title=text(p.get('title'), 'title', 300, True), interest=text(p.get('interest', ''), 'interest'), status='exploring', brief='', objectives=[], assumptions=[], open_questions=[], revision=1, created_at=now, updated_at=now)
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
            return {'track': track}
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
                    return {'attempt': attempts[0], 'duplicate': True}
                events = [h for h in self._all(db, 'help', tid) if h['activity_id'] == activity['id']]
                prior_attempts = [a for a in self._all(db, 'attempt', tid) if a['activity_id'] == activity['id']]
                assistance = max((h['level'] for h in events), key=LEVELS.index, default='unknown' if channel == 'chat_relayed' or prior_attempts else 'none')
                attempt = self._new(track_id=tid, activity_id=activity['id'], activity_version=activity['version'], run_id=run['id'], answer=answer, channel=channel, assistance=assistance, assistance_events=events, prior_help_exposure=any(h['run_id'] != run['id'] for h in events), prior_attempt_count=len(prior_attempts), status='awaiting_assessment', created_at=now)
                self._put(db, 'attempt', attempt)
                return {'attempt': attempt, 'duplicate': False}
            if attempts:
                fail('Submitted attempts are immutable; start a new run for further help', 'run_submitted', 409)
            level = p.get('level')
            if level not in LEVELS[1:]:
                fail('Unsupported help level')
            if self._protected(db, activity, channel):
                fail('Source-sharing policy blocks this help', 'source_restricted', 403)
            content = activity['solution'] if level == 'full-solution-shown' else activity['hints'].get(level)
            if content is None:
                fail('No authored help at this level', 'help_unavailable', 404)
            event = self._new(track_id=tid, run_id=run['id'], activity_id=activity['id'], level=level, channel=channel, created_at=now)
            self._put(db, 'help', event)
            result = {'help': event, 'level': level, 'content': content}
            if level == 'full-solution-shown':
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
            self._put(db, 'assessment', assessment)
            days = {'needs-work': 1, 'developing': 3, 'demonstrated': 7}[outcome]
            review = next((r for r in self._all(db, 'review', tid) if r['activity_id'] == attempt['activity_id']), None)
            exists = review is not None
            if not exists:
                review = self._new(track_id=tid, activity_id=attempt['activity_id'])
            review.update(attempt_id=attempt['id'], assessment_id=assessment['id'], due_at=iso(datetime.fromisoformat(now.replace('Z', '+00:00')) + timedelta(days=days)), reason=f'Policy v1: {method} assessment {outcome}; revisit in {days} day(s). Fixed heuristic, not a mastery estimate.', policy_version=1, updated_at=now, manual=False, disputed=False)
            self._put(db, 'review', review, exists)
            return {'assessment': assessment, 'review': review}
        if action == 'dispute':
            assessment = self._get(db, 'assessment', p.get('assessment_id'), tid)
            dispute = self._new(track_id=tid, assessment_id=assessment['id'], attempt_id=assessment['attempt_id'], reason=text(p.get('reason'), 'reason', 4000, True), created_at=now)
            self._put(db, 'dispute', dispute)
            for review in self._all(db, 'review', tid):
                if review['assessment_id'] == assessment['id']:
                    review.update(disputed=True, reason='Assessment disputed; review the evidence before relying on this schedule.', updated_at=now)
                    self._put(db, 'review', review, True)
            return {'dispute': dispute}
        if action == 'review':
            if channel != 'ui_direct':
                fail('Manual review date changes require an explicit learner action', 'explicit_approval_required', 403)
            review = self._get(db, 'review', p.get('review_id'), tid)
            review.update(due_at=iso(p.get('due_at')), reason='Learner manually adjusted the review date; policy v1 interval overridden.', manual=True, updated_at=now)
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

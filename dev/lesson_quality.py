#!/usr/bin/env python3
"""Prepare blinded human reviews of saved lessons; never calls a model or host."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import secrets
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / 'docs/evaluations/lesson-quality/cases.json'
RUBRIC = (
    'Correctness and source support',
    'Outcome, example, exercise and solution alignment',
    'Visible intermediate reasoning and appropriate prerequisites',
    'Concrete application with a meaningful changed condition',
    'Useful pacing and absence of padding or repeated metadata',
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_cases(path):
    data = json.loads(path.read_text())
    cases = data['cases']
    ids = [case['id'] for case in cases]
    if data['version'] != 1 or not ids or len(ids) != len(set(ids)):
        raise ValueError('Expected version 1 cases with unique IDs')
    return {case['id']: case for case in cases}


def fingerprint(cases):
    paths = [ROOT / 'ui/src/tutor-session.mjs', ROOT / 'skills/humanizer/SKILL.md',
             *sorted((ROOT / 'skills/teach').rglob('*.md'))]
    contents = {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in paths}
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    return {'revision': revision, 'authoring_sha256': digest(json.dumps(contents, sort_keys=True).encode()),
            'cases_sha256': digest(cases.read_bytes()), 'authoring_files': contents}


def capture(path, cases, cases_hash):
    data = json.loads(path.read_text())
    run = data['run']
    for field in ('provider', 'model', 'revision', 'authoring_sha256', 'cases_sha256'):
        if not isinstance(run[field], str) or not run[field].strip():
            raise ValueError(f'{path.name}: missing run {field}')
    for field in ('authoring_sha256', 'cases_sha256'):
        if not re.fullmatch('[0-9a-f]{64}', run[field]):
            raise ValueError(f'{path.name}: invalid {field}')
    if run['cases_sha256'] != cases_hash:
        raise ValueError(f'{path.name}: cases_sha256 differs from the supplied cases/source fixtures')
    if not isinstance(run['settings'], dict):
        raise ValueError('run settings must be an object; record unavailable settings explicitly')
    lessons = {}
    for item in data['lessons']:
        case_id, sample, lesson = item['case_id'], item['sample'], item['lesson']
        if case_id not in cases or type(sample) is not int or sample < 1 or (case_id, sample) in lessons:
            raise ValueError(f'{path.name}: unknown case, invalid sample or duplicate sample')
        if not isinstance(lesson.get('content'), str) or not lesson['content'].strip():
            raise ValueError('A captured lesson needs nonempty content')
        teaching = lesson.get('teaching')
        if not isinstance(teaching, dict) or not all(teaching.get(k) for k in ('outcome', 'misconception')) or not isinstance(teaching.get('prerequisites'), list):
            raise ValueError('A captured lesson needs complete teaching metadata')
        if 'practice' not in lesson or (lesson['practice'] is not None and
                (not isinstance(lesson['practice'], dict) or not all(k in lesson['practice'] for k in ('kind', 'prompt', 'criteria', 'hints', 'explanation')))):
            raise ValueError('A captured lesson needs a practice object or explicit null')
        lessons[case_id, sample] = lesson
    if {key[0] for key in lessons} != set(cases):
        raise ValueError(f'{path.name}: capture all benchmark cases, including failures in a separate run log')
    for case_id in cases:
        samples = {sample for key, sample in lessons if key == case_id}
        if len(samples) < 3 or samples != set(range(1, max(samples) + 1)):
            raise ValueError(f'{path.name}: each case needs at least three consecutive samples starting at 1')
    return run, lessons


def fenced_json(value):
    body = json.dumps(value, ensure_ascii=False, indent=2)
    fence = '`' * max(3, max((len(m[0]) + 1 for m in re.finditer(r'`+', body)), default=0))
    return f'{fence}json\n{body}\n{fence}'


def compare(cases_path, baseline, candidate, output):
    cases = read_cases(cases_path)
    first_run, first = capture(baseline, cases, digest(cases_path.read_bytes()))
    second_run, second = capture(candidate, cases, digest(cases_path.read_bytes()))
    for field in ('provider', 'model', 'settings'):
        if first_run[field] != second_run[field]:
            raise ValueError(f'Keep {field} identical for an authoring comparison')
    if first.keys() != second.keys():
        raise ValueError('Baseline and candidate case/sample pairs must match')
    # Complete validation before creating anything. Never overwrite an earlier review.
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    key = {'learning_effectiveness_evaluated': False, 'run': {'baseline': first_run, 'candidate': second_run},
           'capture_sha256': {'baseline': digest(baseline.read_bytes()), 'candidate': digest(candidate.read_bytes())}, 'pairs': []}
    lines = ['# Blinded lesson review', '',
             'Rate each dimension 0 (fails), 1 (needs revision), or 2 (meets). Cite a passage for each defect. '
             'Record factual/solution errors separately; do not hide them in a combined score. '
             'Choose A, B, tie, or neither. These are human judgments, not a learning or AI-authorship score.', '']
    for number, pair in enumerate(sorted(first), 1):
        case_id, sample = pair
        case = cases[case_id]
        variants = ['baseline', 'candidate']
        secrets.SystemRandom().shuffle(variants)
        key['pairs'].append({'pair': number, 'case_id': case_id, 'sample': sample, 'variants': dict(zip(('A', 'B'), variants))})
        lines += [f'## Pair {number}: {case_id}, sample {sample}', '', '### Request', '', case['request'], '']
        if case.get('sources'):
            lines += ['### Supplied sources', '', fenced_json(case['sources']), '']
        lines += ['### Case checks', '', *[f'- {check}' for check in case['review_checks']], '']
        for label, variant in zip(('A', 'B'), variants):
            lines += [f'### Variant {label}', '', fenced_json((first if variant == 'baseline' else second)[pair]), '']
        lines += ['### Reviewer findings', '', '| Dimension | A | B | Evidence |', '| --- | --- | --- | --- |',
                  *[f'| {item} | | | |' for item in RUBRIC], '',
                  'Hard defects: ', '', 'Preference (A/B/tie/neither) and reason: ', '']
    (output / 'review.md').write_text('\n'.join(lines))
    (output / 'key.json').write_text(json.dumps(key, indent=2) + '\n')
    return len(first)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    snapshot = commands.add_parser('fingerprint', help='Print current authoring/case hashes; makes no model call')
    snapshot.add_argument('--cases', type=Path, default=CASES)
    review = commands.add_parser('compare', help='Pair two saved captures for human review')
    review.add_argument('--cases', type=Path, default=CASES)
    review.add_argument('--baseline', type=Path, required=True)
    review.add_argument('--candidate', type=Path, required=True)
    review.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'fingerprint':
            read_cases(args.cases)
            print(json.dumps(fingerprint(args.cases), indent=2))
        else:
            count = compare(args.cases, args.baseline, args.candidate, args.output)
            print(f'Prepared {count} pairs. Share review.md only; keep key.json with the coordinator. No model or learner evaluation was run.')
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()

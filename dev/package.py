#!/usr/bin/env python3
"""Package built Learning artifacts without installing or accessing host data."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = 'hermes-learning'
VERSION = '0.1.0'
# Deliberately enumerate files; never recursively include a plugin directory.
FILES = (
    'plugin.yaml', '__init__.py', 'runtime.py', 'learning_store.py', 'THIRD_PARTY_NOTICES.md',
    'dashboard/manifest.json', 'dashboard/plugin_api.py', 'dashboard/dist/index.js',
    'skills/teach/SKILL.md', 'skills/humanizer/SKILL.md',
    'desktop/plugin.js', 'desktop/package.json',
)


def collect(source):
    source = Path(source).absolute()
    if source.is_symlink():
        raise ValueError('Plugin source must not be a symlink')
    contents = {}
    for relative in FILES:
        path = source
        for part in Path(relative).parts:
            path = path / part
            if path.is_symlink():
                raise ValueError(f'Symlinks are not packaged: {relative}')
        if not path.is_file():
            raise ValueError(f'Missing required artifact: {relative}; build the UI first')
        contents[relative] = path.read_bytes()
    # The owned manifest uses simple top-level scalar fields. Reject unsupported
    # forms rather than interpreting arbitrary YAML tags or adding a dependency.
    yaml = contents['plugin.yaml'].decode('utf-8')
    for key, expected in (('name', NAME), ('version', VERSION)):
        values = re.findall(r'^' + key + r':\s*([^\n]+)$', yaml, re.MULTILINE)
        if len(values) != 1 or values[0].strip().strip('\"\'') != expected:
            raise ValueError(f'plugin.yaml {key} must be {expected}')
    dashboard = json.loads(contents['dashboard/manifest.json'])
    for key, expected in (('name', NAME), ('version', VERSION),
                          ('entry', 'dist/index.js'), ('api', 'plugin_api.py')):
        if dashboard.get(key) != expected:
            raise ValueError(f'Dashboard {key} must be {expected}')
    desktop = json.loads(contents['desktop/package.json'])
    if desktop.get('type') != 'module':
        raise ValueError('Desktop package must declare type module')
    for key, expected in (('name', NAME), ('version', VERSION)):
        if key in desktop and desktop[key] != expected:
            raise ValueError(f'Desktop {key} must be {expected}')
    return contents


def archive(path, contents):
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for relative, content in sorted(contents.items()):
            entry = zipfile.ZipInfo(f'{NAME}/{relative}', date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(entry, content, compresslevel=9)


def package(source=ROOT, output=ROOT / 'dist'):
    contents = collect(source)  # Validate everything before producing artifacts.
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    paths = (output / f'{NAME}-{VERSION}.zip', output / f'{NAME}-desktop-{VERSION}.zip')
    archive(paths[0], contents)
    archive(paths[1], {name.removeprefix('desktop/'): contents[name]
                       for name in ('desktop/plugin.js', 'desktop/package.json')})
    checksums = ''.join(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n' for path in paths)
    (output / 'SHA256SUMS').write_text(checksums, encoding='utf-8')
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    try:
        paths = package(output=args.output)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    for path in paths:
        print(path)


if __name__ == '__main__':
    main()

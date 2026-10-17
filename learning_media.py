"""Bounded local image import and offline Archify rendering. No model calls."""
import base64
import hashlib
from html import escape
import json
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import subprocess
import tempfile
import threading
import zlib

MAX_IMAGE = 5 * 1024 * 1024
MAX_PIXELS = 16_000_000
_RENDER_SLOTS = threading.BoundedSemaphore(2)
ARCHIFY = Path(__file__).resolve().parent / 'vendor' / 'archify'


def image_file(path):
    if not isinstance(path, str) or not Path(path).is_absolute():
        raise ValueError('Provide the absolute path to a generated PNG or JPEG on the Hermes host.')
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as file:
            info = os.fstat(file.fileno())
            if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_IMAGE:
                raise ValueError('Images must be regular files no larger than 5 MB.')
            data = file.read(MAX_IMAGE + 1)
    except OSError as exc:
        raise ValueError('Cannot read this image file; provide an existing regular file, not a symlink.') from exc
    if len(data) > MAX_IMAGE:
        raise ValueError('Images must be no larger than 5 MB.')
    width = height = 0
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        mime = 'image/png'
        offset = 8; seen_end = False; seen_data = False
        while offset + 12 <= len(data):
            size = int.from_bytes(data[offset:offset+4], 'big'); kind = data[offset+4:offset+8]
            end = offset + 12 + size
            if end > len(data): raise ValueError('Truncated PNG image.')
            payload = data[offset+8:offset+8+size]
            crc = int.from_bytes(data[offset+8+size:end], 'big')
            if zlib.crc32(kind + payload) != crc: raise ValueError('PNG checksum is invalid.')
            if offset == 8:
                if kind != b'IHDR' or size != 13: raise ValueError('PNG header is invalid.')
                width, height = struct.unpack('>II', payload[:8])
            if kind == b'IDAT': seen_data = True
            if kind == b'IEND':
                seen_end = size == 0 and end == len(data); break
            offset = end
        if not seen_end or not seen_data: raise ValueError('PNG image is incomplete.')
    elif data.startswith(b'\xff\xd8') and data.endswith(b'\xff\xd9'):
        mime = 'image/jpeg'; offset = 2
        while offset + 4 <= len(data):
            if data[offset] != 255: break
            while offset < len(data) and data[offset] == 255: offset += 1
            if offset >= len(data): break
            marker = data[offset]; offset += 1
            if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7: continue
            size = int.from_bytes(data[offset:offset+2], 'big')
            if size < 2 or offset + size > len(data): break
            if marker in (0xC0, 0xC1, 0xC2):
                if size < 8: break
                height, width = struct.unpack('>HH', data[offset+3:offset+7]); break
            offset += size
        if not width: raise ValueError('Unsupported or incomplete JPEG image.')
    else:
        raise ValueError('Only PNG and JPEG image contents are supported; HTML and SVG uploads are not accepted.')
    if width < 1 or height < 1 or width * height > MAX_PIXELS or max(width, height) > 8192:
        raise ValueError('Image dimensions exceed 16 megapixels or 8192 pixels per side.')
    return data, mime, width, height, hashlib.sha256(data).hexdigest()


def render_archify(source):
    if not _RENDER_SLOTS.acquire(timeout=1):
        raise ValueError('Other diagrams are rendering. Retry this diagram in a moment.')
    try:
        return _render_archify(source)
    finally:
        _RENDER_SLOTS.release()


def _render_archify(source):
    if not isinstance(source, str) or len(source) > 50000:
        raise ValueError('Archify source must be JSON of at most 50000 characters.')
    try: document = json.loads(source)
    except (ValueError, RecursionError) as exc: raise ValueError('Archify source must be valid JSON.') from exc
    if not isinstance(document, dict) or document.get('diagram_type') not in ('architecture', 'workflow', 'sequence', 'dataflow', 'lifecycle'):
        raise ValueError('Choose an Archify architecture, workflow, sequence, dataflow, or lifecycle diagram.')
    # No network captures, repository reads, custom output paths, or author scripts.
    def inspect(value, depth=0):
        if depth > 20: raise ValueError('Archify JSON is nested too deeply.')
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ('repository', 'repositoryEvidence', 'sourceEvidence', 'evidence'):
                    raise ValueError('Repository evidence and output paths are not supported in lesson diagrams.')
                if key == 'brand' and (not isinstance(item, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', item)):
                    raise ValueError('Use bundled Archify brand IDs; remote brand resources are not supported.')
                inspect(item, depth + 1)
        elif isinstance(value, list):
            if len(value) > 200: raise ValueError('Archify collections are limited to 200 entries.')
            for item in value: inspect(item, depth + 1)
    inspect(document)
    if isinstance(document.get('meta'), dict): document['meta'].pop('output', None)
    node = shutil.which('node')
    if not node: raise ValueError('Archify needs Node.js 18 or newer on the Hermes backend. Mermaid diagrams work without it.')
    kind = document['diagram_type']
    with tempfile.TemporaryDirectory(prefix='learning-archify-') as temp:
        folder = Path(temp); incoming = folder / 'diagram.json'; output = folder / 'diagram.html'
        incoming.write_text(json.dumps(document), encoding='utf-8')
        # Deliberately omit inherited NODE_OPTIONS and Archify filesystem configuration.
        env = {key: os.environ[key] for key in ('PATH', 'SYSTEMROOT', 'WINDIR') if key in os.environ}
        env.update(TMPDIR=temp)
        try:
            result = subprocess.run([node, str(ARCHIFY / 'renderers' / kind / f'render-{kind}.mjs'), str(incoming), str(output)], cwd=temp, env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=12)
        except (OSError, subprocess.TimeoutExpired) as exc: raise ValueError('Archify could not render this diagram within 12 seconds. Simplify the diagram and retry.') from exc
        if result.returncode or not output.is_file():
            detail = result.stderr.decode('utf-8', errors='replace')[:1800].replace(temp, '[temporary directory]')
            raise ValueError('Archify rejected the diagram. Check its schema and layout. ' + detail)
        if output.stat().st_size > 2_000_000: raise ValueError('Archify output is too large. Simplify the diagram.')
        html = output.read_text(encoding='utf-8')
    # Extract the main SVG without executing the viewer. Nested SVGs are balanced.
    start = re.search(r'<svg\s+viewBox=', html)
    if not start: raise ValueError('Archify did not produce an SVG diagram.')
    depth = 0; end = None
    for match in re.finditer(r'</?svg\b[^>]*>', html[start.start():]):
        depth += -1 if match.group().startswith('</') else 1
        if depth == 0: end = start.start() + match.end(); break
    if end is None: raise ValueError('Archify produced an incomplete diagram.')
    svg = html[start.start():end]
    styles = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', html, re.S))
    # SVG is returned solely for <img> rendering: scripts and external loads are disabled by image mode.
    svg = svg.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    at = svg.index('>') + 1
    svg = svg[:at] + '<style>' + escape(styles, quote=False) + '\nsvg{background:var(--bg);font-family:Arial,sans-serif}</style>' + svg[at:]
    return {'mime': 'image/svg+xml', 'data': base64.b64encode(svg.encode()).decode(), 'title': document.get('meta', {}).get('title', 'Archify diagram')}

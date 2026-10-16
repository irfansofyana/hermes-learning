#!/usr/bin/env python3
"""Isolated loopback development preview; this is not a Hermes host adapter."""
import argparse
from http.cookies import SimpleCookie, CookieError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import mimetypes
from pathlib import Path
import secrets
import sys
import tempfile
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
API = '/api/plugins/hermes-learning'
ACTIONS = frozenset(('start', 'resume', 'leave', 'brief', 'approve', 'track_status',
                     'source', 'activity', 'run', 'help', 'submit', 'assess',
                     'dispute', 'review', 'resume_brief', 'recommendation',
                     'recommendation_decide', 'quote_check', 'activity_revision'))
MAX_BODY = 1024 * 1024


def make_server(store, static_root, port, learning_error=ValueError):
    """Create a loopback-only server with an isolated, process-lifetime session."""
    static_root = Path(static_root).resolve()
    session = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            # Request URLs may contain context capabilities. Never log them.
            pass

        def reply(self, status, body, content_type='application/json; charset=utf-8', cookie=False):
            if not isinstance(body, bytes):
                body = json.dumps(body, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            if cookie:
                self.send_header('Set-Cookie', f'hermes_learning_preview={session}; HttpOnly; SameSite=Strict; Path=/')
            self.end_headers()
            self.wfile.write(body)

        def fail(self, status, message):
            self.reply(status, {'error': message})

        def trusted(self, require_session=False, mutation=False):
            host = self.headers.get('Host', '')
            valid_hosts = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
            origin = self.headers.get('Origin')
            if host not in valid_hosts or len(self.headers.get_all('Host', [])) != 1:
                self.fail(403, 'Invalid preview host')
                return False
            if (mutation and not origin) or (origin is not None and origin != f'http://{host}'):
                self.fail(403, 'Same-origin request required')
                return False
            if self.headers.get('Sec-Fetch-Site') not in (None, 'none', 'same-origin'):
                self.fail(403, 'Same-origin request required')
                return False
            if require_session:
                cookie = SimpleCookie()
                try:
                    cookie.load(self.headers.get('Cookie', ''))
                    supplied = cookie.get('hermes_learning_preview')
                    valid = supplied is not None and secrets.compare_digest(supplied.value, session)
                except (CookieError, TypeError):
                    valid = False
                if not valid:
                    self.fail(403, 'Open the preview home page to establish a session')
                    return False
            return True

        def dispatch(self, action, params):
            try:
                self.reply(200, store.dispatch(action, params, channel='ui_direct'))
            except learning_error as exc:
                self.fail(400, str(exc))
            except Exception:
                self.fail(500, 'Preview service failed; no successful result was received')

        def do_GET(self):
            if not self.trusted():
                return
            url = urlsplit(self.path)
            path = unquote(url.path)
            if path.startswith(API + '/'):
                if not self.trusted(require_session=True):
                    return
                route = path[len(API):]
                query = parse_qs(url.query, keep_blank_values=True)
                if route in ('/state', '/export') and not query:
                    return self.dispatch(route[1:], {})
                parts = route.strip('/').split('/')
                if len(parts) == 2 and parts[0] in ('track', 'activity', 'source') and parts[1]:
                    kind, identifier = parts
                    if query and (kind != 'activity' or set(query) != {'context_id'} or len(query['context_id']) != 1):
                        return self.fail(400, 'Unsupported query parameters')
                    action = {'track': 'track', 'activity': 'activity_read', 'source': 'source_read'}[kind]
                    params = {kind + '_id': identifier}
                    if query:
                        params['context_id'] = query['context_id'][0]
                    return self.dispatch(action, params)
                return self.fail(404, 'Unknown preview API route')
            # Limit static files to the built preview. Never serve repository data.
            if path not in ('/', '/index.html', '/preview.js', '/preview.css'):
                return self.fail(404, 'Not found')
            file = (static_root / ('index.html' if path == '/' else path[1:])).resolve()
            if file.parent != static_root or not file.is_file():
                return self.fail(404, 'Build the UI preview first: cd ui && npm run build')
            mime = mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
            self.reply(200, file.read_bytes(), mime + '; charset=utf-8', cookie=path in ('/', '/index.html'))

        def do_POST(self):
            if not self.trusted(require_session=True, mutation=True):
                return
            if self.path != API + '/action':
                return self.fail(404, 'Unknown preview API route')
            if self.headers.get_content_type() != 'application/json':
                return self.fail(415, 'Content-Type must be application/json')
            try:
                if self.headers.get('Transfer-Encoding') or len(self.headers.get_all('Content-Length', [])) != 1:
                    raise ValueError('A single Content-Length is required')
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= MAX_BODY:
                    return self.fail(413, 'Request body is empty or too large')
                payload = json.loads(self.rfile.read(length))
                if type(payload) is not dict or set(payload) != {'action', 'params', 'api_version'}:
                    raise ValueError('Expected action, params, and api_version')
                if type(payload['api_version']) is not int or payload['api_version'] != 1:
                    raise ValueError('Unsupported API version')
                if type(payload['action']) is not str or payload['action'] not in ACTIONS:
                    raise ValueError('Unsupported preview action')
                if type(payload['params']) is not dict:
                    raise ValueError('params must be an object')
            except (ValueError, UnicodeError) as exc:
                return self.fail(400, str(exc))
            self.dispatch(payload['action'], payload['params'])

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8877)
    parser.add_argument('--data-dir', type=Path, help='Isolated preview data directory outside this repository')
    args = parser.parse_args()
    data_dir = (args.data_dir or Path(tempfile.mkdtemp(prefix='hermes-learning-preview-'))).expanduser().resolve()
    daily = (Path.home() / '.hermes').resolve()
    if data_dir == ROOT or ROOT in data_dir.parents or data_dir == daily or daily in data_dir.parents:
        parser.error('Preview data must be outside the repository and ~/.hermes')
    data_dir.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location('hermes_learning_preview_store', ROOT / 'learning_store.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    database = (data_dir / 'learning.sqlite3').resolve()
    if database == ROOT or ROOT in database.parents or database == daily or daily in database.parents:
        parser.error('Preview database must be outside the repository and ~/.hermes')
    store = module.Store(database)
    server = make_server(store, ROOT / 'ui/dist', args.port, module.LearningError)
    print(f'Isolated development preview: http://127.0.0.1:{server.server_port}/', flush=True)
    print(f'Preview data: {data_dir}', flush=True)
    print('This does not verify or modify the real Hermes dashboard, desktop, or messaging hosts.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()

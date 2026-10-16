import http.client
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest

spec = importlib.util.spec_from_file_location('learning_preview', Path(__file__).resolve().parents[1] / 'dev/serve.py')
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class FakeStore:
    def __init__(self):
        self.calls = []

    def dispatch(self, action, params, *, channel):
        self.calls.append((action, params, channel))
        return {'action': action, 'params': params}


class PreviewTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'index.html').write_text('<h1>Preview</h1>')
        (self.root / 'preview.js').write_text('void 0')
        self.store = FakeStore()
        self.server = preview.make_server(self.store, self.root, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = f'http://127.0.0.1:{self.server.server_port}'
        _, headers, _ = self.request('GET', '/')
        self.cookie = headers['Set-Cookie'].split(';')[0]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.directory.cleanup()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        connection.request(method, path, body, headers or {})
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def action(self, payload=None, **headers):
        defaults = {'Cookie': self.cookie, 'Origin': self.origin, 'Content-Type': 'application/json'}
        defaults.update(headers)
        return self.request('POST', preview.API + '/action', json.dumps(payload or {'action': 'start', 'params': {'title': 'Systems'}, 'api_version': 1}), defaults)

    def test_session_and_action(self):
        status, headers, _ = self.request('GET', '/')
        self.assertEqual(status, 200)
        self.assertIn('HttpOnly', headers['Set-Cookie'])
        self.assertIn('SameSite=Strict', headers['Set-Cookie'])
        self.assertEqual(self.action()[0], 200)
        self.assertEqual(self.store.calls[-1], ('start', {'title': 'Systems'}, 'ui_direct'))

    def test_cookie_origin_and_host_required(self):
        for headers in [{'Cookie': ''}, {'Origin': ''}, {'Origin': 'https://evil.example'}, {'Host': 'evil.example'}, {'Sec-Fetch-Site': 'cross-site'}]:
            self.assertEqual(self.action(**headers)[0], 403)
        self.assertFalse(self.store.calls)
        self.assertEqual(self.request('GET', preview.API + '/state')[0], 403)

    def test_strict_action_envelope(self):
        for payload in [{'action': 'backup', 'params': {}, 'api_version': 1}, {'action': 'start', 'params': {}, 'api_version': True}, {'action': 'start', 'params': [] , 'api_version': 1}]:
            self.assertEqual(self.action(payload)[0], 400)
        self.assertFalse(self.store.calls)

    def test_read_routes_and_traversal(self):
        headers = {'Cookie': self.cookie}
        for path, action, params in [('/state', 'state', {}), ('/track/t1', 'track', {'track_id': 't1'}), ('/activity/a1?context_id=c1', 'activity_read', {'activity_id': 'a1', 'context_id': 'c1'}), ('/source/s1', 'source_read', {'source_id': 's1'}), ('/export', 'export', {})]:
            self.assertEqual(self.request('GET', preview.API + path, headers=headers)[0], 200)
            self.assertEqual(self.store.calls[-1], (action, params, 'ui_direct'))
        self.assertEqual(self.request('GET', '/%2e%2e/README.md')[0], 404)
        self.assertEqual(self.request('GET', '/index.html', headers={'Host': 'evil.example'})[0], 403)


if __name__ == '__main__':
    unittest.main()

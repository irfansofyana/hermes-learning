import base64
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch
import runtime


def png(width=1, height=1):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b'\x00\x00\x00\x00')) + chunk(b'IEND', b'')


class LessonMediaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = runtime.Store(self.root / 'learning.db')
        self.addCleanup(patch.stopall)
        patch.object(runtime, 'store', return_value=self.store).start()
        self.start = self.call('course_start', request_id='one', title='Queues', intent='topic', level='beginner', materials=[])
        self.image = self.root / 'diagram.png'; self.image.write_bytes(png())

    def call(self, action, channel='ui_direct', **params):
        return runtime.action(action, params, channel=channel)

    def attach(self, **extra):
        return self.call('course_asset_import', channel='chat_relayed', context_id=self.start['context_id'], path=str(self.image), title='Queue diagram', **extra)

    def test_import_is_durable_idempotent_and_track_scoped(self):
        saved = self.attach()
        self.assertEqual(saved, self.attach())
        self.assertIn('learning-asset:', saved['markdown'])
        self.store = runtime.Store(self.root / 'learning.db')
        patch.object(runtime, 'store', return_value=self.store).start()
        result = self.call('course_asset_read', track_id=self.start['track_id'], asset_id=saved['asset']['id'])
        self.assertEqual(base64.b64decode(result['data']), png())
        other = self.call('course_start', request_id='two', title='Other', intent='topic', level='beginner', materials=[])
        with self.assertRaises(runtime.LearningError):
            self.call('course_asset_read', track_id=other['track_id'], asset_id=saved['asset']['id'])
        with self.assertRaises(runtime.LearningError):
            self.call('course_asset_read', channel='chat_relayed', track_id=self.start['track_id'], asset_id=saved['asset']['id'])
        with self.assertRaises(runtime.LearningError):
            self.call('course_asset_import', context_id=self.start['context_id'], path=str(self.image), title='No browser file access')

    def test_rejects_fake_images_symlinks_and_large_dimensions(self):
        for content in [b'<svg onload="alert(1)"></svg>', b'not an image', png(99999, 1)]:
            self.image.write_bytes(content)
            with self.assertRaises(runtime.LearningError): self.attach()
        self.image.write_bytes(png()); link = self.root / 'link.png'; link.symlink_to(self.image)
        with self.assertRaises(runtime.LearningError):
            self.call('course_asset_import', channel='chat_relayed', context_id=self.start['context_id'], path=str(link), title='Symlink')

    def test_publishing_and_proposals_reject_foreign_or_missing_assets(self):
        self.call('course_plan', channel='chat_relayed', context_id=self.start['context_id'], job_id=self.start['job_id'], summary='Learn', assumptions=[], lessons=[{'key':'one','title':'Queues','goal':'Understand'}])
        args=dict(context_id=self.start['context_id'],job_id=self.start['job_id'],lesson_key='one',source_ids=[])
        with self.assertRaises(runtime.LearningError):
            self.call('course_lesson',channel='chat_relayed',content='![Missing](learning-asset:missing)',**args)
        saved=self.attach()
        lesson=self.call('course_lesson',channel='chat_relayed',content='Queue explanation.\n\n'+saved['markdown'],**args)
        self.assertIn(saved['asset']['id'],lesson['lesson']['content'])
        with self.assertRaises(runtime.LearningError):
            self.call('course_propose',channel='chat_relayed',context_id=self.start['context_id'],request_id='bad',base_revision=1,mode='revise',summary='Image',lessons=[{'lesson_key':'one','content':'![Missing](learning-asset:missing)','source_ids':[]}])

    def test_archify_requires_context_and_rejects_external_resources(self):
        import json
        for source in [{'diagram_type':'unsupported'}, {'diagram_type':'architecture','meta':{'title':'x'},'components':[{'brand':{'url':'https://example.com','sha256':'a'}}]}, {'diagram_type':'architecture','repository':{'path':'/tmp'}}]:
            with self.assertRaises(runtime.LearningError):
                self.call('course_diagram_render',context_id=self.start['context_id'],source=json.dumps(source))

    def test_all_archify_types_render_with_bundled_runtime(self):
        import json
        for file in (Path(__file__).parent / 'fixtures' / 'archify').glob('*.json'):
            with self.subTest(file=file.name):
                result = self.call('course_diagram_render', context_id=self.start['context_id'], source=file.read_text())
                self.assertEqual(result['mime'], 'image/svg+xml')
                svg = base64.b64decode(result['data']).decode()
                __import__('xml.etree.ElementTree', fromlist=['fromstring']).fromstring(svg)
                self.assertIn('<svg', svg)
                self.assertIn('<style>', svg)
                self.assertNotIn('<script', svg)

    def test_archify_missing_node_is_actionable(self):
        source = (Path(__file__).parent / 'fixtures' / 'archify' / 'web-app.architecture.json').read_text()
        with patch.object(runtime._module._media.shutil, 'which', return_value=None):
            with self.assertRaisesRegex(runtime.LearningError, 'Node.js 18'):
                self.call('course_diagram_render', context_id=self.start['context_id'], source=source)

    def test_assets_cannot_be_published_into_another_path(self):
        saved = self.attach()
        other = self.call('course_start', request_id='other', title='Other', intent='topic', level='beginner', materials=[])
        self.call('course_plan', channel='chat_relayed', context_id=other['context_id'], job_id=other['job_id'], summary='Other', assumptions=[], lessons=[{'key':'one','title':'Other','goal':'Learn'}])
        with self.assertRaises(runtime.LearningError):
            self.call('course_lesson', channel='chat_relayed', context_id=other['context_id'], job_id=other['job_id'], lesson_key='one', content=saved['markdown'], source_ids=[])

    def test_asset_bytes_survive_database_backup_and_invalid_context_cannot_import(self):
        saved = self.attach()
        backup = self.root / 'copy.db'; self.store.backup(backup)
        copy = runtime.Store(backup)
        image = copy.dispatch('course_asset_read', {'track_id':self.start['track_id'], 'asset_id':saved['asset']['id']})
        self.assertEqual(base64.b64decode(image['data']), png())
        self.call('leave', context_id=self.start['context_id'])
        with self.assertRaises(runtime.LearningError): self.attach()

    def test_image_quota_and_oversized_file_are_rejected(self):
        self.image.write_bytes(b'x' * (5 * 1024 * 1024 + 1))
        with self.assertRaisesRegex(runtime.LearningError, '5 MB'): self.attach()
        self.image.write_bytes(png())
        for index in range(50):
            self.call('course_asset_import', channel='chat_relayed', context_id=self.start['context_id'], path=str(self.image), title=f'Image {index}')
        with self.assertRaisesRegex(runtime.LearningError, 'limit'): self.attach()

    def test_archify_timeout_is_bounded_and_returns_actionable_error(self):
        import subprocess
        source = (Path(__file__).parent / 'fixtures' / 'archify' / 'web-app.architecture.json').read_text()
        with patch.object(runtime._module._media.subprocess, 'run', side_effect=subprocess.TimeoutExpired('node', 12)):
            with self.assertRaisesRegex(runtime.LearningError, '12 seconds'):
                self.call('course_diagram_render', context_id=self.start['context_id'], source=source)

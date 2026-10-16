import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SPEC = importlib.util.spec_from_file_location('learning_packager', Path(__file__).resolve().parents[1] / 'dev/package.py')
packager = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packager)


class PackageTests(unittest.TestCase):
    def test_repository_root_is_an_installable_release(self):
        # The Git installer inspects the clone root, not a nested plugin/ folder.
        contents = packager.collect(Path(__file__).resolve().parents[1])
        with tempfile.TemporaryDirectory() as output:
            combined, _ = packager.package(output=output)
            with zipfile.ZipFile(combined) as archive:
                self.assertEqual(archive.read('hermes-learning/__init__.py'), contents['__init__.py'])
                self.assertEqual(archive.read('hermes-learning/desktop/plugin.js'), contents['desktop/plugin.js'])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'plugin'
        for relative in packager.FILES:
            file = self.source / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('fixture\n')
        (self.source / 'plugin.yaml').write_text('name: hermes-learning\nversion: "0.1.0"\n')
        (self.source / 'dashboard/manifest.json').write_text(json.dumps({
            'name': 'hermes-learning', 'version': '0.1.0', 'entry': 'dist/index.js', 'api': 'plugin_api.py'}))
        (self.source / 'desktop/package.json').write_text('{"type":"module"}')

    def test_exact_contents_and_deterministic_checksums(self):
        for relative in ('.env', 'data.db', '__pycache__/runtime.pyc', 'skills/secret.md', 'dashboard/private.json'):
            file = self.source / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('must not ship')
        first = packager.package(self.source, self.root / 'one')
        second = packager.package(self.source, self.root / 'two')
        self.assertEqual([p.name for p in first], ['hermes-learning-0.1.0.zip', 'hermes-learning-desktop-0.1.0.zip'])
        for a, b in zip(first, second):
            self.assertEqual(a.read_bytes(), b.read_bytes())
        with zipfile.ZipFile(first[0]) as archive:
            self.assertEqual(set(archive.namelist()), {'hermes-learning/' + f for f in packager.FILES})
        with zipfile.ZipFile(first[1]) as archive:
            self.assertEqual(set(archive.namelist()), {'hermes-learning/plugin.js', 'hermes-learning/package.json'})
        self.assertEqual((self.root / 'one/SHA256SUMS').read_bytes(), (self.root / 'two/SHA256SUMS').read_bytes())

    def test_missing_build_fails_before_output(self):
        (self.source / 'desktop/plugin.js').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing required artifact'):
            packager.package(self.source, self.root / 'out')
        self.assertFalse((self.root / 'out').exists())

    def test_manifest_mismatch_rejected(self):
        (self.source / 'dashboard/manifest.json').write_text('{"name":"different"}')
        with self.assertRaisesRegex(ValueError, 'Dashboard name'):
            packager.collect(self.source)
        (self.source / 'plugin.yaml').write_text('name: hermes-learning\nversion: 9.0.0\n')
        with self.assertRaisesRegex(ValueError, 'version'):
            packager.collect(self.source)

    def test_symlink_file_and_directory_rejected(self):
        external = self.root / 'outside.js'
        external.write_text('private fixture')
        entry = self.source / 'desktop/plugin.js'
        entry.unlink()
        entry.symlink_to(external)
        with self.assertRaisesRegex(ValueError, 'Symlinks'):
            packager.collect(self.source)
        entry.unlink()
        entry.write_text('fixture')
        directory = self.source / 'desktop'
        directory.rename(self.root / 'outside')
        directory.symlink_to(self.root / 'outside', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlinks'):
            packager.collect(self.source)


if __name__ == '__main__':
    unittest.main()

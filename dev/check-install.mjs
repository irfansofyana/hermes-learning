// Exercise the actual Hermes Git installer without touching an installed profile.
// Usage: node dev/check-install.mjs /path/to/hermes-agent [repository-url]
import assert from 'node:assert/strict';
import {mkdtemp, readFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join, resolve} from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {build} from '../ui/node_modules/esbuild/lib/main.js';

const host = process.argv[2];
if (!host) throw new Error('Pass the path to an existing Hermes Agent checkout.');
const repository = fileURLToPath(new URL('..', import.meta.url));
const temporary = await mkdtemp(join(tmpdir(), 'hermes-learning-install-check-'));
try {
  const bundle = join(temporary, 'installer.cjs');
  await build({
    entryPoints: [resolve(host, 'apps/desktop/electron/desktop-plugin-install.ts')],
    outfile: bundle, bundle: true, platform: 'node', format: 'cjs', packages: 'external'
  });
  const installer = createRequire(import.meta.url)(bundle);
  const local = await installer.detectPluginComponents(repository);
  assert.equal(local.agent, true, 'The repository root must expose the agent plugin.');
  assert.equal(local.desktop, true, 'The repository root must expose the desktop plugin.');
  assert.equal(local.agentName, 'hermes-learning');
  assert.equal(local.desktopSourceSubdir, 'desktop');
  const result = {local: {agent: local.agent, desktop: local.desktop, name: local.agentName}};
  const url = process.argv[3];
  if (url) {
    const probe = await installer.probePluginRepo('git', url);
    assert.equal(probe.ok, true, probe.error);
    assert.equal(probe.agent, true);
    assert.equal(probe.desktop, true);
    assert.equal(probe.agentName, 'hermes-learning');
    assert.equal(probe.desktopName, 'hermes-learning');
    const installed = await installer.installDesktopPluginFromGit('git', url, join(temporary, 'desktop-plugins'));
    assert.equal(installed.ok, true, installed.error);
    assert.equal(installed.pluginName, 'hermes-learning');
    assert.deepEqual(await readFile(join(installed.path, 'plugin.js')), await readFile(join(repository, 'desktop/plugin.js')));
    result.remote = {probe: 'passed', desktopInstall: 'passed', name: installed.pluginName};
  }
  console.log(JSON.stringify(result, null, 2));
} finally {
  await rm(temporary, {recursive: true, force: true});
}

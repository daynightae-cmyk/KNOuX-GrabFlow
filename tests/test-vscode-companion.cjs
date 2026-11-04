'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const Module = require('node:module');

const root = path.resolve(__dirname, '..');
const vscodeDir = path.join(root, 'vscode-companion');
const pkgPath = path.join(vscodeDir, 'package.json');
const extPath = path.join(vscodeDir, 'extension.js');
const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));

function vscodeStub() {
  const commands = new Map();
  const clipboard = [];
  const context = { subscriptions: [] };
  const channel = {
    appendLine() {}, append() {}, show() {}, dispose() {}
  };
  return {
    commands,
    clipboard,
    context,
    api: {
      commands: {
        registerCommand(id, handler) {
          commands.set(id, handler);
          return { dispose() {} };
        }
      },
      window: {
        createOutputChannel: () => channel,
        showInputBox: async () => undefined,
        showSaveDialog: async () => undefined,
        showErrorMessage() {},
        showWarningMessage() {},
        showInformationMessage() {}
      },
      workspace: {
        getConfiguration: () => ({ get: (_key, fallback) => fallback }),
        workspaceFolders: []
      },
      Uri: {
        joinPath: (folder, name) => ({ fsPath: path.join(folder.fsPath, name) })
      },
      env: {
        clipboard: { writeText: async text => clipboard.push(text) }
      }
    }
  };
}

function loadExtension(stub) {
  const originalLoad = Module._load;
  Module._load = function (request, parent, isMain) {
    if (request === 'vscode') return stub.api;
    return originalLoad.call(this, request, parent, isMain);
  };
  try {
    delete require.cache[require.resolve(extPath)];
    return require(extPath);
  } finally {
    Module._load = originalLoad;
  }
}

const tests = [];
function test(name, fn) { tests.push([name, fn]); }

test('vscode-companion metadata is complete and version-aligned', () => {
  assert.equal(pkg.name, 'knoux-grabflow-vscode');
  assert.equal(pkg.version, '0.6.7');
  assert.equal(pkg.publisher, 'knoux-labs');
  assert.ok(pkg.engines?.vscode);
  assert.equal(pkg.icon, 'media/icon.png');
  assert.equal(pkg.license, 'SEE LICENSE IN LICENSE.txt');
  assert.equal(pkg.homepage, 'https://github.com/daynightae-cmyk');
  assert.match(pkg.repository?.url || '', /KNOuX-GrabFlow/);
  assert.ok(Array.isArray(pkg.keywords) && pkg.keywords.length >= 5);
  assert.equal(pkg.capabilities?.untrustedWorkspaces?.supported, false);
  for (const file of [
    'extension.js', 'companion/assemble_stream.py', 'companion/companion_host.py',
    'media/icon.png', 'README.md', 'CHANGELOG.md', 'LICENSE.txt'
  ]) {
    assert.ok(pkg.files.includes(file), `files metadata must include ${file}`);
  }
  assert.ok(Array.isArray(pkg.activationEvents));
  assert.equal(pkg.contributes.commands.length, 3);
  const settings = pkg.contributes.configuration.properties;
  for (const key of [
    'knouxGrabflow.ffmpegPath', 'knouxGrabflow.ffprobePath',
    'knouxGrabflow.pythonPath', 'knouxGrabflow.companionScriptPath'
  ]) {
    assert.ok(settings[key], `missing setting ${key}`);
  }
});

test('runtime metadata files exist and declare the same version', () => {
  for (const file of ['README.md', 'CHANGELOG.md', 'LICENSE.txt', 'media/icon.png']) {
    assert.ok(fs.existsSync(path.join(vscodeDir, file)), file);
  }
  const changelog = fs.readFileSync(path.join(vscodeDir, 'CHANGELOG.md'), 'utf8');
  assert.match(changelog, /## 0\.6\.7/);
  const readme = fs.readFileSync(path.join(vscodeDir, 'README.md'), 'utf8');
  assert.match(readme, /not published on the VS Code Marketplace/i);
  assert.match(readme, /Python 3\.8\+/);
  assert.doesNotMatch(readme, /Zero External Dependencies/i);
});

test('extension source bundles and resolves the companion safely', () => {
  const code = fs.readFileSync(extPath, 'utf8');
  assert.ok(code.includes('function activate'));
  assert.ok(code.includes('function deactivate'));
  assert.ok(code.includes('module.exports'));
  for (const command of [
    'knouxGrabflow.inspectMedia',
    'knouxGrabflow.assembleStream',
    'knouxGrabflow.generateFfmpegCommand'
  ]) {
    assert.ok(code.includes(command), command);
  }
  assert.ok(code.includes("path.join(__dirname, 'companion', 'assemble_stream.py')"));
  assert.ok(code.includes("path.resolve(__dirname, '..', 'scripts', 'assemble_stream.py')"));
  assert.ok(code.includes('companion_host.py'));
  assert.ok(code.includes('showSaveDialog'));
  assert.ok(code.includes("'--ffmpeg', ffmpeg"));
  assert.ok(code.includes('cwd: path.dirname(outputPath)'));
  assert.ok(code.includes('isSymbolicLink'));
  assert.doesNotMatch(code, /shell\s*:\s*true/i);
});

test('companion resolver prefers an explicit absolute script, then the repository', () => {
  const extension = loadExtension(vscodeStub());
  const repoScript = path.join(root, 'scripts', 'assemble_stream.py');
  const config = value => ({ get: (_key, fallback) => value === undefined ? fallback : value });

  assert.equal(extension._test.resolveCompanionScript(config('')), repoScript);
  assert.equal(extension._test.resolveCompanionScript(config('scripts/assemble_stream.py')), repoScript);

  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'knoux-vscode-'));
  try {
    const script = path.join(temp, 'assemble_stream.py');
    const host = path.join(temp, 'companion_host.py');
    fs.writeFileSync(script, '# staged helper\n');
    fs.writeFileSync(host, '# staged audit module\n');
    assert.equal(extension._test.resolveCompanionScript(config(script)), script);
    fs.rmSync(host);
    assert.equal(extension._test.resolveCompanionScript(config(script)), null);
  } finally {
    fs.rmSync(temp, { recursive: true, force: true });
  }
});

test('mock-host activation registers all three commands', async () => {
  const stub = vscodeStub();
  const extension = loadExtension(stub);
  extension.activate(stub.context);
  assert.deepEqual([...stub.commands.keys()].sort(), [
    'knouxGrabflow.assembleStream',
    'knouxGrabflow.generateFfmpegCommand',
    'knouxGrabflow.inspectMedia'
  ]);
  const text = await new Promise(resolve => {
    const original = stub.api.window.showInputBox;
    stub.api.window.showInputBox = async () => 'https://example.com/live.m3u8';
    stub.commands.get('knouxGrabflow.generateFfmpegCommand')().then(() => {
      stub.api.window.showInputBox = original;
      resolve(stub.clipboard[0]);
    });
  });
  assert.match(text, /^ffmpeg -hide_banner -nostdin -i /);
  assert.match(text, /https:\/\/example\.com\/live\.m3u8/);
  assert.match(text, /-c copy -movflags \+faststart/);
  extension.deactivate();
});

(async () => {
  let passed = 0;
  for (const [name, fn] of tests) {
    try {
      await fn();
      console.log('PASS', name);
      passed++;
    } catch (error) {
      console.error('FAIL', name);
      throw error;
    }
  }
  console.log(`${passed} VS Code companion contract checks passed.`);
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});

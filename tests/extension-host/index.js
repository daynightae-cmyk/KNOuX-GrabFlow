'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vscode = require('vscode');

async function run() {
  const extension = vscode.extensions.getExtension('knoux-labs.knoux-grabflow-vscode');
  assert.ok(extension, 'KNOuX GrabFlow extension was not discovered by the extension host');
  assert.equal(extension.packageJSON.version, '0.6.7');
  assert.equal(extension.packageJSON.publisher, 'knoux-labs');
  assert.ok(extension.extensionPath, 'extension path is missing');

  await extension.activate();
  assert.equal(extension.isActive, true, 'activation did not complete');

  const expected = [
    'knouxGrabflow.inspectMedia',
    'knouxGrabflow.assembleStream',
    'knouxGrabflow.generateFfmpegCommand',
  ];
  const commands = await vscode.commands.getCommands(true);
  for (const id of expected) {
    assert.ok(commands.includes(id), `missing registered command: ${id}`);
  }

  const helper = path.join(extension.extensionPath, 'companion', 'assemble_stream.py');
  const audit = path.join(extension.extensionPath, 'companion', 'companion_host.py');
  assert.ok(fs.existsSync(helper), 'bundled assemble_stream.py is missing');
  assert.ok(fs.existsSync(audit), 'bundled companion_host.py is missing');

  const loaded = require(path.join(extension.extensionPath, 'extension.js'));
  const resolved = loaded._test.resolveCompanionScript({ get: (_key, fallback) => fallback });
  assert.equal(resolved, helper, 'extension did not prefer the bundled helper');
  assert.ok(loaded._test.ffmpegCandidates().length > 0);

  console.log('EXTENSION_HOST_ACTIVATION_PASS', extension.id, extension.packageJSON.version);
  console.log('EXTENSION_HOST_BUNDLED_HELPER', helper);
  console.log('EXTENSION_HOST_COMMANDS', expected.join(','));
}

module.exports = { run };

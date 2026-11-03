'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const vscodeDir = path.join(root, 'vscode-companion');
const pkgPath = path.join(vscodeDir, 'package.json');
const extPath = path.join(vscodeDir, 'extension.js');

let passed = 0;
function test(name, fn) { fn(); console.log('PASS', name); passed++; }

test('vscode-companion package.json exists and is valid', () => {
  assert.ok(fs.existsSync(pkgPath));
  const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
  assert.equal(pkg.name, 'knoux-grabflow-vscode');
  assert.equal(pkg.version, '0.6.0');
  assert.ok(pkg.engines?.vscode);
  assert.ok(Array.isArray(pkg.activationEvents));
  assert.ok(Array.isArray(pkg.contributes?.commands));
  assert.equal(pkg.contributes.commands.length, 3);
});

test('vscode-companion extension.js exists and exports activate/deactivate', () => {
  assert.ok(fs.existsSync(extPath));
  const code = fs.readFileSync(extPath, 'utf8');
  assert.ok(code.includes('function activate'));
  assert.ok(code.includes('function deactivate'));
  assert.ok(code.includes('module.exports'));
  assert.ok(code.includes('knouxGrabflow.inspectMedia'));
  assert.ok(code.includes('knouxGrabflow.assembleStream'));
  assert.ok(code.includes('knouxGrabflow.generateFfmpegCommand'));
});

console.log(`${passed} VS Code companion contract checks passed.`);

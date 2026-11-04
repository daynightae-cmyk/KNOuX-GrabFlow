'use strict';
/**
 * Run the packaged VSIX in a real VS Code extension host.
 *
 * This is intentionally outside the extension bundle: it extracts the VSIX,
 * downloads/caches VS Code through @vscode/test-electron, and asks the real host
 * to activate the packaged extension. It is not a Marketplace publication test.
 */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

const root = path.resolve(__dirname, '..');

function findVsix() {
  const dist = path.join(root, 'dist');
  const candidates = fs.existsSync(dist)
    ? fs.readdirSync(dist).filter(name => /^KNOuX-GrabFlow-VSCODE-v\d+\.\d+\.\d+\.vsix$/.test(name))
    : [];
  if (candidates.length !== 1) {
    throw new Error(`Expected exactly one VSIX in ${dist}, found: ${candidates.join(', ') || 'none'}`);
  }
  return path.join(dist, candidates[0]);
}

async function main() {
  let runTests;
  try {
    ({ runTests } = require('@vscode/test-electron'));
  } catch (error) {
    console.error('BLOCKED: @vscode/test-electron is not installed in this environment.');
    console.error('Install it outside the repository, then set NODE_PATH to its node_modules:');
    console.error('  npm install --prefix <test-runner-dir> @vscode/test-electron@3.1.0');
    throw error;
  }

  const vsix = findVsix();
  const stage = fs.mkdtempSync(path.join(os.tmpdir(), 'knoux-vsix-extract-'));
  try {
    const extract = 'import sys, zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])';
    execFileSync(process.env.PYTHON || 'python', ['-c', extract, vsix, stage], { stdio: 'inherit' });
    const developmentPath = path.join(stage, 'extension');
    if (!fs.existsSync(path.join(developmentPath, 'package.json'))) {
      throw new Error(`VSIX did not contain extension/package.json: ${vsix}`);
    }
    console.log('EXTENSION_HOST_VSIX', vsix);
    await runTests({
      version: process.env.VSCODE_TEST_VERSION || 'stable',
      cachePath: process.env.VSCODE_TEST_CACHE || path.join(os.tmpdir(), 'knoux-vscode-test-cache'),
      extensionDevelopmentPath: developmentPath,
      extensionTestsPath: path.join(root, 'tests', 'extension-host', 'index.js'),
      launchArgs: [
        '--disable-extensions',
        '--skip-welcome',
        '--skip-release-notes',
        '--disable-workspace-trust',
      ],
    });
    console.log('EXTENSION_HOST_PASS');
  } finally {
    fs.rmSync(stage, { recursive: true, force: true });
  }
}

main().catch(error => {
  console.error(error?.stack ?? error);
  process.exitCode = 1;
});

'use strict';
/**
 * KNOuX GrabFlow — VS Code Companion Extension.
 *
 * Provides developer and media engineering tools for inspecting HLS/DASH streams,
 * generating safe FFmpeg commands, and launching bundled companion stream assembly.
 * No npm runtime dependencies; uses an absolute local Python and FFmpeg/FFprobe,
 * and never a shell.
 */

const vscode = require('vscode');
const fs = require('fs');
const path = require('path');
const { execFile, spawn } = require('child_process');

let outputChannel = null;

function isExecutableFile(candidate) {
  if (!candidate || typeof candidate !== 'string') return false;
  try {
    return fs.statSync(candidate).isFile();
  } catch (_) {
    return false;
  }
}

/** Newest Python under a Windows-style install root, if one exists. */
function pythonUnderRoot(root) {
  if (!root) return null;
  try {
    const versions = fs.readdirSync(root, { withFileTypes: true })
      .filter(entry => entry.isDirectory() && /^Python3\d+$/i.test(entry.name))
      .map(entry => path.join(root, entry.name, 'python.exe'))
      .sort()
      .reverse();
    return versions.find(isExecutableFile) || null;
  } catch (_) {
    return null;
  }
}

/**
 * Resolve an interpreter or tool to an absolute path.
 *
 * A bare name is looked up on the host first, so the child never has to inherit
 * the caller's PATH to find it. If nothing absolute exists we refuse rather than
 * spawning something that only resolves through whatever PATH happens to be set,
 * which is how a planted binary earlier in PATH gets executed.
 */
function resolveTool(configured, candidates, label) {
  if (configured && path.isAbsolute(configured) && isExecutableFile(configured)) {
    return configured;
  }
  for (const candidate of candidates) {
    if (isExecutableFile(candidate)) return candidate;
  }
  const viaPath = (process.env.PATH || '').split(path.delimiter)
    .filter(Boolean)
    .map(directory => path.join(directory, configured || ''))
    .find(isExecutableFile);
  if (viaPath) return viaPath;
  throw new Error(
    `${label} could not be located as an absolute path. Set knouxGrabflow.pythonPath / ` +
    `knouxGrabflow.ffprobePath to an absolute file in Settings.`);
}

function pythonCandidates() {
  if (process.platform === 'win32') {
    const roots = [process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, 'Programs', 'Python'),
                   process.env.ProgramFiles && path.join(process.env.ProgramFiles, 'Python'),
                   process.env['ProgramFiles(x86)'] && path.join(process.env['ProgramFiles(x86)'], 'Python')];
    return roots.map(pythonUnderRoot).filter(Boolean);
  }
  return ['/usr/bin/python3', '/usr/local/bin/python3', '/opt/homebrew/bin/python3'];
}

/** Common absolute FFmpeg locations, checked before the parent PATH. */
function ffmpegCandidates() {
  if (process.platform === 'win32') {
    const local = process.env.LOCALAPPDATA;
    const profile = process.env.USERPROFILE;
    return [
      local && path.join(local, 'Programs', 'ffmpeg', 'bin', 'ffmpeg.exe'),
      local && path.join(local, 'Microsoft', 'WinGet', 'Links', 'ffmpeg.exe'),
      process.env.ProgramFiles && path.join(process.env.ProgramFiles, 'ffmpeg', 'bin', 'ffmpeg.exe'),
      'C:\\ffmpeg\\bin\\ffmpeg.exe',
      'C:\\ProgramData\\chocolatey\\bin\\ffmpeg.exe',
      profile && path.join(profile, 'scoop', 'apps', 'ffmpeg', 'current', 'bin', 'ffmpeg.exe'),
    ].filter(Boolean);
  }
  return ['/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg', '/opt/homebrew/bin/ffmpeg'];
}

/**
 * Resolve assemble_stream.py without ever relying on the extension host's cwd.
 *
 * Order: explicit absolute setting -> script bundled in the VSIX -> repository
 * checkout used during development. companion_host.py must sit beside it because
 * the CLI delegates its nested-reference audit to that module.
 */
function resolveCompanionScript(config) {
  const configured = String(config.get('companionScriptPath', '') || '').trim();
  const candidates = [];
  if (configured && path.isAbsolute(configured)) candidates.push(configured);
  candidates.push(path.join(__dirname, 'companion', 'assemble_stream.py'));
  candidates.push(path.resolve(__dirname, '..', 'scripts', 'assemble_stream.py'));
  const script = candidates.find(candidate =>
    path.basename(candidate).toLowerCase() === 'assemble_stream.py' && isExecutableFile(candidate));
  if (!script) return null;
  return isExecutableFile(path.join(path.dirname(script), 'companion_host.py')) ? script : null;
}

/**
 * Environment for a child process: a fixed PATH containing only the tool's own
 * directory, plus the handful of variables Python and FFmpeg genuinely need.
 */
function childEnvironment(executablePath) {
  const environment = { PATH: path.dirname(executablePath) };
  for (const key of ['SYSTEMROOT', 'SystemRoot', 'WINDIR', 'TEMP', 'TMP', 'HOME', 'USERPROFILE',
                     'LANG', 'LC_ALL', 'PYTHONIOENCODING']) {
    if (process.env[key]) environment[key] = process.env[key];
  }
  return environment;
}

function getChannel() {
  if (!outputChannel) {
    outputChannel = vscode.window.createOutputChannel('KNOuX GrabFlow');
  }
  return outputChannel;
}

function activate(context) {
  const channel = getChannel();
  channel.appendLine('KNOuX GrabFlow Companion Extension activated.');

  // Command 1: Inspect Stream / Media URL
  const inspectCmd = vscode.commands.registerCommand('knouxGrabflow.inspectMedia', async () => {
    const url = await vscode.window.showInputBox({
      prompt: 'Enter HLS (.m3u8), DASH (.mpd), or direct media URL',
      placeHolder: 'https://example.com/stream.m3u8'
    });
    if (!url || !url.trim()) return;

    const trimmed = url.trim();
    channel.show(true);
    channel.appendLine(`\n[INSPECT] Probing URL: ${trimmed}`);

    const isHls = /\.m3u8(?:[?#]|$)/i.test(trimmed);
    const isDash = /\.mpd(?:[?#]|$)/i.test(trimmed);
    channel.appendLine(`Detected Format: ${isHls ? 'HLS (m3u8)' : (isDash ? 'DASH (mpd)' : 'Direct Video/Audio')}`);

    const config = vscode.workspace.getConfiguration('knouxGrabflow');
    const configuredProbe = config.get('ffprobePath', 'ffprobe');
    let ffprobe;
    try {
      ffprobe = resolveTool(configuredProbe,
        [path.join(path.dirname(configuredProbe), 'ffprobe.exe')], 'ffprobe');
    } catch (resolveError) {
      channel.appendLine(`[PROBE ERROR] ${resolveError.message}`);
      vscode.window.showErrorMessage(resolveError.message);
      return;
    }

    execFile(ffprobe, [
      '-hide_banner', '-loglevel', 'error',
      '-show_entries', 'stream=index,codec_name,codec_type,width,height,bit_rate:format=duration,format_name',
      '-of', 'json', trimmed
    ], { timeout: 15000, env: childEnvironment(ffprobe) }, (error, stdout, stderr) => {
      if (error) {
        channel.appendLine(`[PROBE ERROR] ${stderr || error.message}`);
        vscode.window.showWarningMessage(`Could not probe stream with ffprobe. Format classified as ${isHls ? 'HLS' : (isDash ? 'DASH' : 'Direct')}.`);
        return;
      }
      try {
        const data = JSON.parse(stdout);
        channel.appendLine('[STREAM DETAILS]');
        channel.appendLine(JSON.stringify(data, null, 2));
        vscode.window.showInformationMessage(`Stream probed successfully: ${data.streams ? data.streams.length : 0} tracks found.`);
      } catch (_) {
        channel.appendLine(stdout);
      }
    });
  });

  // Command 2: Assemble HLS/DASH Stream via Companion
  const assembleCmd = vscode.commands.registerCommand('knouxGrabflow.assembleStream', async () => {
    const url = await vscode.window.showInputBox({
      prompt: 'Enter direct HLS (.m3u8) or DASH (.mpd) playlist URL',
      placeHolder: 'https://example.com/master.m3u8'
    });
    if (!url || !url.trim()) return;

    const workspaceFolder = vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders[0];
    const defaultUri = workspaceFolder
      ? vscode.Uri.joinPath(workspaceFolder.uri, 'output.mp4')
      : undefined;
    const outputUri = await vscode.window.showSaveDialog({
      saveLabel: 'Assemble stream',
      filters: { 'MP4 video': ['mp4'], 'Matroska video': ['mkv'] },
      defaultUri,
    });
    if (!outputUri) return;
    const outputPath = outputUri.fsPath;
    if (!/\.(mp4|mkv)$/i.test(outputPath)) {
      vscode.window.showErrorMessage('Output filename must end in .mp4 or .mkv.');
      return;
    }

    const config = vscode.workspace.getConfiguration('knouxGrabflow');
    const scriptPath = resolveCompanionScript(config);
    if (!scriptPath) {
      const message = 'The companion helper (assemble_stream.py + companion_host.py) was not found. ' +
        'Reinstall the extension or set knouxGrabflow.companionScriptPath.';
      channel.appendLine(`[ASSEMBLE ERROR] ${message}`);
      vscode.window.showErrorMessage(message);
      return;
    }

    channel.show(true);
    channel.appendLine(`\n[ASSEMBLE] Launching companion assembly: ${url.trim()} -> ${outputPath}`);

    let python;
    let ffmpeg;
    try {
      python = resolveTool(config.get('pythonPath', ''), pythonCandidates(), 'Python');
      ffmpeg = resolveTool(config.get('ffmpegPath', 'ffmpeg'), ffmpegCandidates(), 'FFmpeg');
      if (fs.lstatSync(ffmpeg).isSymbolicLink()) {
        throw new Error('FFmpeg resolves to a symbolic link. Set knouxGrabflow.ffmpegPath ' +
          'to the real absolute executable; the companion refuses symlinked FFmpeg.');
      }
    } catch (resolveError) {
      channel.appendLine(`[ASSEMBLE ERROR] ${resolveError.message}`);
      vscode.window.showErrorMessage(resolveError.message);
      return;
    }

    const proc = spawn(python, [
      scriptPath,
      '--url', url.trim(),
      '--output', outputPath,
      '--ffmpeg', ffmpeg
    ], { env: childEnvironment(python), windowsHide: true, cwd: path.dirname(outputPath) });
    proc.on('error', spawnError => {
      channel.appendLine(`[ASSEMBLE ERROR] ${spawnError.message}`);
      vscode.window.showErrorMessage(`Could not start the companion: ${spawnError.message}`);
    });
    proc.stdout.on('data', data => channel.append(data.toString()));
    proc.stderr.on('data', data => channel.append(data.toString()));
    proc.on('close', code => {
      if (code === 0) {
        vscode.window.showInformationMessage(`Stream assembly complete: ${path.basename(outputPath)}`);
      } else {
        vscode.window.showErrorMessage(`Stream assembly exited with error code ${code}`);
      }
    });
  });

  // Command 3: Copy FFmpeg Assembly Command
  const ffmpegCmd = vscode.commands.registerCommand('knouxGrabflow.generateFfmpegCommand', async () => {
    const url = await vscode.window.showInputBox({
      prompt: 'Enter HLS or DASH stream URL',
      placeHolder: 'https://example.com/live.m3u8'
    });
    if (!url || !url.trim()) return;

    const cmd = `ffmpeg -hide_banner -nostdin -i "${url.trim()}" -c copy -movflags +faststart "output.mp4"`;
    await vscode.env.clipboard.writeText(cmd);
    vscode.window.showInformationMessage('FFmpeg assembly command copied to clipboard!');
  });

  context.subscriptions.push(inspectCmd, assembleCmd, ffmpegCmd);
}

function deactivate() {
  if (outputChannel) {
    outputChannel.dispose();
  }
}

module.exports = {
  activate,
  deactivate,
  _test: {
    resolveCompanionScript,
    resolveTool,
    ffmpegCandidates,
    isExecutableFile
  }
};

'use strict';
/**
 * KNOuX GrabFlow — VS Code Companion Extension.
 *
 * Provides developer and media engineering tools for inspecting HLS/DASH streams,
 * generating safe FFmpeg commands, and launching desktop companion stream assembly.
 * Designed to be zero-dependency, secure (no shell interpolation), and lightweight.
 */

const vscode = require('vscode');
const path = require('path');
const { execFile, spawn } = require('child_process');

let outputChannel = null;

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
    const ffprobe = config.get('ffprobePath', 'ffprobe');

    execFile(ffprobe, [
      '-hide_banner', '-loglevel', 'error',
      '-show_entries', 'stream=index,codec_name,codec_type,width,height,bit_rate:format=duration,format_name',
      '-of', 'json', trimmed
    ], { timeout: 15000 }, (error, stdout, stderr) => {
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

    const defaultOut = 'output.mp4';
    const outputFilename = await vscode.window.showInputBox({
      prompt: 'Enter output filename (.mp4 or .mkv)',
      value: defaultOut
    });
    if (!outputFilename || !outputFilename.trim()) return;

    const scriptPath = path.resolve(__dirname, '..', 'scripts', 'assemble_stream.py');
    channel.show(true);
    channel.appendLine(`\n[ASSEMBLE] Launching companion assembly: ${url.trim()} -> ${outputFilename.trim()}`);

    const proc = spawn('python', [scriptPath, '--url', url.trim(), '--output', outputFilename.trim()]);
    proc.stdout.on('data', data => channel.append(data.toString()));
    proc.stderr.on('data', data => channel.append(data.toString()));
    proc.on('close', code => {
      if (code === 0) {
        vscode.window.showInformationMessage(`Stream assembly complete: ${outputFilename}`);
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
  deactivate
};

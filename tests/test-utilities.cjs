'use strict';
const assert = require('node:assert/strict');
const {
  filterSortAssets, safeDownloadName, exportAssetsCsv, exportAssetsJson,
  isDownloadableAsset, classifyMediaAsset, summarizeDownloads,
  generateFfmpegCommand, generateCurlCommand, formatDuration
} = require('../asset-utils');

let tests = 0;
function test(name, fn) { fn(); console.log('PASS', name); tests++; }

const data = [
  {type:'image', name:'zebra', url:'https://x.test/a.webp', width:1200, height:600},
  {type:'image', name:'alpha', url:'https://x.test/b.jpg', width:200, height:100},
  {type:'document', name:'Readme', url:'https://x.test/file.pdf'},
  {type:'video', name:'Showreel', url:'https://x.test/video.mp4', format:'direct'},
  {type:'video', name:'Live Broadcast', url:'https://x.test/live.m3u8', format:'hls'},
  {type:'audio', name:'Soundtrack', url:'https://x.test/audio.mp3'}
];

test('sort name without mutating input', () => {
 const original = [...data];
 const sorted = filterSortAssets(data, {sort:'name'});
 assert.deepEqual(sorted.map(x=>x.name), ['alpha','Live Broadcast','Readme','Showreel','Soundtrack','zebra']);
 assert.deepEqual(data, original);
});
test('large images filter keeps nonimage items', () => {
 const out = filterSortAssets(data, {largeImages:true});
 assert.deepEqual(out.map(x=>x.name), ['zebra','Readme','Showreel','Live Broadcast','Soundtrack']);
});
test('filter and search compose', () => {
 const out = filterSortAssets(data, {type:'image', query:'WEBP'});
 assert.equal(out.length, 1); assert.equal(out[0].name, 'zebra');
});
test('stream filter isolates HLS/DASH streaming manifests', () => {
 const streams = filterSortAssets(data, {type:'stream'});
 assert.equal(streams.length, 1);
 assert.equal(streams[0].name, 'Live Broadcast');
 assert.equal(streams[0].format, 'hls');
});
test('safe file names protect Windows device names and path traversal', () => {
 assert.equal(safeDownloadName({type:'document',url:'https://x.test/%2E%2E%2FCON.pdf'},1,'x.test'), 'KNOuX-GrabFlow/x.test/_CON.pdf');
 assert.equal(safeDownloadName({type:'image',url:'https://x.test/photo.webp'},2,'x.test'), 'KNOuX-GrabFlow/x.test/photo.webp');
 assert.ok(!safeDownloadName({type:'document',url:'https://x.test/%2E%2E%5Cevil.zip'},1,'x.test').includes('..'));
});
test('direct audio links preserve their extension in downloads', () => {
 assert.equal(safeDownloadName({type:'audio',url:'https://cdn.test/podcast.m4a'},4,'mysite.test'), 'KNOuX-GrabFlow/mysite.test/podcast.m4a');
});
test('CSV quotes potentially dangerous names as text', () => {
 const csv = exportAssetsCsv([{type:'image',name:'A, "B"',url:'https://site/a.png',width:1,height:2,source:'image'}]);
 assert.match(csv, /"A, ""B"""/);
 assert.equal(csv.split('\r\n').length, 2);
 const hostile=exportAssetsCsv([{type:'image',name:'=HYPERLINK(\"evil\")',url:'https://x.test'}]);
 assert.ok(hostile.includes(String.raw`"'=HYPERLINK`));
});
test('manifest imposes least privilege, no remote code, no traffic observation', () => {
 const m = require('../manifest.json');
 assert.equal(m.manifest_version, 3);
 assert.deepEqual(m.permissions, ['activeTab','scripting','downloads','storage','nativeMessaging']);
 assert.equal(m.host_permissions, undefined);
 assert.equal(m.optional_permissions, undefined);
 assert.equal(m.declarative_net_request, undefined);
 // The service worker exists for download lifecycle + companion session only.
 assert.deepEqual(m.background, {service_worker: 'background.js'});
 const code = require('fs').readFileSync(require('path').join(__dirname, '..', 'background.js'), 'utf8')
   .replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
 for (const forbidden of ['webRequest','declarativeNetRequest','executeScript','<all_urls>','debugger']) {
   assert.ok(!code.includes(forbidden), `background.js must not use ${forbidden}`);
 }
 assert.ok(!JSON.stringify(m).includes('unsafe-eval'));
});
test('hidden panels actually hide: every display-declaring class has a [hidden] rule', () => {
 // A `display:` on a class outranks the UA `[hidden]{display:none}` rule. This
 // shipped once as the scanner and Download Manager stacking together in Edge.
 const css = require('fs').readFileSync(require('path').join(__dirname, '..', 'popup.css'), 'utf8');
 const html = require('fs').readFileSync(require('path').join(__dirname, '..', 'popup.html'), 'utf8');
 // Classes used on elements the code toggles `hidden` on.
 const toggled = ['view-panel', 'preview-modal', 'notice', 'download-status'];
 for (const cls of toggled) {
   const declaresDisplay = new RegExp('\\.' + cls + '[^{}]*\\{[^}]*display:', 's').test(css);
   if (declaresDisplay) {
     assert.ok(new RegExp('\\.' + cls + '\\[hidden\\]').test(css),
       `.${cls} sets display but has no [hidden] override`);
   }
 }
 // The markup must still carry the ids the worker bridge and QA scripts address.
 for (const id of ['managerView','scannerView','previewModal','downloadStatus','notice',
                   'buildTag','watchToggleBtn','previewInspectBtn','previewDetails']) {
   assert.ok(html.includes(`id="${id}"`), `popup.html lost #${id}`);
 }
});
test('re-assembling a finished companion job keeps the media type', () => {
 // safeDownloadName derives the extension from asset.type. Dropping it on the
 // retry path silently produced a .bin output for an HLS assembly.
 const popup = require('fs').readFileSync(require('path').join(__dirname, '..', 'popup.js'), 'utf8');
 const retry = popup.match(/if \(item\.kind === 'companion'\)[\s\S]{0,400}?return;\s*\}/);
 assert.ok(retry, 'companion retry branch not found');
 assert.ok(/type:\s*'video'/.test(retry[0]),
   'companion retry must pass a media type so the output extension is correct');
 assert.equal(safeDownloadName({type:'video', url:'https://cdn.test/master.m3u8', format:'hls'}, 3, 'cdn.test'),
   'KNOuX-GrabFlow/cdn.test/master.m3u8');
});
test('stream playlists are copy-only, direct video files are downloadable', () => {
 assert.equal(isDownloadableAsset({type:'video',format:'hls'}), false);
 assert.equal(isDownloadableAsset({type:'video',format:'dash'}), false);
 assert.equal(isDownloadableAsset({type:'video',format:'direct'}), true);
 assert.equal(isDownloadableAsset({type:'document'}), true);
});
test('real download states are reconciled separately from download starts', () => {
 assert.deepEqual(summarizeDownloads([{state:'complete'},{state:'in_progress'},{state:'interrupted'},null]),
  {complete:1, running:1, interrupted:1, missing:1});
});
test('CSV exports media format for programmatic stream conversion', () => {
 const csv = exportAssetsCsv([{type:'video',name:'Stream',url:'https://cdn.test/master.m3u8',format:'hls'}]);
 assert.ok(csv.includes('format'));
 assert.ok(csv.includes('"hls"'));
});
test('safeDownloadName preserves MKV and WebM extensions accurately', () => {
 assert.equal(safeDownloadName({type:'video',url:'https://cdn.test/feature.mkv'},1,'cdn.test'), 'KNOuX-GrabFlow/cdn.test/feature.mkv');
 assert.equal(safeDownloadName({type:'video',url:'https://cdn.test/clip.webm?token=xyz'},2,'cdn.test'), 'KNOuX-GrabFlow/cdn.test/clip.webm');
 assert.equal(safeDownloadName({type:'video',format:'mkv',url:'https://cdn.test/get?id=99'},3,'cdn.test'), 'KNOuX-GrabFlow/cdn.test/video-3.mkv');
});
test('classifyMediaAsset constructs complete structured metadata', () => {
 const asset = {
   type: 'video',
   format: 'hls',
   url: 'https://media.test/master.m3u8',
   name: 'Master Stream',
   width: 1920,
   height: 1080,
   codec: 'avc1.640028',
   subtitles: [{src: 'https://media.test/sub.vtt', srclang: 'en', label: 'English', kind: 'subtitles'}]
 };
 const classified = classifyMediaAsset(asset);
 assert.equal(classified.mediaType, 'video');
 assert.equal(classified.format, 'hls');
 assert.equal(classified.isPlaylist, true);
 assert.equal(classified.resolution, '1920×1080');
 assert.equal(classified.codec, 'avc1.640028');
 assert.equal(classified.hasSubtitles, true);
 assert.equal(classified.subtitles.length, 1);
 assert.equal(classified.downloadEligibility, 'requires-companion');
 assert.equal(classified.supportedConversionPath, 'companion-assembly');
});
test('generateFfmpegCommand constructs secure, properly quoted CLI arguments', () => {
 const cmd = generateFfmpegCommand('https://cdn.test/live.m3u8', 'my_stream.mp4');
 assert.ok(cmd.startsWith('ffmpeg -hide_banner -nostdin -i "https://cdn.test/live.m3u8" -c copy -movflags +faststart'));
 assert.ok(cmd.endsWith('"my_stream.mp4"'));
});
test('generateCurlCommand generates correct direct download command', () => {
 const cmd = generateCurlCommand('https://cdn.test/archive.zip', 'archive.zip');
 assert.equal(cmd, 'curl -L -o "archive.zip" "https://cdn.test/archive.zip"');
});
test('formatDuration formats seconds into clean mm:ss or hh:mm:ss strings', () => {
 assert.equal(formatDuration(45), '0:45');
 assert.equal(formatDuration(125), '2:05');
 assert.equal(formatDuration(3665), '1:01:05');
 assert.equal(formatDuration(-1), '');
 assert.equal(formatDuration(null), '');
});
test('exportAssetsJson exports structured valid JSON', () => {
 const jsonStr = exportAssetsJson([{type:'video',format:'mp4',url:'https://x.test/vid.mp4',name:'Vid'}]);
 const parsed = JSON.parse(jsonStr);
 assert.ok(Array.isArray(parsed));
 assert.equal(parsed[0].mediaType, 'video');
 assert.equal(parsed[0].format, 'mp4');
});

console.log(`${tests} utility/security checks passed`);

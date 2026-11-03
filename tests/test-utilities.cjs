'use strict';
const assert = require('node:assert/strict');
const { filterSortAssets, safeDownloadName, exportAssetsCsv, isDownloadableAsset, summarizeDownloads } = require('../asset-utils');
let tests = 0;
function test(name, fn) { fn(); console.log('PASS',name); tests++; }
const data = [
  {type:'image', name:'zebra', url:'https://x.test/a.webp', width:1200, height:600},
  {type:'image', name:'alpha', url:'https://x.test/b.jpg', width:200, height:100},
  {type:'document', name:'Readme', url:'https://x.test/file.pdf'},
  {type:'video', name:'Showreel', url:'https://x.test/video.mp4'},
  {type:'audio', name:'Soundtrack', url:'https://x.test/audio.mp3'}
];
test('sort name without mutating input', () => {
 const original = [...data];
 const sorted = filterSortAssets(data,{sort:'name'});
 assert.deepEqual(sorted.map(x=>x.name),['alpha','Readme','Showreel','Soundtrack','zebra']);
 assert.deepEqual(data,original);
});
test('large images filter keeps nonimage items', () => {
 const out = filterSortAssets(data,{largeImages:true});
 assert.deepEqual(out.map(x=>x.name),['zebra','Readme','Showreel','Soundtrack']);
});
test('filter and search compose', () => {
 const out = filterSortAssets(data,{type:'image',query:'WEBP'});
 assert.equal(out.length,1); assert.equal(out[0].name,'zebra');
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
 assert.match(csv,/"A, ""B"""/);
 assert.equal(csv.split('\r\n').length,2);
 const hostile=exportAssetsCsv([{type:'image',name:'=HYPERLINK(\"evil\")',url:'https://x.test'}]);
 assert.ok(hostile.includes(String.raw`"'=HYPERLINK`));
});
test('manifest imposes least privilege, no remote code or background scanner', () => {
 const m = require('../manifest.json');
 assert.equal(m.manifest_version,3);
 assert.deepEqual(m.permissions,['activeTab','scripting','downloads','storage']);
 assert.equal(m.host_permissions,undefined);
 assert.equal(m.background,undefined);
 assert.ok(!JSON.stringify(m).includes('unsafe-eval'));
});
test('stream playlists are copy-only, direct video files are downloadable', () => {
 assert.equal(isDownloadableAsset({type:'video',format:'hls'}),false);
 assert.equal(isDownloadableAsset({type:'video',format:'dash'}),false);
 assert.equal(isDownloadableAsset({type:'video',format:'direct'}),true);
 assert.equal(isDownloadableAsset({type:'document'}),true);
});
test('real download states are reconciled separately from download starts', () => {
 assert.deepEqual(summarizeDownloads([{state:'complete'},{state:'in_progress'},{state:'interrupted'},null]),
  {complete:1,running:1,interrupted:1,missing:1});
});
test('CSV exports media format for programmatic stream conversion', () => {
 const csv=exportAssetsCsv([{type:'video',name:'Stream',url:'https://cdn.test/master.m3u8',format:'hls'}]);
 assert.ok(csv.includes('format'));
 assert.ok(csv.includes('"hls"'));
});
console.log(`${tests} utility/security checks passed`);

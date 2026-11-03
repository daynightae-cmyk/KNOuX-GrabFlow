'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const scanner = fs.readFileSync(path.join(root, 'scan-page.js'), 'utf8');
let passed = 0;
function makeNode(attrs = {}, extra = {}) {
  return {
    getAttribute: key => attrs[key] ?? null,
    textContent: extra.textContent || '',
    currentSrc: extra.currentSrc || '',
    querySelectorAll: selector => (extra.children || {})[selector] || [],
  };
}
function run({imgs=[], videos=[], audios=[], pictures=[], metas=[], links=[], css=[], scripts=[], resourceUrls=[], hostname='example.com', title='Example', url='https://example.com/page'} = {}) {
  const document = {
    baseURI: url, title,
    querySelectorAll: selector => ({
      'img': imgs, 'video': videos, 'audio': audios,
      'picture source[srcset],picture source[data-srcset]': pictures,
      'meta[property="og:image"],meta[property="og:image:url"],meta[name="twitter:image"],meta[property="og:video"],meta[property="og:video:url"],meta[property="og:video:secure_url"],meta[property="og:audio"],meta[property="og:audio:secure_url"]': metas,
      'a[href]': links, '[style*="background"]': css,
      'script[type="application/ld+json"]': scripts,
    })[selector] || []
  };
  const performance = {getEntriesByType: type => type === 'resource' ? resourceUrls.map(name=>({name})) : []};
  return vm.runInNewContext(`${scanner}\nscanPageAssets()`, {document, location: {hostname, href: url}, URL, Set, String, RegExp, performance});
}
function test(name, fn) { fn(); passed++; console.log('PASS', name); }

test('manifest uses MV3 with least-privilege click-to-scan and no all-sites permission', () => {
  const m = JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
  assert.equal(m.manifest_version, 3);
  assert.deepEqual(m.permissions, ['activeTab','scripting','downloads','storage']);
  assert.equal(m.host_permissions, undefined);
  assert.equal(m.background, undefined);
});
test('extracts and normalizes image relative URLs', () => {
  const page = run({imgs: [makeNode({src: '/images/test.png', alt:'Sample'})]});
  assert.equal(page.assets.length, 1);
  assert.equal(page.assets[0].url, 'https://example.com/images/test.png');
  assert.equal(page.assets[0].name, 'Sample');
});
test('honors currentSrc and deduplicates identical assets', () => {
  const page = run({imgs: [makeNode({src:'/a.jpg'}, {currentSrc: 'https://example.com/large.webp'}), makeNode({src:'/a.jpg'}, {currentSrc: 'https://example.com/large.webp'})]});
  assert.equal(page.assets.length, 1);
  assert.equal(page.assets[0].url, 'https://example.com/large.webp');
});
test('discovers lazy image from data-src and srcset', () => {
  const page = run({imgs: [makeNode({'data-src':'/lazy.png'}), makeNode({srcset:'/a.jpg 1x, /b.jpg 2x'})]});
  assert.deepEqual(Array.from(page.assets, a=>a.url), ['https://example.com/lazy.png','https://example.com/b.jpg']);
});
test('ignores non-http data, blob, javascript and invalid links', () => {
  const page = run({imgs: [makeNode({src:'data:image/png;base64,abc'}),makeNode({src:'blob:https://example.com/blab'}),makeNode({src:'javascript:alert(1)'})], links:[makeNode({href:'data:text/plain;base64,test.pdf'})]});
  assert.equal(page.assets.length, 0);
});
test('discovers direct video and files without touching network resources', () => {
  const vid = makeNode({src:'/promo.mp4', title:'Preview'}, {children:{'source[src],source[data-src]':[makeNode({src:'/backup.webm'})]}});
  const page = run({videos:[vid], links:[makeNode({href:'/manual.pdf'},{textContent:'Manual'}),makeNode({href:'/source.zip?dl=1'})]});
  assert.deepEqual(Array.from(page.assets,a=>a.type), ['video','video','document','document']);
  assert.equal(page.assets[2].name,'Manual');
});
test('does not expose YouTube video links through the scanner', () => {
  const page = run({hostname:'www.youtube.com',videos:[makeNode({src:'https://cdn.example/v.mp4'})],links:[makeNode({href:'https://cdn.example/alt.mp4'})]});
  assert.equal(page.assets.length, 0);
});
test('rejects non-direct OpenGraph video URLs', () => {
  const page = run({metas:[makeNode({content:'https://example.com/player?video=1'})]});
  assert.equal(page.assets.length, 0);
});
test('caps extracted asset count to 600', () => {
  const imgs = Array.from({length:650},(_,i)=>makeNode({src:`/img-${i}.png`}));
  const page = run({imgs});
  assert.equal(page.assets.length,600);
  assert.equal(page.truncated,true);
});
test('discovers inline CSS background images without fetching them', () => {
  const page = run({css:[makeNode({style: 'background-image:url(\"/cover.webp\")'})]});
  assert.equal(page.assets.length,1); assert.equal(page.assets[0].source,'background');
});
test('discovers directly linked images and blocks URLs with credentials', () => {
  const page = run({links:[makeNode({href:'/gallery.jpg'}), makeNode({href:'https://u:p@evil.test/private.jpg'})]});
  assert.equal(page.assets.length,1); assert.equal(page.assets[0].type,'image');
});
test('falls back to real lazy URLs when currentSrc contains a data placeholder', () => {
  const img=makeNode({'src':'data:image/svg+xml;base64,abcd','data-src':'/photography/hero.webp'},{currentSrc:'data:image/gif;base64,aaa'});
  const page=run({imgs:[img]});
  assert.equal(page.assets[0].url, 'https://example.com/photography/hero.webp');
});
test('extracts responsive picture source without executing scripts or fetching resources', () => {
  const page=run({pictures:[makeNode({'srcset':'/small.avif 300w, /large.avif 1200w'})]});
  assert.equal(page.assets[0].url,'https://example.com/large.avif');
  assert.equal(page.assets[0].source,'picture');
});
test('extracts direct audio players and audio links', () => {
  const player=makeNode({src:'/podcast.mp3',title:'Episode'},{children:{'source[src],source[data-src]':[makeNode({src:'/mix.flac'})]}});
  const page=run({audios:[player],links:[makeNode({href:'/music.ogg'})]});
  assert.deepEqual(Array.from(page.assets, a => a.type), ['audio','audio','audio']);
});
test('recognizes OpenGraph images and direct media but rejects player pages', () => {
  const page=run({metas:[makeNode({property:'og:image',content:'/share.webp'}), makeNode({property:'og:audio',content:'/track.mp3'}),makeNode({property:'og:video',content:'/player?watch=1'})]});
  assert.deepEqual(Array.from(page.assets, a=>a.type), ['image','audio']);
});
test('rejects authenticated URLs and script-like candidate values even inside new formats', () => {
  const page=run({pictures:[makeNode({srcset:'javascript:alert(1) 3x, data:image/png;base64,zzz 2x'})], audios:[makeNode({src:'https://user:pass@example.com/private.mp3'})]});
  assert.equal(page.assets.length,0);
});
test('records loaded image dimensions for size filtering', () => {
  const img = makeNode({src:'/photo.jpg'}); img.naturalWidth=1920; img.naturalHeight=1080;
  const page = run({imgs:[img]}); assert.equal(page.assets[0].width,1920);
});
test('sanitizes untrusted labels by truncating long strings', () => {
  const page = run({imgs:[makeNode({src:'/pic.jpg',alt:'A'.repeat(500)})]});
  assert.equal(page.assets[0].name.length,140);
});
test('detects HLS and DASH manifests but never mistakes segments for full videos', () => {
  const video = makeNode({src:'blob:https://example.com/test'}, {children:{'source[src],source[data-src]':[makeNode({src:'/stream/master.m3u8'})]}});
  const page=run({videos:[video], links:[makeNode({href:'/livestream.mpd'}),makeNode({href:'/segment_001.ts'})]});
  assert.deepEqual(Array.from(page.assets,a=>a.format), ['hls','dash']);
  assert.equal(page.assets.length,2);
});
test('finds dynamically requested direct media and HLS via resource timing names only', () => {
  const page=run({resourceUrls:['https://example.com/player.js','https://cdn.example.com/clip.mp4?token=x',
    'https://cdn.example.com/index.m3u8','https://cdn.example.com/part_02.m4s']});
  assert.deepEqual(Array.from(page.assets,a=>a.format), ['direct','hls']);
  assert.ok(page.assets.every(a=>a.source==='resource-timing'));
});
test('detects extensionless video sources only when explicit media MIME is provided', () => {
  const video=makeNode({src:'https://example.com/api/asset?id=44',type:'video/mp4'});
  const stream=makeNode({href:'https://example.com/live/playlist?id=1',type:'application/vnd.apple.mpegurl'});
  const page=run({videos:[video],links:[stream]});
  assert.deepEqual(Array.from(page.assets,a=>a.format), ['direct','hls']);
});
test('discovers direct VideoObject contentUrl without executing embedded page scripts', () => {
  const scripts=[makeNode({}, {textContent:JSON.stringify({'@graph':[{'@type':'VideoObject',name:'My movie',contentUrl:'https://cdn.example.com/my-video.webm'}]})})];
  const page=run({scripts});
  assert.equal(page.assets.length,1);
  assert.equal(page.assets[0].name,'My movie');
  assert.equal(page.assets[0].format,'direct');
});
test('limits structured metadata and does not classify generic embed pages as video files', () => {
  const scripts=[makeNode({}, {textContent:'{' + 'a'.repeat(140000)})];
  const page=run({scripts,resourceUrls:['https://example.com/watch?video=1','https://example.com/stream/seg_4.ts']});
  assert.equal(page.assets.length,0);
});
test('does not expose video manifests or observed files from YouTube host', () => {
  const page=run({hostname:'youtube.com',resourceUrls:['https://cdn.example.com/vid.mp4','https://cdn.example.com/master.m3u8'],links:[makeNode({href:'/list.m3u8'})]});
  assert.equal(page.assets.length,0);
});
console.log(`\n${passed} scanner/security checks passed.`);

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
function run({imgs=[], videos=[], metas=[], links=[], css=[], hostname='example.com', title='Example', url='https://example.com/page'} = {}) {
  const document = {
    baseURI: url, title,
    querySelectorAll: selector => ({
      'img': imgs, 'video': videos,
      'meta[property="og:video"],meta[property="og:video:url"],meta[property="og:video:secure_url"]': metas,
      'a[href]': links, '[style*="background"]': css,
    })[selector] || []
  };
  return vm.runInNewContext(`${scanner}\nscanPageAssets()`, {document, location: {hostname, href: url}, URL, Set, String, RegExp});
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
  const vid = makeNode({src:'/promo.mp4', title:'Preview'}, {children:{'source[src]':[makeNode({src:'/backup.webm'})]}});
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
test('records loaded image dimensions for size filtering', () => {
  const img = makeNode({src:'/photo.jpg'}); img.naturalWidth=1920; img.naturalHeight=1080;
  const page = run({imgs:[img]}); assert.equal(page.assets[0].width,1920);
});
test('sanitizes untrusted labels by truncating long strings', () => {
  const page = run({imgs:[makeNode({src:'/pic.jpg',alt:'A'.repeat(500)})]});
  assert.equal(page.assets[0].name.length,140);
});
console.log(`\n${passed} scanner/security checks passed.`);

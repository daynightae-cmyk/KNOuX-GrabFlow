'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const {scanPageAssets} = require(path.join(root, 'scan-page.js'));
let passed = 0;
function makeNode(attrs = {}, extra = {}) {
  return {
    getAttribute: key => attrs[key] ?? null,
    textContent: extra.textContent || '',
    currentSrc: extra.currentSrc || '',
    videoWidth: extra.videoWidth || 0,
    videoHeight: extra.videoHeight || 0,
    duration: extra.duration || 0,
    naturalWidth: extra.naturalWidth || 0,
    naturalHeight: extra.naturalHeight || 0,
    shadowRoot: extra.shadowRoot || null,
    querySelectorAll: selector => (extra.children || {})[selector] || [],
  };
}
function run({imgs=[], videos=[], audios=[], pictures=[], metas=[], links=[], css=[], scripts=[], resourceUrls=[], resourceEntries=[], dynamicPlayers=[], iframes=[], preloads=[], objects=[], hostname='example.com', title='Example', url='https://example.com/page', bufferSize=null} = {}) {
  const document = {
    baseURI: url, title,
    querySelectorAll: selector => ({
      'img': imgs, 'video': videos, 'audio': audios,
      'picture source[srcset],picture source[data-srcset]': pictures,
      'meta[property="og:image"],meta[property="og:image:url"],meta[name="twitter:image"],meta[property="og:video"],meta[property="og:video:url"],meta[property="og:video:secure_url"],meta[property="og:audio"],meta[property="og:audio:secure_url"],meta[name="twitter:player:stream"]': metas,
      'a[href]': links, '[style*="background"]': css,
      'script[type="application/ld+json"]': scripts,
      'video-js, plyr, media-player, video-player, [data-player], .jwplayer, .vjs-tech': dynamicPlayers,
      'iframe': iframes,
      'link[rel="preload"],link[rel="preconnect"],link[rel="preload"]': preloads,
      'object[data],embed[src]': objects
    })[selector] || []
  };
  const entries = resourceEntries.length
    ? resourceEntries
    : resourceUrls.map(name => ({name}));
  const performance = {
    getEntriesByType: type => type === 'resource' ? entries : [],
    // The real browser exposes this; the scanner must ask for a larger buffer
    // because Chrome stops recording at ~250 entries by default.
    ...(bufferSize === false ? {} : {setResourceTimingBufferSize: size => { bufferSizeSeen = size; }})
  };
  // The scanner reads `document`, `location` and `performance` as free variables.
  // Supplying them as real globals lets the shipped module run unmodified, with no
  // dynamic evaluation of a source string anywhere in the test path.
  const saved = {
    document: globalThis.document,
    location: globalThis.location,
    performance: globalThis.performance
  };
  globalThis.document = document;
  globalThis.location = {hostname, href: url};
  globalThis.performance = performance;
  try {
    return scanPageAssets();
  } finally {
    globalThis.document = saved.document;
    globalThis.location = saved.location;
    globalThis.performance = saved.performance;
  }
}
let bufferSizeSeen = null;
function test(name, fn) { fn(); passed++; console.log('PASS', name); }

test('manifest uses MV3 with least-privilege click-to-scan and no all-sites permission', () => {
  const m = JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
  assert.equal(m.manifest_version, 3);
  assert.deepEqual(m.permissions, ['activeTab','scripting','downloads','storage','nativeMessaging']);
  assert.equal(m.host_permissions, undefined);
  assert.equal(m.optional_permissions, undefined);
  assert.equal(m.declarative_net_request, undefined);
  // A background worker is permitted, but only for the download lifecycle and
  // the companion session. It must never gain scanning or traffic powers.
  assert.deepEqual(m.background, {service_worker: 'background.js'});
  const rawWorker = fs.readFileSync(path.join(root,'background.js'),'utf8');
  // Comments may name a forbidden API to explain why it is absent; only code counts.
  const worker = rawWorker.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
  for (const forbidden of ['webRequest','declarativeNetRequest','executeScript','<all_urls>',
                           'cookies','history','debugger','tabs.query']) {
    assert.ok(!worker.includes(forbidden), `background.js must not reference ${forbidden}`);
  }
});
test('extracts and normalizes image relative URLs', () => {
  const page = run({imgs: [makeNode({src: '/images/test.png', alt:'Sample'})]});
  assert.equal(page.assets.length, 1);
  assert.equal(page.assets[0].url, 'https://example.com/images/test.png');
  assert.equal(page.assets[0].name, 'Sample');
});
test('honors currentSrc and deduplicates identical assets', () => {
  const page = run({imgs: [makeNode({src:'/a.jpg'}, {currentSrc: 'https://example.com/a.jpg'}), makeNode({src:'https://example.com/a.jpg'})]});
  assert.equal(page.assets.length, 1);
});
test('discovers lazy image from data-src and srcset', () => {
  const page = run({imgs: [makeNode({'data-src':'/lazy.png'}), makeNode({srcset:'/a.jpg 1x, /b.jpg 2x'})]});
  assert.deepEqual(Array.from(page.assets, a=>a.url), ['https://example.com/lazy.png','https://example.com/b.jpg']);
});
test('ignores non-http data, blob, javascript and invalid links', () => {
  const page = run({
    imgs: [makeNode({src: 'data:image/png;base64,AAA'}), makeNode({src: 'blob:https://example.com/123'})],
    links: [makeNode({href: 'javascript:void(0)'}), makeNode({href: 'mailto:me@example.com'})]
  });
  assert.equal(page.assets.length, 0);
});
test('discovers direct video and files without touching network resources', () => {
  const page = run({videos: [makeNode({src: '/clip.mp4', title:'Intro Video'})], links: [makeNode({href:'/doc.pdf', download:'Report'})]});
  assert.deepEqual(Array.from(page.assets, a => a.type), ['video','document']);
});
test('does not expose YouTube video links through the scanner', () => {
  const page = run({hostname: 'www.youtube.com', videos: [makeNode({src: '/watch?v=123'})]});
  assert.equal(page.assets.length, 0);
});
test('rejects non-direct OpenGraph video URLs', () => {
  const page = run({metas: [makeNode({property:'og:video', content: 'https://example.com/embed/player'})]});
  assert.equal(page.assets.length, 0);
});
test('caps extracted asset count to 600', () => {
  const imgs = Array.from({length: 650}, (_, i) => makeNode({src: `/img-${i}.png`}));
  const page = run({imgs});
  assert.equal(page.assets.length, 600);
  assert.equal(page.truncated, true);
});
test('discovers inline CSS background images without fetching them', () => {
  const page = run({css: [makeNode({style: 'background-image: url("/bg.jpg")'})]});
  assert.equal(page.assets.length, 1);
  assert.equal(page.assets[0].url, 'https://example.com/bg.jpg');
});
test('discovers directly linked images and blocks URLs with credentials', () => {
  const page = run({links: [makeNode({href: '/banner.png'}), makeNode({href: 'https://user:pass@example.com/secret.png'})]});
  assert.equal(page.assets.length, 1);
  assert.equal(page.assets[0].url, 'https://example.com/banner.png');
});
test('falls back to real lazy URLs when currentSrc contains a data placeholder', () => {
  const node = makeNode({'data-src': '/hero.webp'}, {currentSrc: 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'});
  const page = run({imgs: [node]});
  assert.equal(page.assets.length, 1);
  assert.equal(page.assets[0].url, 'https://example.com/hero.webp');
});
test('extracts responsive picture source without executing scripts or fetching resources', () => {
  const page = run({pictures: [makeNode({srcset: '/small.avif 1x, /large.avif 2x'})]});
  assert.equal(page.assets.length, 1);
  assert.equal(page.assets[0].url, 'https://example.com/large.avif');
  assert.equal(page.assets[0].source, 'picture');
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
  const page = run({resourceUrls: ['https://example.com/media/clip.webm','https://example.com/hls/live.m3u8','https://example.com/analytics.js']});
  assert.equal(page.assets.length, 2);
  assert.deepEqual(Array.from(page.assets, a=>a.source), ['resource-timing','resource-timing']);
});
test('extracts direct video contentUrl from JSON-LD VideoObject without a video tag', () => {
  const script = makeNode({}, {textContent: JSON.stringify({'@context':'https://schema.org','@type':'VideoObject',name:'Promo',contentUrl:'https://example.com/promo.mp4',width:1280,height:720})});
  const page = run({scripts: [script]});
  assert.equal(page.assets.length, 1);
  assert.equal(page.assets[0].type, 'video');
  assert.equal(page.assets[0].url, 'https://example.com/promo.mp4');
  assert.equal(page.assets[0].source, 'structured-data');
});
test('does not expose video manifests or observed files from YouTube host', () => {
  const video = makeNode({src: '/stream.m3u8'});
  const page = run({hostname: 'm.youtube.com', videos: [video], resourceUrls: ['https://m.youtube.com/videoplayback.mp4']});
  assert.equal(page.assets.length, 0);
});
test('discovers directly available MKV videos and classifies them as direct format', () => {
  const video = makeNode({src: '/archive/feature.mkv', title: 'Feature Film'});
  const page = run({videos: [video]});
  assert.equal(page.assets.length, 1);
  assert.equal(page.assets[0].type, 'video');
  assert.equal(page.assets[0].format, 'direct');
  assert.equal(page.assets[0].downloadEligibility, 'eligible');
});
test('extracts subtitle tracks from video element', () => {
  const track1 = makeNode({src: '/subtitles/en.vtt', kind: 'subtitles', srclang: 'en', label: 'English'});
  const track2 = makeNode({src: '/subtitles/ar.vtt', kind: 'captions', srclang: 'ar', label: 'Arabic'});
  const vid = makeNode({src: '/movie.mp4', title: 'Subtitled Movie'}, {
    children: {'track': [track1, track2]}
  });
  const page = run({videos: [vid]});
  assert.equal(page.assets.length, 1);
  assert.equal(page.assets[0].hasSubtitles, true);
  assert.equal(page.assets[0].subtitles.length, 2);
  assert.equal(page.assets[0].subtitles[0].srclang, 'en');
  assert.equal(page.assets[0].subtitles[1].srclang, 'ar');
});
test('extracts video resolution and codec from MIME codecs parameter', () => {
  const source = makeNode({src: '/stream.mp4', type: 'video/mp4; codecs="avc1.640028, mp4a.40.2"', width: '1920', height: '1080'});
  const vid = makeNode({title: 'HD Stream'}, {
    children: {'source[src],source[data-src]': [source]}
  });
  const page = run({videos: [vid]});
  assert.equal(page.assets.length, 1);
  assert.equal(page.assets[0].codec, 'avc1.640028, mp4a.40.2');
  assert.equal(page.assets[0].resolution, '1920×1080');
});
test('marks HLS and DASH with requires-companion eligibility and companion-assembly conversion', () => {
  const vid = makeNode({src: '/live/manifest.m3u8'});
  const page = run({videos: [vid]});
  assert.equal(page.assets[0].format, 'hls');
  assert.equal(page.assets[0].isPlaylist, true);
  assert.equal(page.assets[0].downloadEligibility, 'requires-companion');
  assert.equal(page.assets[0].conversionPath, 'companion-assembly');
});
test('discovers video sources from dynamic player custom elements (video-js, plyr, media-player)', () => {
  const player = makeNode({'data-video-src': 'https://cdn.example.com/interactive-promo.mp4', 'title': 'Custom Player'});
  const page = run({dynamicPlayers: [player]});
  assert.equal(page.assets.length, 1);
  assert.equal(page.assets[0].type, 'video');
  assert.equal(page.assets[0].url, 'https://cdn.example.com/interactive-promo.mp4');
  assert.equal(page.assets[0].source, 'dynamic-player');
});
test('extracts video poster image as image asset and attaches it to video metadata', () => {
  const vid = makeNode({src: '/trailer.mp4', poster: '/images/poster-hd.jpg', title: 'Teaser'});
  const page = run({videos: [vid]});
  assert.equal(page.assets.length, 2);
  const posterAsset = page.assets.find(a => a.type === 'image');
  const videoAsset = page.assets.find(a => a.type === 'video');
  assert.ok(posterAsset);
  assert.equal(posterAsset.url, 'https://example.com/images/poster-hd.jpg');
  assert.equal(posterAsset.source, 'poster');
  assert.ok(videoAsset);
  assert.equal(videoAsset.poster, 'https://example.com/images/poster-hd.jpg');
});
test('extracts video duration in seconds when available', () => {
  const vid = makeNode({src: '/clip.webm', title: 'Duration Clip'}, {duration: 142.5});
  const page = run({videos: [vid]});
  assert.equal(page.assets.length, 1);
  assert.equal(page.assets[0].duration, 143);
});
test('discovers streaming sources from data-hls-src and data-file player attributes', () => {
  const player = makeNode({'data-hls-src': 'https://stream.example.com/live.m3u8', 'title': 'HLS Player'});
  const page = run({dynamicPlayers: [player]});
  assert.equal(page.assets.length, 1);
  assert.equal(page.assets[0].format, 'hls');
  assert.equal(page.assets[0].isPlaylist, true);
});

test('discovers media declared by link rel=preload without issuing any request', () => {
  const nodes = [
    makeNode({rel: 'preload', as: 'video', href: '/media/feature.mp4'}),
    makeNode({rel: 'preload', as: 'audio', href: '/media/voice.mp3'}),
    makeNode({rel: 'preload', as: 'image', href: '/media/hero.webp'}),
    makeNode({rel: 'preload', href: '/media/master.m3u8'})
  ];
  const page = run({preloads: nodes});
  const byUrl = Object.fromEntries(page.assets.map(a => [a.url.split('/').pop(), a]));
  assert.equal(byUrl['feature.mp4'].type, 'video');
  assert.equal(byUrl['voice.mp3'].type, 'audio');
  assert.equal(byUrl['hero.webp'].type, 'image');
  assert.equal(byUrl['master.m3u8'].format, 'hls');
  assert.ok(page.assets.every(a => a.source === 'preload'));
});
test('discovers plugin media from object data and embed src', () => {
  const page = run({objects: [
    makeNode({data: 'https://legacy.example.com/lecture.mp4', title: 'Lecture'}),
    makeNode({src: 'https://legacy.example.com/song.mp3'}),
    makeNode({data: 'https://legacy.example.com/spec.pdf'})
  ]});
  // Spread into an outer-realm array: vm results are cross-realm Arrays and
  // deepStrictEqual compares prototypes.
  const kinds = [...page.assets].map(a => `${a.type}:${a.source}`).sort((a, b) => a.localeCompare(b));
  assert.deepEqual(kinds, ['audio:object', 'document:object', 'video:object']);
});
test('records the browser initiatorType so a UI can show what asked for the media', () => {
  const page = run({resourceEntries: [
    {name: 'https://cdn.example.com/feature.mp4', initiatorType: 'video'},
    {name: 'https://cdn.example.com/podcast.mp3', initiatorType: 'audio'},
    {name: 'https://cdn.example.com/report.pdf', initiatorType: 'xmlhttprequest'}
  ]});
  const byName = Object.fromEntries(page.assets.map(a => [a.url.split('/').pop(), a]));
  assert.equal(byName['feature.mp4'].initiatorType, 'video');
  assert.equal(byName['podcast.mp3'].initiatorType, 'audio');
  assert.equal(byName['report.pdf'].initiatorType, 'xmlhttprequest');
});
test('expands the resource timing buffer so late manifests are still visible', () => {
  bufferSizeSeen = null;
  run({resourceUrls: ['https://cdn.example.com/a.mp4']});
  assert.equal(bufferSizeSeen, 3000);
});
test('survives a browser without setResourceTimingBufferSize', () => {
  bufferSizeSeen = null;
  const page = run({resourceUrls: ['https://cdn.example.com/b.mp4'], bufferSize: false});
  assert.equal(page.assets[0].url, 'https://cdn.example.com/b.mp4');
});
test('still refuses every media type on YouTube hosts, including resource timing', () => {
  const page = run({
    hostname: 'www.youtube.com',
    resourceEntries: [
      {name: 'https://cdn.example.com/clip.mp4', initiatorType: 'video'},
      {name: 'https://cdn.example.com/talk.mp3', initiatorType: 'audio'}
    ],
    objects: [makeNode({data: 'https://cdn.example.com/lecture.mp4'})]
  });
  assert.equal(page.assets.filter(a => ['video', 'audio'].includes(a.type)).length, 0);
});

console.log(`\n${passed} scanner/security checks passed.`);

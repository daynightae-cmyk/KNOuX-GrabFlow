'use strict';
/**
 * On-demand, DOM-only, dependency-free scanner. This function MUST stay
 * self-contained: chrome.scripting.executeScript serializes it across realms.
 * It never fetches URLs, runs page scripts, touches cookies, or captures traffic.
 */
function scanPageAssets() {
  const LIMIT = 600;
  const assets = [];
  const seen = new Map();
  const blockedVideo = /(^|\.)(youtube\.com|youtube-nocookie\.com|youtu\.be)$/i.test(location.hostname);
  const extensions = {
    image: /\.(?:jpe?g|png|webp|gif|svg|avif|bmp|tiff?)(?:[?#]|$)/i,
    video: /\.(?:mp4|webm|ogv|mov|m4v)(?:[?#]|$)/i,
    audio: /\.(?:mp3|m4a|aac|wav|flac|ogg|oga|opus)(?:[?#]|$)/i,
    document: /\.(?:pdf|docx?|xlsx?|pptx?|txt|csv|epub|zip|rar|7z|json|md)(?:[?#]|$)/i
  };
  const validTypes = Object.keys(extensions);
  // A playlist is a recipe for many segments, not a downloadable complete video.
  function videoFormat(value, mime = '') {
    const v = String(value || '');
    const m = String(mime || '').toLowerCase();
    if (/\.m3u8(?:[?#]|$)/i.test(v) || /(?:vnd\.apple\.mpegurl|x-mpegurl)/.test(m)) return 'hls';
    if (/\.mpd(?:[?#]|$)/i.test(v) || m.includes('dash+xml')) return 'dash';
    return 'direct';
  }
  function classifyVideo(value, mime = '') {
    if (videoFormat(value, mime) !== 'direct') return true;
    return extensions.video.test(String(value || '')) || /^(?:video\/(?:mp4|webm|ogg|quicktime|x-m4v))\b/i.test(String(mime || ''));
  }
  function safeUrl(value) {
    if (typeof value !== 'string' || !value.trim()) return null;
    try {
      const u = new URL(value.trim(), document.baseURI);
      // Never expose credentials, local files, dangerous schemes or browser URLs.
      return ['http:', 'https:'].includes(u.protocol) && !u.username && !u.password ? u.href : null;
    } catch (_) { return null; }
  }
  function add(type, candidate, label, source = 'dom', width = 0, height = 0, mime = '') {
    if (assets.length >= LIMIT || !validTypes.includes(type) || (blockedVideo && type === 'video')) return;
    const url = safeUrl(candidate);
    if (!url) return;
    if (seen.has(url)) {
      const prior = assets[seen.get(url)];
      if (prior && !prior.width && width > 0) { prior.width = width; prior.height = height; }
      return;
    }
    let name = typeof label === 'string' ? label.replace(/\s+/g, ' ').trim() : '';
    if (!name) {
      try { name = decodeURIComponent(new URL(url).pathname.split('/').pop() || ''); }
      catch (_) { name = ''; }
    }
    seen.set(url, assets.length);
    assets.push({type, url, name: (name || `${type} asset`).slice(0, 140), source,
      ...(type === 'video' ? {format: videoFormat(url, mime)} : {}),
      width: Number.isFinite(width) && width > 0 ? Math.trunc(width) : 0,
      height: Number.isFinite(height) && height > 0 ? Math.trunc(height) : 0});
  }
  function bestSrcset(value) {
    if (typeof value !== 'string' || !value.trim()) return '';
    // Remove complete data: entries before splitting: their payload contains a comma.
    const withoutData = value.replace(/data:[^\s]+(?:\s+\d+(?:\.\d+)?[wx])?/gi, '');
    const candidates = withoutData.split(',').map(part => {
      const [url, descriptor = ''] = part.trim().split(/\s+/);
      const match = /^(\d+(?:\.\d+)?)(w|x)$/.exec(descriptor);
      return {url, weight: match ? Number(match[1]) : 0};
    }).filter(candidate => safeUrl(candidate.url));
    candidates.sort((a, b) => b.weight - a.weight);
    return candidates[0]?.url || '';
  }
  function firstHttp(...values) {
    for (const v of values) if (safeUrl(v)) return v;
    return '';
  }
  for (const img of document.querySelectorAll('img')) {
    const url = firstHttp(img.currentSrc,
      img.getAttribute('data-src'), img.getAttribute('data-original'),
      img.getAttribute('data-lazy-src'), img.getAttribute('data-url'),
      bestSrcset(img.getAttribute('data-srcset')),
      bestSrcset(img.getAttribute('srcset')), img.getAttribute('src'));
    add('image', url, img.getAttribute('alt') || img.getAttribute('title'), 'image',
      img.naturalWidth, img.naturalHeight);
    if (assets.length >= LIMIT) break;
  }
  // Picture/source may expose an original responsive image even when <img>
  // is still a data URI placeholder. Do not trigger additional network requests.
  for (const source of document.querySelectorAll('picture source[srcset],picture source[data-srcset]')) {
    add('image', firstHttp(bestSrcset(source.getAttribute('data-srcset')),
      bestSrcset(source.getAttribute('srcset'))), '', 'picture');
    if (assets.length >= LIMIT) break;
  }
  if (!blockedVideo) {
    for (const video of document.querySelectorAll('video')) {
      const src = firstHttp(video.currentSrc, video.getAttribute('src'), video.getAttribute('data-src'),
        video.getAttribute('data-hls'), video.getAttribute('data-video-src'));
      if (src) add('video', src, video.getAttribute('title') || video.getAttribute('aria-label'), 'video', 0, 0,
        video.getAttribute('type') || '');
      for (const source of video.querySelectorAll('source[src],source[data-src]')) {
        const src = firstHttp(source.getAttribute('src'), source.getAttribute('data-src'));
        if (src && classifyVideo(src, source.getAttribute('type'))) add('video', src,
          video.getAttribute('title'), 'video', 0, 0, source.getAttribute('type'));
      }
    }
  }
  for (const audio of document.querySelectorAll('audio')) {
    add('audio', firstHttp(audio.currentSrc, audio.getAttribute('src'), audio.getAttribute('data-src')),
      audio.getAttribute('title') || audio.getAttribute('aria-label'), 'audio');
    for (const source of audio.querySelectorAll('source[src],source[data-src]')) {
      add('audio', firstHttp(source.getAttribute('src'), source.getAttribute('data-src')),
        audio.getAttribute('title'), 'audio');
    }
  }
  // Only direct media formats from OpenGraph; no playlist, page player or DRM.
  for (const meta of document.querySelectorAll('meta[property="og:image"],meta[property="og:image:url"],meta[name="twitter:image"],meta[property="og:video"],meta[property="og:video:url"],meta[property="og:video:secure_url"],meta[property="og:audio"],meta[property="og:audio:secure_url"]')) {
    const tag = meta.getAttribute('property') || meta.getAttribute('name') || '';
    const value = meta.getAttribute('content');
    const type = tag.includes('image') ? 'image' : tag.includes('audio') ? 'audio' : 'video';
    if (value && (type === 'video' ? classifyVideo(value) : extensions[type].test(value))) add(type, value, '', 'meta');
  }
  // Deliberately bounded scan of *inline* CSS. Never fetch stylesheets.
  let sampled = 0;
  for (const node of document.querySelectorAll('[style*="background"]')) {
    if (++sampled > 300 || assets.length >= LIMIT) break;
    const style = node.getAttribute('style') || '';
    const match = /background(?:-image)?\s*:[^;]*?url\(\s*["']?([^)'"\s]+)["']?\s*\)/i.exec(style);
    if (match) add('image', match[1], node.getAttribute('aria-label') || node.getAttribute('title'), 'background');
  }
  for (const link of document.querySelectorAll('a[href]')) {
    const url = link.getAttribute('href');
    if (!url) continue;
    const name = link.getAttribute('download') || link.getAttribute('aria-label') || link.textContent;
    for (const type of validTypes) {
      if (type === 'video' ? classifyVideo(url, link.getAttribute('type')) : extensions[type].test(url)) {
        add(type, url, name, 'link', 0, 0, link.getAttribute('type')); break;
      }
    }
    if (assets.length >= LIMIT) break;
  }
  // Video-first: read public Resource Timing *names* from the current page only.
  // Do NOT fetch or intercept network traffic and do NOT collect streaming segments.
  if (!blockedVideo && typeof performance !== 'undefined' && typeof performance.getEntriesByType === 'function') {
    let checked = 0;
    for (const entry of performance.getEntriesByType('resource')) {
      if (++checked > 1200 || assets.length >= LIMIT) break;
      if (typeof entry.name === 'string' && classifyVideo(entry.name)) {
        add('video', entry.name, '', 'resource-timing');
      }
    }
  }
  // VideoObject often exposes a legitimate direct contentUrl without a <video> tag.
  if (!blockedVideo) {
    let checked = 0;
    function visit(value, depth = 0) {
      if (!value || depth > 5 || assets.length >= LIMIT) return;
      if (Array.isArray(value)) { for (const x of value.slice(0, 40)) visit(x, depth + 1); return; }
      if (typeof value !== 'object') return;
      const typ = value['@type'];
      if (typ === 'VideoObject' || (Array.isArray(typ) && typ.includes('VideoObject'))) {
        const content = value.contentUrl;
        const mime = value.encodingFormat || '';
        if (typeof content === 'string' && classifyVideo(content, mime)) {
          add('video', content, value.name || '', 'structured-data', 0, 0, mime);
        }
      }
      for (const k of ['@graph', 'mainEntity', 'video', 'itemListElement']) if (value[k]) visit(value[k], depth + 1);
    }
    for (const script of document.querySelectorAll('script[type="application/ld+json"]')) {
      if (++checked > 20 || assets.length >= LIMIT) break;
      const raw = script.textContent || '';
      if (raw.length > 131072) continue;
      try { visit(JSON.parse(raw)); } catch (_) { /* untrusted or invalid metadata */ }
    }
  }
  return {
    title: String(document.title || '').slice(0, 150),
    domain: location.hostname, pageUrl: location.href,
    assets, truncated: assets.length >= LIMIT
  };
}

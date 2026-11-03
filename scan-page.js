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
    video: /\.(?:mp4|webm|ogv|mov|m4v|mkv)(?:[?#]|$)/i,
    audio: /\.(?:mp3|m4a|aac|wav|flac|ogg|oga|opus|weba)(?:[?#]|$)/i,
    document: /\.(?:pdf|docx?|xlsx?|pptx?|txt|csv|epub|zip|rar|7z|json|md)(?:[?#]|$)/i
  };
  const validTypes = Object.keys(extensions);
  const audioMime = /^(?:audio\/(?:mpeg|mp4|aac|wav|flac|ogg|opus|webm))\b/i;

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
    return extensions.video.test(String(value || '')) || /^(?:video\/(?:mp4|webm|ogg|quicktime|x-m4v|x-matroska))\b/i.test(String(mime || ''));
  }
  function classifyAudio(value, mime = '') {
    return extensions.audio.test(String(value || '')) || audioMime.test(String(mime || ''));
  }
  function safeUrl(value) {
    if (typeof value !== 'string' || !value.trim()) return null;
    try {
      const u = new URL(value.trim(), document.baseURI);
      // Never expose credentials, local files, dangerous schemes or browser URLs.
      return ['http:', 'https:'].includes(u.protocol) && !u.username && !u.password ? u.href : null;
    } catch (_) { return null; }
  }
  function add(type, candidate, label, source = 'dom', width = 0, height = 0, mime = '', extra = {}) {
    if (assets.length >= LIMIT || !validTypes.includes(type) || (blockedVideo && type === 'video')) return;
    const url = safeUrl(candidate);
    if (!url) return;
    if (seen.has(url)) {
      const prior = assets[seen.get(url)];
      if (prior) {
        if (!prior.width && width > 0) { prior.width = Math.trunc(width); prior.height = Math.trunc(height); }
        if (extra.subtitles && (!prior.subtitles || !prior.subtitles.length)) {
          prior.subtitles = extra.subtitles;
          prior.hasSubtitles = true;
        }
        if (extra.codec && !prior.codec) prior.codec = extra.codec;
        if (extra.poster && !prior.poster) prior.poster = extra.poster;
        if (extra.duration && !prior.duration) prior.duration = extra.duration;
      }
      return;
    }
    let name = typeof label === 'string' ? label.replace(/\s+/g, ' ').trim() : '';
    if (!name) {
      try { name = decodeURIComponent(new URL(url).pathname.split('/').pop() || ''); }
      catch (_) { name = ''; }
    }
    seen.set(url, assets.length);
    const w = Number.isFinite(width) && width > 0 ? Math.trunc(width) : 0;
    const h = Number.isFinite(height) && height > 0 ? Math.trunc(height) : 0;
    const item = {
      type, url, name: (name || `${type} asset`).slice(0, 140), source,
      width: w, height: h
    };
    if (type === 'video') {
      const format = videoFormat(url, mime);
      const isPlaylist = ['hls', 'dash'].includes(format);
      item.format = format;
      item.isPlaylist = isPlaylist;
      item.conversionPath = isPlaylist ? 'companion-assembly' : 'direct-download';
      item.downloadEligibility = isPlaylist ? 'requires-companion' : 'eligible';
      const codecMatch = /codecs\s*=\s*["']?([^"';]+)["']?/i.exec(mime || '');
      item.codec = codecMatch ? codecMatch[1].trim() : (extra.codec || null);
      item.resolution = w > 0 && h > 0 ? `${w}×${h}` : (extra.resolution || null);
      item.hasAudio = extra.hasAudio ?? null;
      item.hasSubtitles = Boolean(extra.subtitles && extra.subtitles.length > 0);
      if (item.hasSubtitles) item.subtitles = extra.subtitles;
      if (extra.poster) item.poster = extra.poster;
      if (extra.duration) item.duration = extra.duration;
    }
    assets.push(item);
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
  function parseTracks(mediaEl) {
    const tracks = [];
    if (!mediaEl || typeof mediaEl.querySelectorAll !== 'function') return tracks;
    try {
      const list = mediaEl.querySelectorAll('track') || [];
      for (const track of list) {
        const src = safeUrl(track.getAttribute('src'));
        if (src) {
          tracks.push({
            src,
            kind: track.getAttribute('kind') || 'subtitles',
            srclang: track.getAttribute('srclang') || '',
            label: (track.getAttribute('label') || '').slice(0, 50)
          });
        }
      }
    } catch (_) { /* defensive */ }
    return tracks;
  }
  function scanVideoElement(video) {
    if (!video || blockedVideo) return;
    const w = video.videoWidth || Number(video.getAttribute('width')) || 0;
    const h = video.videoHeight || Number(video.getAttribute('height')) || 0;
    const tracks = parseTracks(video);
    const mime = video.getAttribute('type') || '';
    const poster = safeUrl(video.getAttribute('poster'));
    const duration = Number.isFinite(video.duration) && video.duration > 0 ? Math.round(video.duration) : null;

    if (poster) {
      add('image', poster, (video.getAttribute('title') || 'Video Poster') + ' (Poster)', 'poster');
    }

    const src = firstHttp(
      video.currentSrc,
      video.getAttribute('src'),
      video.getAttribute('data-src'),
      video.getAttribute('data-hls'),
      video.getAttribute('data-video-src'),
      video.getAttribute('data-manifest'),
      video.getAttribute('data-stream'),
      video.getAttribute('data-dash'),
      video.getAttribute('data-file'),
      video.getAttribute('data-media-url'),
      video.getAttribute('data-orig-url'),
      video.getAttribute('data-hls-src'),
      video.getAttribute('data-mpd-src')
    );
    if (src) {
      add('video', src, video.getAttribute('title') || video.getAttribute('aria-label'), 'video', w, h, mime,
        {subtitles: tracks, poster, duration});
    }
    const sources = (typeof video.querySelectorAll === 'function') ? (video.querySelectorAll('source[src],source[data-src]') || []) : [];
    for (const source of sources) {
      const sSrc = firstHttp(source.getAttribute('src'), source.getAttribute('data-src'), source.getAttribute('data-stream'));
      const sMime = source.getAttribute('type') || '';
      const sW = Number(source.getAttribute('width') || source.getAttribute('res')) || w;
      const sH = Number(source.getAttribute('height')) || h;
      if (sSrc && classifyVideo(sSrc, sMime)) {
        add('video', sSrc, video.getAttribute('title') || source.getAttribute('title'), 'video', sW, sH, sMime,
          {subtitles: tracks, poster, duration});
      }
    }
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
      scanVideoElement(video);
      if (assets.length >= LIMIT) break;
    }
    // Modern dynamic web component players (Video.js, Plyr, media-player, shadow DOM)
    let playersChecked = 0;
    try {
      const dynamicList = document.querySelectorAll('video-js, plyr, media-player, video-player, [data-player], .jwplayer, .vjs-tech') || [];
      for (const container of dynamicList) {
        if (++playersChecked > 50 || assets.length >= LIMIT) break;
        // Shadow root traversal (up to 2 levels)
        if (container.shadowRoot && typeof container.shadowRoot.querySelectorAll === 'function') {
          for (const shadowVideo of container.shadowRoot.querySelectorAll('video')) {
            scanVideoElement(shadowVideo);
          }
          for (const subContainer of container.shadowRoot.querySelectorAll('video-js, plyr, media-player, video-player')) {
            if (subContainer.shadowRoot && typeof subContainer.shadowRoot.querySelectorAll === 'function') {
              for (const innerVideo of subContainer.shadowRoot.querySelectorAll('video')) {
                scanVideoElement(innerVideo);
              }
            }
          }
        }
        const directDataSrc = firstHttp(
          container.getAttribute('data-src'), container.getAttribute('data-video-src'),
          container.getAttribute('data-hls'), container.getAttribute('data-stream'),
          container.getAttribute('data-manifest'), container.getAttribute('data-file'),
          container.getAttribute('data-media-url'), container.getAttribute('data-hls-src')
        );
        if (directDataSrc && classifyVideo(directDataSrc)) {
          add('video', directDataSrc, container.getAttribute('title') || container.getAttribute('aria-label'), 'dynamic-player');
        }
      }
    } catch (_) { /* ignore if not queryable */ }

    // Same-origin iframe scanning (bounded to 6 frames, safe from cross-origin errors)
    try {
      const iframes = document.querySelectorAll('iframe');
      let framesChecked = 0;
      for (const frame of iframes) {
        if (++framesChecked > 6 || assets.length >= LIMIT) break;
        try {
          const doc = frame.contentDocument || frame.contentWindow?.document;
          if (doc && typeof doc.querySelectorAll === 'function') {
            for (const v of doc.querySelectorAll('video')) scanVideoElement(v);
          }
        } catch (_) { /* cross-origin frame - expected and cleanly skipped */ }
      }
    } catch (_) { /* defensive */ }
  }
  for (const audio of document.querySelectorAll('audio')) {
    add('audio', firstHttp(audio.currentSrc, audio.getAttribute('src'), audio.getAttribute('data-src')),
      audio.getAttribute('title') || audio.getAttribute('aria-label'), 'audio');
    const sources = (typeof audio.querySelectorAll === 'function') ? (audio.querySelectorAll('source[src],source[data-src]') || []) : [];
    for (const source of sources) {
      const sSrc = firstHttp(source.getAttribute('src'), source.getAttribute('data-src'));
      const sMime = source.getAttribute('type') || '';
      if (sSrc && classifyAudio(sSrc, sMime)) {
        add('audio', sSrc, audio.getAttribute('title'), 'audio');
      }
    }
    if (assets.length >= LIMIT) break;
  }
  // Only direct media formats from OpenGraph; no playlist, page player or DRM.
  for (const meta of document.querySelectorAll('meta[property="og:image"],meta[property="og:image:url"],meta[name="twitter:image"],meta[property="og:video"],meta[property="og:video:url"],meta[property="og:video:secure_url"],meta[property="og:audio"],meta[property="og:audio:secure_url"],meta[name="twitter:player:stream"]')) {
    const tag = meta.getAttribute('property') || meta.getAttribute('name') || '';
    const value = meta.getAttribute('content');
    const type = tag.includes('image') ? 'image' : tag.includes('audio') ? 'audio' : 'video';
    if (value && (type === 'video' ? classifyVideo(value) : extensions[type].test(value))) add(type, value, '', 'meta');
    if (assets.length >= LIMIT) break;
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
      if (type === 'video' ? classifyVideo(url, link.getAttribute('type')) : (type === 'audio' ? classifyAudio(url, link.getAttribute('type')) : extensions[type].test(url))) {
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
          const w = Number(value.width) || 0;
          const h = Number(value.height) || 0;
          const poster = safeUrl(value.thumbnailUrl || value.thumbnail);
          add('video', content, value.name || '', 'structured-data', w, h, mime, {poster});
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

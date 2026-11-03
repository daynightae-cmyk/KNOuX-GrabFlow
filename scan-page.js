'use strict';
/**
 * On-demand, same-tab DOM scanner. No network interception, background tracking,
 * cookies, authenticated fetches, playlist ripping, or DRM bypass.
 * This function is self-contained because chrome.scripting.executeScript serializes it.
 */
function scanPageAssets() {
  const MAX_ASSETS = 600;
  const assets = [];
  const seen = new Map();
  const blockedVideo = /(^|\.)(youtube\.com|youtube-nocookie\.com|youtu\.be)$/i.test(location.hostname);
  const fileTypes = {
    image: /\.(?:jpe?g|png|webp|gif|svg|avif|bmp|tiff?)(?:[?#]|$)/i,
    video: /\.(?:mp4|webm|ogv|mov|m4v)(?:[?#]|$)/i,
    document: /\.(?:pdf|docx?|xlsx?|pptx?|txt|csv|epub|zip|rar|7z|json|md)(?:[?#]|$)/i
  };

  function safeUrl(value) {
    if (typeof value !== 'string' || !value.trim()) return null;
    try {
      const u = new URL(value.trim(), document.baseURI);
      if (!['https:', 'http:'].includes(u.protocol) || u.username || u.password) return null;
      return u.href;
    } catch (_) { return null; }
  }
  function add(type, value, label, source = 'dom', width = 0, height = 0) {
    if (assets.length >= MAX_ASSETS || !['image','video','document'].includes(type)) return;
    const url = safeUrl(value);
    if (!url || (blockedVideo && type === 'video')) return;
    if (seen.has(url)) {
      const prior = assets[seen.get(url)];
      if (prior && !prior.width && width) { prior.width = width; prior.height = height; }
      return;
    }
    let name = String(label || '').replace(/\s+/g, ' ').trim();
    if (!name) {
      try { name = decodeURIComponent(new URL(url).pathname.split('/').pop() || ''); }
      catch (_) { name = ''; }
    }
    // Store the full URL for the user, but never interpolate it into HTML.
    seen.set(url, assets.length);
    assets.push({type, url, name: name.slice(0, 140) || `${type} asset`, source,
      width: Number.isFinite(width) && width > 0 ? Math.trunc(width) : 0,
      height: Number.isFinite(height) && height > 0 ? Math.trunc(height) : 0});
  }
  function bestSrcset(value) {
    if (!value) return '';
    const candidates = value.split(',').map(v => {
      const parts = v.trim().split(/\s+/);
      const descriptor = parts[1] || '';
      const weight = /^\d+(?:\.\d+)?w$/.test(descriptor) || /^\d+(?:\.\d+)?x$/.test(descriptor)
        ? parseFloat(descriptor) : 0;
      return {url: parts[0], weight};
    }).filter(x => x.url);
    candidates.sort((a, b) => b.weight - a.weight);
    return candidates[0]?.url || '';
  }
  for (const img of document.querySelectorAll('img')) {
    const url = img.currentSrc || img.getAttribute('data-src') || img.getAttribute('src') ||
      bestSrcset(img.getAttribute('data-srcset') || img.getAttribute('srcset'));
    add('image', url, img.getAttribute('alt') || img.getAttribute('title'), 'image', img.naturalWidth, img.naturalHeight);
    if (assets.length >= MAX_ASSETS) break;
  }
  if (!blockedVideo) {
    for (const video of document.querySelectorAll('video')) {
      add('video', video.currentSrc || video.getAttribute('src'), video.getAttribute('title') || video.getAttribute('aria-label'), 'video');
      for (const source of video.querySelectorAll('source[src]'))
        add('video', source.getAttribute('src'), video.getAttribute('title'), 'video');
    }
    for (const meta of document.querySelectorAll('meta[property="og:video"],meta[property="og:video:url"],meta[property="og:video:secure_url"]')) {
      const url = meta.getAttribute('content');
      if (fileTypes.video.test(url || '')) add('video', url, 'Page video', 'meta');
    }
  }
  // Only inline CSS explicitly naming a background image; no expensive full-page
  // computed-style traversal, stylesheet fetching, or JavaScript execution.
  let sampled = 0;
  for (const node of document.querySelectorAll('[style*="background"]')) {
    if (++sampled > 300 || assets.length >= MAX_ASSETS) break;
    const style = node.getAttribute('style') || '';
    const match = /background(?:-image)?\s*:[^;]*?url\(\s*["']?([^)'"\s]+)["']?\s*\)/i.exec(style);
    if (match) add('image', match[1], node.getAttribute('aria-label') || node.getAttribute('title'), 'background');
  }
  for (const link of document.querySelectorAll('a[href]')) {
    const url = link.getAttribute('href');
    if (!url) continue;
    const name = link.getAttribute('download') || link.getAttribute('aria-label') || link.textContent;
    if (fileTypes.image.test(url)) add('image', url, name, 'link');
    else if (fileTypes.document.test(url)) add('document', url, name, 'link');
    else if (!blockedVideo && fileTypes.video.test(url)) add('video', url, name, 'link');
    if (assets.length >= MAX_ASSETS) break;
  }
  return {
    title: String(document.title || '').slice(0, 150),
    domain: location.hostname, pageUrl: location.href, assets,
    truncated: assets.length >= MAX_ASSETS
  };
}

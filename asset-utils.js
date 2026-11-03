'use strict';
/** Deterministic helpers for filtering, export and safe Downloads API file names. */
function filterSortAssets(assets, {type = 'all', query = '', sort = 'page', largeImages = false} = {}) {
  const needle = String(query).toLocaleLowerCase().trim();
  const result = assets.filter(a =>
    (type === 'all' || a.type === type) &&
    (!largeImages || a.type !== 'image' || Math.max(a.width || 0, a.height || 0) >= 800) &&
    (!needle || `${a.name} ${a.url}`.toLocaleLowerCase().includes(needle)));
  if (sort === 'name') result.sort((a, b) => a.name.localeCompare(b.name));
  if (sort === 'type') result.sort((a, b) => a.type.localeCompare(b.type) || a.name.localeCompare(b.name));
  return result;
}

function safeDownloadName(asset, index, pageDomain) {
  const allowed = {image: '.png', video: '.mp4', audio: '.mp3', document: '.bin'};
  let ext = allowed[asset.type] || '.bin';
  if (asset.type === 'video') {
    if (asset.format === 'webm' || /\.webm(?:[?#]|$)/i.test(asset.url)) ext = '.webm';
    else if (asset.format === 'mkv' || /\.mkv(?:[?#]|$)/i.test(asset.url)) ext = '.mkv';
    else if (asset.format === 'mov' || /\.mov(?:[?#]|$)/i.test(asset.url)) ext = '.mov';
  } else if (asset.type === 'audio') {
    if (/\.flac(?:[?#]|$)/i.test(asset.url)) ext = '.flac';
    else if (/\.opus(?:[?#]|$)/i.test(asset.url)) ext = '.opus';
    else if (/\.wav(?:[?#]|$)/i.test(asset.url)) ext = '.wav';
    else if (/\.m4a(?:[?#]|$)/i.test(asset.url)) ext = '.m4a';
    else if (/\.ogg(?:[?#]|$)/i.test(asset.url)) ext = '.ogg';
  }
  let last = '';
  try { last = decodeURIComponent(new URL(asset.url).pathname.split('/').pop() || ''); }
  catch (_) { /* malicious or broken encoding */ }
  let name = last && /\.[a-z0-9]{2,7}$/i.test(last) ? last : `${asset.type}-${index}${ext}`;
  name = name.replace(/[<>:"/\\|?*\x00-\x1f]/g, '_').replace(/^[. ]+|[. ]+$/g, '').slice(0, 100);
  if (!name || /^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(name)) name = `asset-${index}${ext}`;
  const domain = String(pageDomain || 'website').replace(/[^a-z0-9.\-_]/gi, '_').slice(0, 70) || 'website';
  return `KNOuX-GrabFlow/${domain}/${name}`;
}

function isDownloadableAsset(asset) {
  // HLS/DASH manifests must be assembled into a movie by a dedicated converter.
  return !!asset && (asset.type !== 'video' || !['hls', 'dash'].includes(asset.format));
}

function classifyMediaAsset(asset) {
  if (!asset || typeof asset !== 'object') return null;
  const isVideo = asset.type === 'video';
  const format = asset.format || (isVideo ? 'direct' : null);
  const isPlaylist = isVideo && ['hls', 'dash'].includes(format);
  return {
    url: asset.url || '',
    mediaType: asset.type || 'unknown',
    sourceType: asset.source || 'dom',
    detectionMethod: asset.source || 'dom',
    isPlaylist,
    format: format || 'direct',
    codec: asset.codec || null,
    resolution: asset.resolution || (asset.width && asset.height ? `${asset.width}×${asset.height}` : null),
    bitrate: asset.bitrate || null,
    hasAudio: asset.hasAudio ?? (isVideo ? null : true),
    hasSubtitles: Boolean(asset.hasSubtitles || (asset.subtitles && asset.subtitles.length > 0)),
    subtitles: Array.isArray(asset.subtitles) ? asset.subtitles : [],
    supportedConversionPath: isPlaylist ? 'companion-assembly' : 'direct-download',
    downloadEligibility: isPlaylist ? 'requires-companion' : 'eligible',
    confidence: asset.source === 'resource-timing' ? 'medium' : 'high'
  };
}

function summarizeDownloads(items) {
  const counts = {complete: 0, running: 0, interrupted: 0, missing: 0};
  for (const item of items) {
    if (!item) counts.missing++;
    else if (item.state === 'complete') counts.complete++;
    else if (item.state === 'interrupted') counts.interrupted++;
    else counts.running++;
  }
  return counts;
}

function exportAssetsCsv(assets) {
  const quote = v => {
    let text = String(v ?? '');
    if (/^\s*[=+@-]/.test(text)) text = `'${text}`; // spreadsheet formula injection
    return `"${text.replace(/"/g, '""')}"`;
  };
  return [['type','name','url','width','height','source','format'].join(','), ...assets.map(a =>
    [a.type, a.name, a.url, a.width || '', a.height || '', a.source || 'dom', a.format || ''].map(quote).join(','))].join('\r\n');
}

if (typeof module !== 'undefined') module.exports = {
  filterSortAssets, safeDownloadName, exportAssetsCsv, isDownloadableAsset, classifyMediaAsset, summarizeDownloads
};

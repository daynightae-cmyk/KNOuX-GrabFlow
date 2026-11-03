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
  const ext = allowed[asset.type] || '.bin';
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
if (typeof module !== 'undefined') module.exports = {filterSortAssets, safeDownloadName, exportAssetsCsv, isDownloadableAsset, summarizeDownloads};

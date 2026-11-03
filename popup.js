'use strict';

const ui = Object.fromEntries([
  'langBtn','refreshBtn','totalCount','pageHost','search','results','selectedLabel',
  'selectVisible','clearSelection','copyBtn','downloadBtn','notice','countAll',
  'countImage','countVideo','countAudio','countDocument','sortMode','largeImages','csvBtn','downloadStatus'
].map(id => [id, document.getElementById(id)]));

const dictionary = {
  en: {
    heroNote: 'LOCAL • PRIVATE • ON DEMAND', detected: 'Assets detected on this page',
    all: 'All', images: 'Images', videos: 'Video', audio: 'Audio', docs: 'Files',
    selectVisible: 'Select visible', clear: 'Clear', copy: 'Copy links', download: 'Download selected',
    privacy: 'No tracking. No uploads. No accounts.', legal: 'Only download content you may use',
    scanning: 'Scanning page…', noAssets: 'No directly accessible assets found on this page.',
    noMatch: 'No matches. Try another filter.', restricted: 'This page cannot be scanned. Open a normal website.',
    selected: n => `${n} selected`, search: 'Filter by name or URL…', copied: 'Selected links copied.',
    copyFail: 'Unable to copy links.', scanFail: 'Could not inspect this tab.',
    selectFirst: 'Select at least one asset.', max: 'For safety, download at most 30 files per batch.',
    done: (ok, fail) => `Downloads started: ${ok}${fail ? ` · Could not start: ${fail}` : ''}`,
    downloading: (done, total) => `Starting downloads ${done}/${total}…`,
    blocked: 'Some files may be unavailable or require website permission.',
    typeImage: 'IMAGE', typeVideo: 'VIDEO', typeAudio: 'AUDIO', typeDocument: 'FILE',
    sortBy: 'Sort', pageOrder: 'Page order', sortName: 'Name A–Z', sortType: 'File type',
    largeOnly: 'Large images', exportCsv: 'CSV', csvCopied: 'CSV copied for the visible results.',
    streamHint: 'Stream playlist — needs a converter to produce one playable video.',
    streamNotDirect: 'HLS/DASH playlists cannot be saved as complete videos with Chrome Downloads. Copy the links for an authorized converter.',
    streamSkipped: n => `${n} streaming playlists skipped (copy their links for a converter).`,
    downloadProgress: (c,r,f) => `Downloaded: ${c} complete · ${r} running · ${f} failed`,
  },
  ar: {
    heroNote: 'محلي • خصوصية • عند الطلب', detected: 'ملف قابل للاكتشاف في الصفحة',
    all: 'الكل', images: 'الصور', videos: 'فيديو', audio: 'صوت', docs: 'ملفات',
    selectVisible: 'تحديد الظاهر', clear: 'إلغاء', copy: 'نسخ الروابط', download: 'تحميل المحدد',
    privacy: 'بدون تتبع أو رفع ملفات أو حساب.', legal: 'حمّل المحتوى المسموح لك فقط',
    scanning: 'جارٍ فحص الصفحة…', noAssets: 'لم يتم اكتشاف ملفات مباشرة قابلة للوصول.',
    noMatch: 'لا توجد نتائج مطابقة. غيّر الفلتر.', restricted: 'لا يمكن فحص الصفحة دي. افتح موقع ويب عادي.',
    selected: n => `${n} محدد`, search: 'فلترة بالاسم أو الرابط…', copied: 'تم نسخ الروابط المحددة.',
    copyFail: 'تعذر نسخ الروابط.', scanFail: 'تعذر فحص التبويب الحالي.',
    selectFirst: 'حدد ملفًا واحدًا على الأقل.', max: 'للأمان، الحد الأقصى 30 ملفًا في الدفعة.',
    done: (ok, fail) => `بدأ تحميل ${ok}${fail ? ` · تعذر بدء ${fail}` : ''}`,
    downloading: (done, total) => `بدء التحميل ${done}/${total}…`,
    blocked: 'قد تتطلب بعض الملفات صلاحيات من الموقع أو تكون غير متاحة.',
    typeImage: 'صورة', typeVideo: 'فيديو', typeAudio: 'صوت', typeDocument: 'ملف',
    sortBy: 'الترتيب', pageOrder: 'ترتيب الصفحة', sortName: 'بالاسم', sortType: 'نوع الملف',
    largeOnly: 'الصور الكبيرة', exportCsv: 'CSV', csvCopied: 'تم نسخ CSV للنتائج الظاهرة.',
    streamHint: 'قائمة بث تحتاج تجميعًا لإنتاج فيديو واحد قابل للتشغيل.',
    streamNotDirect: 'قوائم HLS/DASH ليست ملفات فيديو كاملة. انسخ الرابط واستخدم محوّلًا مصرحًا به.',
    streamSkipped: n => `تم تجاوز ${n} قائمة بث؛ يمكن نسخ روابطها للمحوّل.`,
    downloadProgress: (c,r,f) => `التنزيل: ${c} مكتمل · ${r} جارٍ · ${f} فشل`,
  }
};

const state = {lang: 'en', assets: [], selected: new Set(), filter: 'all', busy: false, tab: null, page: null};
const t = (key, ...args) => {
  const value = dictionary[state.lang][key] || key;
  return typeof value === 'function' ? value(...args) : value;
};
function translate() {
  document.documentElement.lang = state.lang;
  document.documentElement.dir = state.lang === 'ar' ? 'rtl' : 'ltr';
  ui.langBtn.textContent = state.lang === 'ar' ? 'English' : 'عربي';
  document.querySelectorAll('[data-i18n]').forEach(node => { node.textContent = t(node.dataset.i18n); });
  ui.search.placeholder = t('search');
  ui.selectedLabel.textContent = t('selected', state.selected.size);
  if (state.page) render();
  if (!ui.downloadStatus.hidden) restoreDownloadStatus();
}
function notice(message, error = false) {
  ui.notice.hidden = !message;
  ui.notice.classList.toggle('error', error);
  ui.notice.textContent = message || '';
}
function visibleAssets() {
  const query = ui.search.value.toLocaleLowerCase().trim();
  return filterSortAssets(state.assets, {type: state.filter, query, sort: ui.sortMode.value, largeImages: ui.largeImages.checked});
}
function setBusy(busy) {
  state.busy = busy;
  ui.refreshBtn.disabled = busy;
  ui.selectVisible.disabled = busy;
  ui.clearSelection.disabled = busy;
  renderButtons();
}
function renderButtons() {
  const hasSelection = state.selected.size > 0;
  const hasDownloadable = selectedAssets().some(isDownloadableAsset);
  ui.copyBtn.disabled = state.busy || !hasSelection;
  ui.downloadBtn.disabled = state.busy || !hasDownloadable;
  ui.selectedLabel.textContent = t('selected', state.selected.size);
}
function empty(message) {
  ui.results.replaceChildren();
  const block = document.createElement('div');
  block.className = 'empty';
  const emblem = document.createElement('div');
  emblem.className = 'empty-orbit';
  emblem.textContent = '◇';
  const content = document.createElement('div');
  content.textContent = message;
  block.append(emblem, content);
  ui.results.append(block);
}
function render() {
  const counts = {all: state.assets.length, image: 0, video: 0, document: 0, audio: 0};
  for (const asset of state.assets) counts[asset.type]++;
  ui.countAll.textContent = counts.all;
  ui.countImage.textContent = counts.image;
  ui.countVideo.textContent = counts.video;
  ui.countDocument.textContent = counts.document;
  ui.countAudio.textContent = counts.audio;
  ui.totalCount.textContent = String(counts.all).padStart(2, '0');
  const shown = visibleAssets();
  renderButtons();
  if (!state.assets.length) { empty(t('noAssets')); return; }
  if (!shown.length) { empty(t('noMatch')); return; }
  const fragment = document.createDocumentFragment();
  for (const asset of shown) {
    const row = document.createElement('label');
    row.className = 'asset';
    row.classList.toggle('selected', state.selected.has(asset.url));
    row.classList.toggle('stream', asset.type === 'video' && !isDownloadableAsset(asset));
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = state.selected.has(asset.url);
    checkbox.disabled = state.busy;
    checkbox.setAttribute('aria-label', asset.name);
    checkbox.addEventListener('change', () => {
      if (checkbox.checked) state.selected.add(asset.url);
      else state.selected.delete(asset.url);
      row.classList.toggle('selected', checkbox.checked);
      renderButtons();
    });
    const icon = document.createElement('span');
    icon.className = 'asset-icon';
    icon.textContent = {image: '▧', video: '▷', document: '▤', audio: '♫'}[asset.type];
    const info = document.createElement('span');
    info.className = 'asset-info';
    const name = document.createElement('div');
    name.className = 'asset-name';
    name.textContent = asset.name;
    name.title = asset.name;
    const url = document.createElement('div');
    url.className = 'asset-url';
    url.textContent = asset.url;
    url.title = asset.url;
    info.append(name, url);
    if (asset.type === 'video') {
      const format = document.createElement('div');
      format.className = 'asset-format';
      format.textContent = (asset.format === 'hls' ? 'HLS · M3U8' : asset.format === 'dash' ? 'DASH · MPD' : 'VIDEO FILE');
      if (!isDownloadableAsset(asset)) format.title = t('streamHint');
      info.append(format);
    }
    if (asset.type === 'image' && asset.width && asset.height) {
      const dimensions = document.createElement('div');
      dimensions.className = 'asset-meta';
      dimensions.textContent = `${asset.width} × ${asset.height} px`;
      info.append(dimensions);
    }
    const badge = document.createElement('span');
    badge.className = 'asset-type';
    badge.textContent = t(`type${asset.type[0].toUpperCase()}${asset.type.slice(1)}`);
    row.append(checkbox, icon, info, badge);
    fragment.append(row);
  }
  ui.results.replaceChildren(fragment);
}
function applyScannedPage(result) {
  if (!result || !Array.isArray(result.assets)) throw new Error('Invalid scan result');
  state.page = result;
  state.assets = result.assets.filter(a => ['image', 'video', 'audio', 'document'].includes(a?.type) &&
    typeof a?.url === 'string' && /^https?:\/\//i.test(a.url));
  state.selected.clear();
  ui.pageHost.textContent = result.domain || '—';
  render();
  if (result.truncated) notice(state.lang === 'ar' ? 'تم عرض أول 600 نتيجة.' : 'Showing the first 600 results.');
}
async function scan() {
  setBusy(true);
  notice('');
  ui.totalCount.textContent = '··';
  empty(t('scanning'));
  try {
    const tabs = await chrome.tabs.query({active: true, currentWindow: true});
    const tab = tabs && tabs[0];
    if (!tab || !/^https?:\/\//i.test(tab.url || '')) {
      state.page = null;
      state.assets = [];
      state.selected.clear();
      ui.totalCount.textContent = '00';
      ui.pageHost.textContent = '—';
      empty(t('restricted'));
      return;
    }
    state.tab = tab;
    const response = await chrome.scripting.executeScript({target: {tabId: tab.id}, func: scanPageAssets});
    applyScannedPage(response?.[0]?.result);
  } catch (error) {
    state.page = null;
    state.assets = [];
    state.selected.clear();
    ui.totalCount.textContent = '00';
    ui.pageHost.textContent = '—';
    empty(t('scanFail'));
    notice(error?.message || t('scanFail'), true);
  } finally {
    setBusy(false);
  }
}
function selectedAssets() { return state.assets.filter(asset => state.selected.has(asset.url)); }
async function downloadSelected() {
  const allSelected = selectedAssets();
  const chosen = allSelected.filter(isDownloadableAsset);
  const skipped = allSelected.length - chosen.length;
  if (!chosen.length && skipped) { notice(t('streamNotDirect'), true); return; }
  if (!chosen.length) { notice(t('selectFirst'), true); return; }
  if (chosen.length > 30) { notice(t('max'), true); return; }
  setBusy(true);
  let success = 0, failures = 0;
  const ids = [];
  try {
    for (let index = 0; index < chosen.length; index++) {
      const asset = chosen[index];
      notice(t('downloading', index + 1, chosen.length));
      try {
        const id = await chrome.downloads.download({
          url: asset.url, filename: safeDownloadName(asset, index + 1, state.page?.domain), conflictAction: 'uniquify', saveAs: false
        });
        if (typeof id === 'number') { success++; ids.push(id); } else failures++;
      } catch (_) { failures++; }
    }
    // Persist IDs only: reopening the popup reconciles Chrome's real download states.
    if (ids.length) {
      try { await chrome.storage.local.set({downloadRuns: ids.slice(-30)}); } catch (_) { /* optional */ }
    }
    const suffix = skipped ? ` · ${t('streamSkipped', skipped)}` : '';
    notice(t('done', success, failures) + suffix, failures > 0 || skipped > 0);
    if (ids.length) await refreshDownloadStatus(ids);
  } finally { setBusy(false); }
}

async function refreshDownloadStatus(ids) {
  if (!Array.isArray(ids) || !ids.length || !chrome.downloads?.search) return;
  const items = await Promise.all(ids.map(id => chrome.downloads.search({id}).then(x => x?.[0] || null).catch(() => null)));
  const totals = summarizeDownloads(items);
  ui.downloadStatus.hidden = false;
  ui.downloadStatus.textContent = t('downloadProgress', totals.complete, totals.running, totals.interrupted + totals.missing);
}
async function restoreDownloadStatus() {
  try {
    const data = await chrome.storage.local.get(['downloadRuns']);
    await refreshDownloadStatus(data.downloadRuns);
  } catch (_) { /* download history is optional, never blocks the page scan */ }
}
if (chrome.downloads?.onChanged?.addListener) {
  chrome.downloads.onChanged.addListener(() => {
    chrome.storage.local.get(['downloadRuns']).then(data => refreshDownloadStatus(data.downloadRuns)).catch(() => {});
  });
}
ui.langBtn.addEventListener('click', async () => {
  state.lang = state.lang === 'en' ? 'ar' : 'en';
  translate();
  try { await chrome.storage.local.set({language: state.lang}); } catch (_) { /* optional */ }
});
ui.refreshBtn.addEventListener('click', scan);
ui.search.addEventListener('input', render);
ui.sortMode.addEventListener('change', render);
ui.largeImages.addEventListener('change', render);
ui.csvBtn.addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(exportAssetsCsv(visibleAssets())); notice(t('csvCopied')); }
  catch (_) { notice(t('copyFail'), true); }
});
document.querySelectorAll('[data-filter]').forEach(tab => tab.addEventListener('click', () => {
  state.filter = tab.dataset.filter;
  document.querySelectorAll('[data-filter]').forEach(t => {
    t.classList.toggle('active', t.dataset.filter === state.filter);
    t.setAttribute('aria-pressed', String(t.dataset.filter === state.filter));
  });
  render();
}));
ui.selectVisible.addEventListener('click', () => {
  for (const asset of visibleAssets()) state.selected.add(asset.url);
  render();
});
ui.clearSelection.addEventListener('click', () => { state.selected.clear(); render(); });
ui.copyBtn.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(selectedAssets().map(asset => asset.url).join('\n'));
    notice(t('copied'));
  } catch (_) { notice(t('copyFail'), true); }
});
ui.downloadBtn.addEventListener('click', downloadSelected);
(async () => {
  try {
    const settings = await chrome.storage.local.get(['language']);
    state.lang = settings.language === 'ar' || settings.language === 'en'
      ? settings.language : (navigator.language.toLowerCase().startsWith('ar') ? 'ar' : 'en');
  } catch (_) { state.lang = 'en'; }
  translate();
  await Promise.all([scan(), restoreDownloadStatus()]);
})();

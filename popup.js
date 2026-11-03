'use strict';

const ui = Object.fromEntries([
  'langBtn', 'refreshBtn', 'totalCount', 'pageHost', 'search', 'results', 'selectedLabel',
  'selectVisible', 'clearSelection', 'copyBtn', 'downloadBtn', 'notice', 'countAll',
  'countImage', 'countVideo', 'countStream', 'countAudio', 'countDocument', 'sortMode', 'largeImages',
  'csvBtn', 'exportJsonBtn', 'downloadStatus', 'managerToggleBtn', 'scannerView', 'managerView',
  'managerList', 'managerCount', 'clearHistoryBtn', 'companionStatus',
  'previewModal', 'previewBackdrop', 'previewTitle', 'previewCloseBtn', 'previewContent',
  'previewMeta', 'previewCopyBtn', 'previewActionBtn'
].map(id => [id, document.getElementById(id)]));

const dictionary = {
  en: {
    heroNote: 'LOCAL • PRIVATE • ON DEMAND', detected: 'Assets detected on this page',
    all: 'All', images: 'Images', videos: 'Video', streams: 'Streams', audio: 'Audio', docs: 'Files',
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
    largeOnly: 'Large images', exportCsv: 'CSV', exportJson: 'JSON',
    csvCopied: 'CSV copied for visible results.', jsonCopied: 'Structured JSON copied for visible results.',
    streamHint: 'Stream playlist — needs companion to produce one playable video.',
    streamNotDirect: 'HLS/DASH playlists cannot be saved as complete videos with Chrome Downloads alone. Use the KNOuX Native Companion or copy links.',
    streamSkipped: n => `${n} streaming playlists skipped (use Assemble button or copy links).`,
    downloadProgress: (c, r, f) => `Downloads: ${c} complete · ${r} running · ${f} failed`,
    downloadManagerTitle: 'Download Manager', clearHistory: 'Clear History',
    noDownloads: 'No active or recent downloads.', openFile: 'Open', showFolder: 'Folder',
    retry: 'Retry', cancel: 'Cancel', stateComplete: 'Complete', stateInProgress: 'Downloading',
    stateInterrupted: 'Interrupted', stateFailed: 'Failed',
    companionConnected: 'COMPANION: CONNECTED', companionChecking: 'COMPANION: CHECKING', companionMissing: 'COMPANION: NOT INSTALLED',
    subtitlesLabel: n => `${n} SUBTITLES`,
    mediaPreview: 'Media Preview', previewBtn: 'Preview',
    assembleWithCompanion: '⚡ Assemble', copyFfmpeg: '📋 FFmpeg',
    ffmpegCopied: 'FFmpeg assembly command copied! Run in terminal or register companion.',
    assemblyStarted: 'Companion stream assembly started! Tracking in Download Manager.',
    assemblySuccess: 'Stream assembled successfully into single video file.',
    assemblyFailed: 'Stream assembly failed.',
    corsNotice: 'Direct preview blocked by website CORS. Direct download remains intact.'
  },
  ar: {
    heroNote: 'محلي • خصوصية • عند الطلب', detected: 'ملف قابل للاكتشاف في الصفحة',
    all: 'الكل', images: 'الصور', videos: 'فيديو', streams: 'قوائم بث', audio: 'صوت', docs: 'ملفات',
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
    largeOnly: 'الصور الكبيرة', exportCsv: 'CSV', exportJson: 'JSON',
    csvCopied: 'تم نسخ CSV للنتائج الظاهرة.', jsonCopied: 'تم نسخ بيانات JSON المهيكلة للنتائج.',
    streamHint: 'قائمة بث تحتاج المساعد المحلي لإنتاج فيديو كامل.',
    streamNotDirect: 'قوائم HLS/DASH ليست ملفات فيديو مباشرة. استخدم زر التجميع بالمساعد أو انسخ الروابط.',
    streamSkipped: n => `تم تجاوز ${n} قائمة بث؛ استخدم زر التجميع أو انسخ الروابط.`,
    downloadProgress: (c, r, f) => `التنزيل: ${c} مكتمل · ${r} جارٍ · ${f} فشل`,
    downloadManagerTitle: 'إدارة التحميلات', clearHistory: 'مسح السجل',
    noDownloads: 'لا توجد تنزيلات نشطة أو سابقة.', openFile: 'فتح', showFolder: 'المجلد',
    retry: 'إعادة', cancel: 'إلغاء', stateComplete: 'مكتمل', stateInProgress: 'جارٍ التحميل',
    stateInterrupted: 'متوقف', stateFailed: 'فشل',
    companionConnected: 'المساعد: متصل', companionChecking: 'المساعد: جارٍ التحقق', companionMissing: 'المساعد: غير مثبت',
    subtitlesLabel: n => `${n} ترجمة`,
    mediaPreview: 'معاينة الوسائط', previewBtn: 'معاينة',
    assembleWithCompanion: '⚡ تجميع', copyFfmpeg: '📋 أمر FFmpeg',
    ffmpegCopied: 'تم نسخ أمر FFmpeg! شغّله في الطرفية أو سجّل المساعد المحلي.',
    assemblyStarted: 'بدأ تجميع البث عبر المساعد! يمكنك المتابعة في إدارة التحميلات.',
    assemblySuccess: 'تم تجميع قائمة البث بنجاح كملف فيديو موحد.',
    assemblyFailed: 'تعذر تجميع قائمة البث.',
    corsNotice: 'المعاينة المباشرة محجوبة بسياسة CORS من الموقع. التنزيل يعمل بشكل طبيعي.'
  }
};

const state = {
  lang: 'en',
  assets: [],
  selected: new Set(),
  filter: 'all',
  busy: false,
  tab: null,
  page: null,
  view: 'scanner', // 'scanner' | 'manager'
  companion: { connected: false, version: null },
  activeDownloads: new Map(),
  previewingAsset: null
};

const t = (key, ...args) => {
  const value = dictionary[state.lang][key] || key;
  return typeof value === 'function' ? value(...args) : value;
};

function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

function translate() {
  document.documentElement.lang = state.lang;
  document.documentElement.dir = state.lang === 'ar' ? 'rtl' : 'ltr';
  ui.langBtn.textContent = state.lang === 'ar' ? 'English' : 'عربي';
  document.querySelectorAll('[data-i18n]').forEach(node => {
    node.textContent = t(node.dataset.i18n);
  });
  ui.search.placeholder = t('search');
  ui.selectedLabel.textContent = t('selected', state.selected.size);
  if (ui.companionStatus) {
    ui.companionStatus.textContent = state.companion.connected
      ? t('companionConnected') : t('companionMissing');
  }
  if (state.page) render();
  renderDownloads();
  if (!ui.downloadStatus.hidden) restoreDownloadStatus();
}

function notice(message, error = false) {
  ui.notice.hidden = !message;
  ui.notice.classList.toggle('error', error);
  ui.notice.textContent = message || '';
}

function visibleAssets() {
  const query = ui.search.value.toLocaleLowerCase().trim();
  return filterSortAssets(state.assets, {
    type: state.filter,
    query,
    sort: ui.sortMode.value,
    largeImages: ui.largeImages.checked
  });
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
  const counts = {all: state.assets.length, image: 0, video: 0, stream: 0, document: 0, audio: 0};
  for (const asset of state.assets) {
    counts[asset.type]++;
    if (asset.type === 'video' && ['hls', 'dash'].includes(asset.format)) {
      counts.stream++;
    }
  }
  ui.countAll.textContent = counts.all;
  ui.countImage.textContent = counts.image;
  ui.countVideo.textContent = counts.video;
  if (ui.countStream) ui.countStream.textContent = counts.stream;
  ui.countDocument.textContent = counts.document;
  ui.countAudio.textContent = counts.audio;
  ui.totalCount.textContent = String(counts.all).padStart(2, '0');

  const shown = visibleAssets();
  renderButtons();
  if (!state.assets.length) { empty(t('noAssets')); return; }
  if (!shown.length) { empty(t('noMatch')); return; }

  const fragment = document.createDocumentFragment();
  for (const asset of shown) {
    const isStream = asset.type === 'video' && ['hls', 'dash'].includes(asset.format);
    const row = document.createElement('label');
    row.className = 'asset';
    row.classList.toggle('selected', state.selected.has(asset.url));
    row.classList.toggle('stream', isStream);

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
    icon.textContent = {image: '▧', video: isStream ? '⚡' : '▷', document: '▤', audio: '♫'}[asset.type] || '✦';

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

    const badges = document.createElement('div');
    badges.className = 'asset-badges';

    if (asset.type === 'video') {
      const format = document.createElement('span');
      format.className = 'asset-format';
      format.textContent = asset.format === 'hls' ? 'HLS · M3U8'
        : (asset.format === 'dash' ? 'DASH · MPD' : (asset.format ? asset.format.toUpperCase() : 'VIDEO FILE'));
      if (isStream) format.title = t('streamHint');
      badges.append(format);

      if (asset.resolution) {
        const res = document.createElement('span');
        res.className = 'asset-format';
        res.textContent = asset.resolution;
        badges.append(res);
      }
      if (asset.codec) {
        const c = document.createElement('span');
        c.className = 'asset-format';
        c.textContent = asset.codec.slice(0, 16);
        badges.append(c);
      }
      if (asset.duration) {
        const dur = document.createElement('span');
        dur.className = 'asset-meta';
        dur.textContent = formatDuration(asset.duration);
        badges.append(dur);
      }
      if (asset.hasSubtitles && asset.subtitles?.length) {
        const sub = document.createElement('span');
        sub.className = 'asset-subtag';
        sub.textContent = t('subtitlesLabel', asset.subtitles.length);
        badges.append(sub);
      }
    } else if (asset.type === 'image' && asset.width && asset.height) {
      const dimensions = document.createElement('span');
      dimensions.className = 'asset-meta';
      dimensions.textContent = `${asset.width} × ${asset.height} px`;
      badges.append(dimensions);
    }
    if (badges.childNodes.length > 0) info.append(badges);

    // Card Quick Actions (Preview, Assemble, FFmpeg command)
    const actionsBar = document.createElement('div');
    actionsBar.className = 'asset-actions';

    // Preview button
    if (['image', 'video', 'audio'].includes(asset.type) && !isStream) {
      const prevBtn = document.createElement('button');
      prevBtn.type = 'button';
      prevBtn.className = 'btn-card-action';
      prevBtn.textContent = `👁 ${t('previewBtn')}`;
      prevBtn.addEventListener('click', e => {
        e.preventDefault();
        e.stopPropagation();
        openMediaPreview(asset);
      });
      actionsBar.append(prevBtn);
    }

    // Stream Assembly or Copy FFmpeg Command
    if (isStream) {
      if (state.companion.connected) {
        const assembleBtn = document.createElement('button');
        assembleBtn.type = 'button';
        assembleBtn.className = 'btn-card-action btn-assemble';
        assembleBtn.textContent = t('assembleWithCompanion');
        assembleBtn.addEventListener('click', e => {
          e.preventDefault();
          e.stopPropagation();
          assembleStreamViaCompanion(asset);
        });
        actionsBar.append(assembleBtn);
      } else {
        const ffmpegBtn = document.createElement('button');
        ffmpegBtn.type = 'button';
        ffmpegBtn.className = 'btn-card-action';
        ffmpegBtn.textContent = t('copyFfmpeg');
        ffmpegBtn.addEventListener('click', async e => {
          e.preventDefault();
          e.stopPropagation();
          const cmd = generateFfmpegCommand(asset.url, safeDownloadName(asset, 1, state.page?.domain));
          try {
            await navigator.clipboard.writeText(cmd);
            notice(t('ffmpegCopied'));
          } catch (_) {
            notice(t('copyFail'), true);
          }
        });
        actionsBar.append(ffmpegBtn);
      }
    }

    if (actionsBar.childNodes.length > 0) info.append(actionsBar);

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
        const filename = safeDownloadName(asset, index + 1, state.page?.domain);
        const id = await chrome.downloads.download({
          url: asset.url, filename, conflictAction: 'uniquify', saveAs: false
        });
        if (typeof id === 'number') {
          success++;
          ids.push(id);
          recordDownloadJob(id, {
            id, url: asset.url, filename, domain: state.page?.domain,
            format: asset.format || asset.type, state: 'in_progress', bytesReceived: 0, totalBytes: 0
          });
        } else {
          failures++;
        }
      } catch (_) { failures++; }
    }
    if (ids.length) {
      try {
        const stored = await chrome.storage.local.get(['downloadRuns']);
        const prior = Array.isArray(stored.downloadRuns) ? stored.downloadRuns : [];
        const merged = Array.from(new Set([...prior, ...ids])).slice(-50);
        await chrome.storage.local.set({downloadRuns: merged});
      } catch (_) { /* optional */ }
    }
    const suffix = skipped ? ` · ${t('streamSkipped', skipped)}` : '';
    notice(t('done', success, failures) + suffix, failures > 0 || skipped > 0);
    if (ids.length) await refreshDownloadStatus(ids);
  } finally { setBusy(false); }
}

function assembleStreamViaCompanion(asset) {
  if (!chrome.runtime?.sendNativeMessage) {
    notice(t('streamNotDirect'), true);
    return;
  }
  const jobId = `companion-${Date.now()}`;
  const filename = safeDownloadName(asset, state.activeDownloads.size + 1, state.page?.domain);
  recordDownloadJob(jobId, {
    id: jobId,
    url: asset.url,
    filename,
    domain: state.page?.domain,
    format: asset.format,
    state: 'in_progress',
    bytesReceived: 0,
    totalBytes: 0,
    isCompanion: true
  });
  notice(t('assemblyStarted'));
  try {
    chrome.runtime.sendNativeMessage('com.knoux.grabflow.companion', {
      action: 'assemble', url: asset.url, output: filename, jobId
    }, resp => {
      if (chrome.runtime.lastError || !resp || resp.status !== 'complete') {
        const err = chrome.runtime.lastError?.message || resp?.error || t('assemblyFailed');
        recordDownloadJob(jobId, { state: 'failed', error: err });
        notice(err, true);
      } else {
        recordDownloadJob(jobId, {
          state: 'complete',
          bytesReceived: resp.bytes,
          fileSize: resp.bytes,
          filename: resp.output || filename
        });
        notice(t('assemblySuccess'));
      }
    });
  } catch (err) {
    recordDownloadJob(jobId, { state: 'failed', error: err.message });
    notice(err.message, true);
  }
}

function recordDownloadJob(id, details) {
  state.activeDownloads.set(id, { ...(state.activeDownloads.get(id) || {}), ...details });
  renderDownloads();
}

/* Download Manager rendering */
function renderDownloads() {
  if (!ui.managerList) return;
  const items = Array.from(state.activeDownloads.values());
  ui.managerCount.textContent = items.length;
  if (!items.length) {
    ui.managerList.innerHTML = `<div class="empty-downloads"><div class="empty-orbit">▽</div><div>${t('noDownloads')}</div></div>`;
    return;
  }
  const frag = document.createDocumentFragment();
  for (const item of [...items].reverse()) {
    const card = document.createElement('div');
    card.className = 'dl-card';

    const top = document.createElement('div');
    top.className = 'dl-card-top';

    const name = document.createElement('div');
    name.className = 'dl-card-name';
    name.textContent = item.filename ? item.filename.split('/').pop().split('\\').pop() : (item.url ? item.url.split('/').pop() : 'Download');
    name.title = item.url;

    const badge = document.createElement('span');
    const st = item.state || 'in_progress';
    badge.className = `dl-state-badge ${st}`;
    badge.textContent = st === 'complete' ? t('stateComplete')
      : (st === 'interrupted' ? t('stateInterrupted') : (st === 'failed' ? t('stateFailed') : t('stateInProgress')));

    top.append(name, badge);
    card.append(top);

    const progress = document.createElement('div');
    progress.className = 'dl-card-progress';
    const bar = document.createElement('div');
    bar.className = 'dl-card-progress-bar';
    const pct = item.totalBytes > 0 ? Math.min(100, Math.round((item.bytesReceived / item.totalBytes) * 100))
      : (st === 'complete' ? 100 : 30);
    bar.style.width = `${pct}%`;
    progress.append(bar);
    card.append(progress);

    const meta = document.createElement('div');
    meta.className = 'dl-card-meta';

    const sizeInfo = document.createElement('span');
    if (st === 'complete') {
      sizeInfo.textContent = formatBytes(item.fileSize || item.bytesReceived);
    } else if (item.totalBytes > 0) {
      sizeInfo.textContent = `${formatBytes(item.bytesReceived)} / ${formatBytes(item.totalBytes)} (${pct}%)`;
    } else if (item.bytesReceived > 0) {
      sizeInfo.textContent = formatBytes(item.bytesReceived);
    } else {
      sizeInfo.textContent = item.domain || '';
    }

    const actions = document.createElement('div');
    actions.className = 'dl-actions';

    if (st === 'complete') {
      const openBtn = document.createElement('button');
      openBtn.type = 'button';
      openBtn.className = 'dl-action-btn';
      openBtn.textContent = t('openFile');
      openBtn.addEventListener('click', () => {
        if (typeof item.id === 'number' && chrome.downloads?.open) chrome.downloads.open(item.id);
      });
      const showBtn = document.createElement('button');
      showBtn.type = 'button';
      showBtn.className = 'dl-action-btn';
      showBtn.textContent = t('showFolder');
      showBtn.addEventListener('click', () => {
        if (typeof item.id === 'number' && chrome.downloads?.show) chrome.downloads.show(item.id);
      });
      if (typeof item.id === 'number') actions.append(openBtn, showBtn);
    } else if (st === 'interrupted' || st === 'failed') {
      const retryBtn = document.createElement('button');
      retryBtn.type = 'button';
      retryBtn.className = 'dl-action-btn';
      retryBtn.textContent = t('retry');
      retryBtn.addEventListener('click', () => {
        if (item.isCompanion) {
          assembleStreamViaCompanion({url: item.url, format: item.format, name: item.filename});
        } else {
          chrome.downloads?.download({url: item.url, filename: item.filename, conflictAction: 'uniquify'});
        }
      });
      actions.append(retryBtn);
    } else if (st === 'in_progress') {
      const cancelBtn = document.createElement('button');
      cancelBtn.type = 'button';
      cancelBtn.className = 'dl-action-btn';
      cancelBtn.textContent = t('cancel');
      cancelBtn.addEventListener('click', () => {
        if (item.isCompanion && chrome.runtime?.sendNativeMessage) {
          chrome.runtime.sendNativeMessage('com.knoux.grabflow.companion', {action: 'cancel', jobId: item.id});
          recordDownloadJob(item.id, {state: 'failed', error: 'Cancelled by user'});
        } else if (typeof item.id === 'number' && chrome.downloads?.cancel) {
          chrome.downloads.cancel(item.id);
        }
      });
      actions.append(cancelBtn);
    }

    meta.append(sizeInfo, actions);
    card.append(meta);
    frag.append(card);
  }
  ui.managerList.replaceChildren(frag);
}

async function refreshDownloadStatus(ids) {
  if (!Array.isArray(ids) || !ids.length || !chrome.downloads?.search) return;
  const items = await Promise.all(ids.map(id => chrome.downloads.search({id}).then(x => x?.[0] || null).catch(() => null)));
  for (const item of items) {
    if (item && item.id) {
      state.activeDownloads.set(item.id, {
        id: item.id,
        url: item.url,
        filename: item.filename,
        state: item.state,
        bytesReceived: item.bytesReceived,
        totalBytes: item.totalBytes,
        fileSize: item.fileSize,
        error: item.error
      });
    }
  }
  const totals = summarizeDownloads(items);
  ui.downloadStatus.hidden = false;
  ui.downloadStatus.textContent = t('downloadProgress', totals.complete, totals.running, totals.interrupted + totals.missing);
  renderDownloads();
}

async function restoreDownloadStatus() {
  try {
    const data = await chrome.storage.local.get(['downloadRuns']);
    if (Array.isArray(data.downloadRuns)) {
      await refreshDownloadStatus(data.downloadRuns);
    }
  } catch (_) { /* download history optional */ }
}

async function checkNativeCompanion() {
  if (!chrome.runtime?.sendNativeMessage) {
    state.companion.connected = false;
    if (ui.companionStatus) ui.companionStatus.textContent = t('companionMissing');
    return;
  }
  try {
    chrome.runtime.sendNativeMessage('com.knoux.grabflow.companion', {action: 'ping'}, resp => {
      if (chrome.runtime.lastError || !resp || resp.action !== 'pong') {
        state.companion.connected = false;
        if (ui.companionStatus) {
          ui.companionStatus.classList.remove('connected');
          ui.companionStatus.textContent = t('companionMissing');
        }
      } else {
        state.companion.connected = true;
        state.companion.version = resp.version;
        if (ui.companionStatus) {
          ui.companionStatus.classList.add('connected');
          ui.companionStatus.textContent = t('companionConnected');
        }
      }
      render();
    });
  } catch (_) {
    state.companion.connected = false;
    if (ui.companionStatus) ui.companionStatus.textContent = t('companionMissing');
  }
}

/* Media Preview Drawer/Modal */
function openMediaPreview(asset) {
  if (!ui.previewModal || !asset) return;
  state.previewingAsset = asset;
  ui.previewContent.replaceChildren();
  ui.previewTitle.textContent = `${t('mediaPreview')} — ${asset.type.toUpperCase()}`;
  ui.previewMeta.textContent = `${asset.name} (${asset.resolution || asset.format || asset.type})`;

  if (asset.type === 'video') {
    const video = document.createElement('video');
    video.controls = true;
    video.autoplay = true;
    video.playsInline = true;
    video.src = asset.url;
    if (asset.poster) video.poster = asset.poster;
    video.onerror = () => {
      ui.previewContent.innerHTML = `<div class="empty"><div style="font-size:20px;">⚠️</div><div>${t('corsNotice')}</div></div>`;
    };
    ui.previewContent.append(video);
  } else if (asset.type === 'audio') {
    const audio = document.createElement('audio');
    audio.controls = true;
    audio.autoplay = true;
    audio.src = asset.url;
    audio.onerror = () => {
      ui.previewContent.innerHTML = `<div class="empty"><div style="font-size:20px;">⚠️</div><div>${t('corsNotice')}</div></div>`;
    };
    ui.previewContent.append(audio);
  } else if (asset.type === 'image') {
    const img = document.createElement('img');
    img.src = asset.url;
    img.alt = asset.name;
    img.onerror = () => {
      ui.previewContent.innerHTML = `<div class="empty"><div style="font-size:20px;">⚠️</div><div>${t('corsNotice')}</div></div>`;
    };
    ui.previewContent.append(img);
  }

  ui.previewActionBtn.disabled = !isDownloadableAsset(asset);
  ui.previewModal.hidden = false;
}

function closeMediaPreview() {
  if (!ui.previewModal) return;
  ui.previewModal.hidden = true;
  ui.previewContent.replaceChildren();
  state.previewingAsset = null;
}

if (chrome.downloads?.onChanged?.addListener) {
  chrome.downloads.onChanged.addListener(delta => {
    if (state.activeDownloads.has(delta.id)) {
      const cur = state.activeDownloads.get(delta.id);
      if (delta.state) cur.state = delta.state.current;
      if (delta.error) cur.error = delta.error.current;
      renderDownloads();
    }
    chrome.storage.local.get(['downloadRuns']).then(data => refreshDownloadStatus(data.downloadRuns)).catch(() => {});
  });
}

// Event Listeners
ui.managerToggleBtn?.addEventListener('click', () => {
  state.view = state.view === 'scanner' ? 'manager' : 'scanner';
  ui.scannerView.hidden = state.view === 'manager';
  ui.managerView.hidden = state.view !== 'manager';
  ui.managerToggleBtn.classList.toggle('active', state.view === 'manager');
  if (state.view === 'manager') renderDownloads();
});

ui.clearHistoryBtn?.addEventListener('click', async () => {
  state.activeDownloads.clear();
  try { await chrome.storage.local.set({downloadRuns: []}); } catch (_) {}
  ui.downloadStatus.hidden = true;
  renderDownloads();
});

ui.langBtn.addEventListener('click', async () => {
  state.lang = state.lang === 'en' ? 'ar' : 'en';
  translate();
  try { await chrome.storage.local.set({language: state.lang}); } catch (_) { /* optional */ }
});

ui.refreshBtn.addEventListener('click', scan);
ui.search.addEventListener('input', render);
ui.sortMode.addEventListener('change', render);
ui.largeImages.addEventListener('change', render);

ui.csvBtn?.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(exportAssetsCsv(visibleAssets()));
    notice(t('csvCopied'));
  } catch (_) { notice(t('copyFail'), true); }
});

ui.exportJsonBtn?.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(exportAssetsJson(visibleAssets()));
    notice(t('jsonCopied'));
  } catch (_) { notice(t('copyFail'), true); }
});

ui.previewCloseBtn?.addEventListener('click', closeMediaPreview);
ui.previewBackdrop?.addEventListener('click', closeMediaPreview);

ui.previewCopyBtn?.addEventListener('click', async () => {
  if (state.previewingAsset?.url) {
    try {
      await navigator.clipboard.writeText(state.previewingAsset.url);
      notice(t('copied'));
    } catch (_) { notice(t('copyFail'), true); }
  }
});

ui.previewActionBtn?.addEventListener('click', () => {
  if (state.previewingAsset && isDownloadableAsset(state.previewingAsset)) {
    const asset = state.previewingAsset;
    closeMediaPreview();
    state.selected.clear();
    state.selected.add(asset.url);
    render();
    downloadSelected();
  }
});

document.querySelectorAll('[data-filter]').forEach(tab => tab.addEventListener('click', () => {
  state.filter = tab.dataset.filter;
  document.querySelectorAll('[data-filter]').forEach(t => {
    const isAct = t.dataset.filter === state.filter;
    t.classList.toggle('active', isAct);
    t.setAttribute('aria-pressed', String(isAct));
    t.setAttribute('aria-selected', String(isAct));
  });
  render();
}));

ui.selectVisible.addEventListener('click', () => {
  for (const asset of visibleAssets()) state.selected.add(asset.url);
  render();
});

ui.clearSelection.addEventListener('click', () => {
  state.selected.clear();
  render();
});

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
  await Promise.all([scan(), restoreDownloadStatus(), checkNativeCompanion()]);
})();

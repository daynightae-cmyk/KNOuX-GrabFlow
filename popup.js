'use strict';

const ui = Object.fromEntries([
  'langBtn', 'refreshBtn', 'totalCount', 'pageHost', 'search', 'results', 'selectedLabel',
  'selectVisible', 'clearSelection', 'copyBtn', 'downloadBtn', 'notice', 'countAll',
  'countImage', 'countVideo', 'countStream', 'countAudio', 'countDocument', 'sortMode', 'largeImages',
  'csvBtn', 'exportJsonBtn', 'downloadStatus', 'managerToggleBtn', 'scannerView', 'managerView',
  'managerList', 'managerCount', 'clearHistoryBtn', 'companionStatus', 'watchToggleBtn', 'buildTag',
  'previewModal', 'previewBackdrop', 'previewTitle', 'previewCloseBtn', 'previewContent',
  'previewMeta', 'previewCopyBtn', 'previewActionBtn', 'previewInspectBtn', 'previewDetails'
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
    streamHint: 'Stream playlist — needs the companion to produce one playable video.',
    streamNotDirect: 'HLS/DASH playlists cannot be saved as complete videos by the browser alone. Use Assemble, or copy links.',
    streamSkipped: n => `${n} streaming playlists skipped (use Assemble, or copy links).`,
    downloadProgress: (c, r, f) => `Downloads: ${c} complete · ${r} running · ${f} failed`,
    downloadManagerTitle: 'Download Manager', clearHistory: 'Clear History',
    noDownloads: 'No active or recent downloads.', openFile: 'Open', showFolder: 'Folder',
    retry: 'Retry', cancel: 'Cancel', stateComplete: 'Complete', stateInProgress: 'Downloading',
    stateInterrupted: 'Interrupted', stateFailed: 'Failed', stateCancelled: 'Cancelled',
    statePending: 'Queued',
    companionConnected: 'COMPANION: CONNECTED', companionChecking: 'COMPANION: CHECKING',
    companionMissing: 'COMPANION: NOT INSTALLED',
    companionToolsMissing: 'COMPANION: FFMPEG/FFPROBE MISSING', cancelUnavailable: 'Cancel unavailable',
    subtitlesLabel: n => `${n} SUBTITLES`,
    mediaPreview: 'Media Preview', previewBtn: 'Preview',
    assembleWithCompanion: '⚡ Assemble', copyFfmpeg: '📋 FFmpeg',
    ffmpegCopied: 'FFmpeg assembly command copied! Run it in a terminal or install the companion.',
    assemblyStarted: 'Companion assembly started — tracking in the Download Manager.',
    assemblySuccess: 'Stream assembled into a single playable video file.',
    assemblyFailed: 'Stream assembly failed.',
    corsNotice: 'Direct preview blocked by website CORS. Direct download remains intact.',
    inspectBtn: 'Inspect', inspecting: 'Reading stream with ffprobe…',
    inspectUnavailable: 'Inspection needs the native companion with FFmpeg installed.',
    inspectFailed: 'The companion could not read this stream.',
    inspectDuration: 'Duration', inspectBitrate: 'Bitrate', inspectTracks: 'Tracks',
    inspectContainer: 'Container', inspectSize: 'Reported size', inspectHosts: 'Source hosts',
    inspectDrm: 'Encryption/DRM suspected — assembly will be refused.',
    auditPassed: n => `Nested audit: ${n} references verified public`,
    auditUnavailable: 'Nested audit unavailable — FFmpeg transport whitelist still enforced.',
    cancelledJob: 'Assembly cancelled.',
    watchOn: 'Live watch: ON', watchOff: 'Live watch: OFF',
    watchHint: 'Watch this tab for media added after the scan',
    watchChanged: n => `Live watch found ${n} new asset(s) — press Refresh to include them.`,
    workerLost: 'Background service unavailable; downloads still start, but progress needs the popup open.',
    percentOf: (done, total) => `${formatBytesStatic(done)} / ${formatBytesStatic(total)}`
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
    streamHint: 'قائمة بث تحتاج المساعد المحلي لإنتاج فيديو كامل واحد.',
    streamNotDirect: 'قوائم HLS/DASH لا تُحفظ كفيديو كامل بالمساعد المتصفح وحده. استخدم تجميع أو انسخ الروابط.',
    streamSkipped: n => `تم تجاوز ${n} قائمة بث؛ استخدم تجميع أو انسخ الروابط.`,
    downloadProgress: (c, r, f) => `التنزيل: ${c} مكتمل · ${r} جارٍ · ${f} فشل`,
    downloadManagerTitle: 'إدارة التحميلات', clearHistory: 'مسح السجل',
    noDownloads: 'لا توجد تنزيلات نشطة أو سابقة.', openFile: 'فتح', showFolder: 'المجلد',
    retry: 'إعادة', cancel: 'إلغاء', stateComplete: 'مكتمل', stateInProgress: 'جارٍ التحميل',
    stateInterrupted: 'متوقف', stateFailed: 'فشل', stateCancelled: 'ملغى', statePending: 'في الانتظار',
    companionConnected: 'المساعد: متصل', companionChecking: 'المساعد: جارٍ التحقق',
    companionMissing: 'المساعد: غير مثبت',
    companionToolsMissing: 'المساعد: FFmpeg/FFprobe غير متاحين', cancelUnavailable: 'الإلغاء غير متاح',
    subtitlesLabel: n => `${n} ترجمة`,
    mediaPreview: 'معاينة الوسائط', previewBtn: 'معاينة',
    assembleWithCompanion: '⚡ تجميع', copyFfmpeg: '📋 أمر FFmpeg',
    ffmpegCopied: 'تم نسخ أمر FFmpeg! شغّله في الطرفية أو ثبّت المساعد المحلي.',
    assemblyStarted: 'بدأ تجميع البث — تابعه في إدارة التحميلات.',
    assemblySuccess: 'تم تجميع قائمة البث في ملف فيديو واحد قابل للتشغيل.',
    assemblyFailed: 'تعذر تجميع قائمة البث.',
    corsNotice: 'المعاينة المباشرة محجوبة بسياسة CORS من الموقع. التنزيل يعمل بشكل طبيعي.',
    inspectBtn: 'فحص', inspecting: 'جارٍ قراءة البث بـ ffprobe…',
    inspectUnavailable: 'الفحص يحتاج المساعد المحلي مع FFmpeg.',
    inspectFailed: 'لم يستطع المساعد قراءة هذا البث.',
    inspectDuration: 'المدة', inspectBitrate: 'معدل البيانات', inspectTracks: 'المسارات',
    inspectContainer: 'الحاوية', inspectSize: 'الحجم المُبلغ', inspectHosts: 'مصادر الاستضافة',
    inspectDrm: 'يُشتبه بتشفير/DRM — سيرفض التجميع.',
    auditPassed: n => `تدقيق داخلي: ${n} مرجعًا تحققت أنها عامة`,
    auditUnavailable: 'التدقيق الداخلي غير متاح — قائمة بروتوكولات FFmpeg ما زالت مطبقة.',
    cancelledJob: 'أُلغي التجميع.',
    watchOn: 'المراقبة الحية: مفعّلة', watchOff: 'المراقبة الحية: متوقفة',
    watchHint: 'راقب هذا التبويب لاكتشاف وسائط أُضيفت بعد الفحص',
    watchChanged: n => `المراقبة الحية وجدت ${n} عنصرًا جديدًا — اضغط تحديث لإدراجه.`,
    workerLost: 'خدمة الخلفية غير متاحة؛ يبدأ التنزيل لكن التقدّم يتطلب إبقاء النافذة مفتوحة.',
    percentOf: (done, total) => `${formatBytesStatic(done)} / ${formatBytesStatic(total)}`
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
  view: 'scanner',
  companion: {connected: false, missingTools: false, version: null, capabilities: []},
  jobs: new Map(),
  previewingAsset: null,
  workerReady: false,
  liveWatch: false,
  liveBaselineCount: 0
};

const t = (key, ...args) => {
  const value = dictionary[state.lang][key] || key;
  return typeof value === 'function' ? value(...args) : value;
};

function formatBytesStatic(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}
const formatBytes = formatBytesStatic;

/* ----------------------------------------------------------- worker bridge --
 * The popup is a view. The service worker owns download and companion state so
 * that tracking survives the popup closing; this bridge mirrors that state in.
 * -------------------------------------------------------------------------- */

function sendToWorker(type, payload) {
  return new Promise(resolve => {
    if (!chrome.runtime?.sendMessage) { resolve(null); return; }
    try {
      chrome.runtime.sendMessage({type, ...(payload || {})}, response => {
        if (chrome.runtime.lastError) { resolve(null); return; }
        resolve(response ?? null);
      });
    } catch (_) { resolve(null); }
  });
}

let uiPort = null;

function connectWorker() {
  if (!chrome.runtime?.connect) { onWorkerLost(); return; }
  try {
    uiPort = chrome.runtime.connect({name: 'grabflow-ui'});
  } catch (_) { onWorkerLost(); return; }
  state.workerReady = true;
  uiPort.onMessage.addListener(handleWorkerEvent);
  uiPort.onDisconnect.addListener(() => {
    uiPort = null;
    state.workerReady = false;
    setTimeout(connectWorker, 1200);   // the worker is restarted on demand
  });
}

function handleWorkerEvent(event) {
  if (!event || typeof event !== 'object') return;
  if (event.type === 'hydrate') {
    state.workerReady = true;
    for (const job of (event.jobs || [])) state.jobs.set(job.key, job);
    if (event.companion) state.companion = event.companion;
    renderDownloads();
    renderCompanion();
  } else if (event.type === 'job') {
    state.jobs.set(event.job.key, event.job);
    renderDownloads();
    renderDownloadStatus();
  } else if (event.type === 'companion') {
    state.companion = event.state;
    state.workerReady = true;
    renderCompanion();
    if (state.page) render();
  } else if (event.type === 'cleared') {
    state.jobs.clear();
    for (const job of (event.jobs || [])) state.jobs.set(job.key, job);
    renderDownloads();
    renderDownloadStatus();
  }
}

function onWorkerLost() {
  state.workerReady = false;
  notice(t('workerLost'), true);
  armPopupDownloadFallback();
}

/**
 * Graceful degradation. When the service worker is unreachable — a crash, a
 * restart race, or a host that exposes no runtime messaging — downloads must
 * still start and still be tracked in this window. Progress simply stops
 * being reported once the popup closes, and the notice above says so.
 */
let popupFallbackArmed = false;
function armPopupDownloadFallback() {
  if (popupFallbackArmed || !chrome.downloads?.onChanged?.addListener) return;
  popupFallbackArmed = true;
  chrome.downloads.onChanged.addListener(delta => {
    const key = `chrome-${delta.id}`;
    const job = state.jobs.get(key);
    if (!job) return;
    if (delta.state) job.state = delta.state.current;
    if (delta.error) job.error = delta.error.current;
    if (delta.bytesReceived !== undefined) job.bytesReceived = delta.bytesReceived.current;
    if (delta.totalBytes !== undefined) job.totalBytes = delta.totalBytes.current;
    job.updatedAt = Date.now();
    renderDownloads();
    renderDownloadStatus();
  });
}

async function startDownloadLocal(asset, index, domain) {
  const filename = safeDownloadName(asset, index, domain);
  try {
    const id = await chrome.downloads.download({
      url: asset.url, filename, conflictAction: 'uniquify', saveAs: false
    });
    if (typeof id !== 'number') throw new Error('no download id');
    const key = `chrome-${id}`;
    state.jobs.set(key, {
      key, kind: 'chrome', id, url: asset.url, filename, domain,
      format: asset.format || asset.type, state: 'in_progress',
      bytesReceived: 0, totalBytes: 0, updatedAt: Date.now()
    });
    // Reconcile immediately: a small local file can finish before we get here.
    try {
      const found = await chrome.downloads.search({id});
      const record = found && found[0];
      const tracked = state.jobs.get(key);
      if (record && tracked) Object.assign(tracked, {
        state: record.state, bytesReceived: record.bytesReceived,
        totalBytes: record.totalBytes, fileSize: record.fileSize,
        filename: record.filename || filename, error: record.error, updatedAt: Date.now()
      });
    } catch (_) { /* status is optional */ }
    return {ok: true, id, filename};
  } catch (_) {
    return {ok: false, error: 'download-failed', filename};
  }
}

/* --------------------------------------------------------------- i18n / chrome */

function translate() {
  document.documentElement.lang = state.lang;
  document.documentElement.dir = state.lang === 'ar' ? 'rtl' : 'ltr';
  ui.langBtn.textContent = state.lang === 'ar' ? 'English' : 'عربي';
  document.querySelectorAll('[data-i18n]').forEach(node => {
    node.textContent = t(node.dataset.i18n);
  });
  ui.search.placeholder = t('search');
  ui.selectedLabel.textContent = t('selected', state.selected.size);
  if (ui.watchToggleBtn) {
    ui.watchToggleBtn.textContent = state.liveWatch ? t('watchOn') : t('watchOff');
    ui.watchToggleBtn.title = t('watchHint');
    ui.watchToggleBtn.classList.toggle('active', state.liveWatch);
    ui.watchToggleBtn.setAttribute('aria-pressed', String(state.liveWatch));
  }
  renderCompanion();
  if (state.page) render();
  renderDownloads();
  renderDownloadStatus();
}

function renderCompanion() {
  if (!ui.companionStatus) return;
  const label = state.companion.connected
    ? t('companionConnected')
    : state.companion.missingTools ? t('companionToolsMissing') : t('companionMissing');
  ui.companionStatus.textContent = label;
  ui.companionStatus.classList.toggle('connected', !!state.companion.connected);
  ui.companionStatus.title = state.companion.version
    ? `v${state.companion.version} · ${(state.companion.capabilities || []).join(', ')}`
    : (state.companion.error || label);
}

function notice(message, error = false) {
  ui.notice.hidden = !message;
  ui.notice.classList.toggle('error', error);
  ui.notice.textContent = message || '';
}

function visibleAssets() {
  const query = ui.search.value.toLocaleLowerCase().trim();
  return filterSortAssets(state.assets, {
    type: state.filter, query, sort: ui.sortMode.value, largeImages: ui.largeImages.checked
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
  const hasDownloadable = selectedAssets().some(asset => isDownloadableAsset(asset));
  ui.copyBtn.disabled = state.busy || !hasSelection;
  ui.downloadBtn.disabled = state.busy || !hasDownloadable;
  ui.selectedLabel.textContent = t('selected', state.selected.size);
}

function streamFormatLabel(format) {
  if (format === 'hls') return 'HLS · M3U8';
  if (format === 'dash') return 'DASH · MPD';
  return format ? format.toUpperCase() : 'VIDEO FILE';
}

/**
 * Run an asynchronous UI action without leaving its promise floating.
 * A rejection here would otherwise be an unhandled rejection: invisible in the
 * popup's own error surface and, in a service worker, enough to kill it.
 */
function runAction(action, failureMessage) {
  Promise.resolve()
    .then(action)
    .catch(() => {
      if (failureMessage) notice(failureMessage, true);
    });
}

function makeBadge(className, text, title) {
  const node = document.createElement('span');
  node.className = className;
  node.textContent = text;
  if (title) node.title = title;
  return node;
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
    if (asset.type === 'video' && ['hls', 'dash'].includes(asset.format)) counts.stream++;
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
      format.textContent = streamFormatLabel(asset.format);
      if (isStream) format.title = t('streamHint');
      badges.append(format);

      if (asset.resolution) badges.append(makeBadge('asset-format', asset.resolution));
      if (asset.codec) badges.append(makeBadge('asset-format', String(asset.codec).slice(0, 16)));
      if (asset.duration) badges.append(makeBadge('asset-meta', formatDuration(asset.duration)));
      if (asset.initiatorType) badges.append(makeBadge('asset-format',
        asset.initiatorType.toUpperCase(), 'Browser resource type'));
      if (asset.hasSubtitles && asset.subtitles?.length) badges.append(
        makeBadge('asset-subtag', t('subtitlesLabel', asset.subtitles.length)));
    } else if (asset.type === 'image' && asset.width && asset.height) {
      badges.append(makeBadge('asset-meta', `${asset.width} × ${asset.height} px`));
    }
    if (badges.childNodes.length > 0) info.append(badges);

    const actionsBar = document.createElement('div');
    actionsBar.className = 'asset-actions';

    if (['image', 'video', 'audio'].includes(asset.type) && !isStream) {
      const prevBtn = document.createElement('button');
      prevBtn.type = 'button';
      prevBtn.className = 'btn-card-action';
      prevBtn.textContent = t('previewBtn');
      prevBtn.addEventListener('click', e => { e.preventDefault(); e.stopPropagation(); openMediaPreview(asset); });
      actionsBar.append(prevBtn);
    }

    if (isStream) {
      const inspectBtn = document.createElement('button');
      inspectBtn.type = 'button';
      inspectBtn.className = 'btn-card-action';
      inspectBtn.textContent = t('inspectBtn');
      inspectBtn.disabled = !state.companion.connected;
      inspectBtn.addEventListener('click', e => {
        e.preventDefault();
        e.stopPropagation();
        inspectStream(asset).catch(() => notice(t('inspectFailed'), true));
      });
      actionsBar.append(inspectBtn);

      if (state.companion.connected) {
        const assembleBtn = document.createElement('button');
        assembleBtn.type = 'button';
        assembleBtn.className = 'btn-card-action btn-assemble';
        assembleBtn.textContent = t('assembleWithCompanion');
        assembleBtn.addEventListener('click', e => {
          e.preventDefault();
          e.stopPropagation();
          assembleStreamViaCompanion(asset).catch(() => notice(t('assemblyFailed'), true));
        });
        actionsBar.append(assembleBtn);
      } else {
        const ffmpegBtn = document.createElement('button');
        ffmpegBtn.type = 'button';
        ffmpegBtn.className = 'btn-card-action';
        ffmpegBtn.textContent = t('copyFfmpeg');
        ffmpegBtn.addEventListener('click', async e => {
          e.preventDefault(); e.stopPropagation();
          const cmd = generateFfmpegCommand(asset.url, safeDownloadName(asset, 1, state.page?.domain));
          try { await navigator.clipboard.writeText(cmd); notice(t('ffmpegCopied')); }
          catch (_) { notice(t('copyFail'), true); }
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
  state.liveBaselineCount = state.assets.length;
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
    if (state.liveWatch) armLiveWatch(tab.id);
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

/* ------------------------------------------------------------ live watch ---
 * Media on modern pages often appears only after the user interacts. A bounded
 * MutationObserver inside the page counts media-bearing nodes and reports back;
 * it never auto-downloads and never leaves a timer running after the tab closes.
 * -------------------------------------------------------------------------- */

function armLiveWatch(tabId) {
  chrome.scripting.executeScript({target: {tabId}, func: installLiveMediaWatch, args: [state.lang]})
    .catch(() => { /* tab may have navigated away */ });
}

function installLiveMediaWatch(lang) {
  if (window.__knouxGrabflowWatch) return {installed: true};
  const countMedia = () => document.querySelectorAll(
    'video, audio, source, img, object[data], embed[src], a[href]').length;
  let baseline = countMedia();
  let pending = 0;
  let timer = null;
  const observer = new MutationObserver(() => {
    const now = countMedia();
    if (now !== baseline) {
      pending = Math.max(pending, Math.abs(now - baseline));
      baseline = now;
      clearTimeout(timer);
      timer = setTimeout(() => {
        try {
          chrome.runtime.sendMessage({type: 'watch:changed', count: pending});
        } catch (_) { /* popup already closed */ }
        pending = 0;
      }, 900);
    }
  });
  observer.observe(document.documentElement, {childList: true, subtree: true, attributes: true,
    attributeFilter: ['src', 'href', 'data-src', 'poster']});
  window.__knouxGrabflowWatch = {observer, disconnect: () => { observer.disconnect(); clearTimeout(timer); }};
  return {installed: true};
}

/* ---------------------------------------------------------------- downloads */

function selectedAssets() { return state.assets.filter(asset => state.selected.has(asset.url)); }

async function downloadSelected() {
  const allSelected = selectedAssets();
  const chosen = allSelected.filter(asset => isDownloadableAsset(asset));
  const skipped = allSelected.length - chosen.length;
  if (!chosen.length && skipped) { notice(t('streamNotDirect'), true); return; }
  if (!chosen.length) { notice(t('selectFirst'), true); return; }
  if (chosen.length > 30) { notice(t('max'), true); return; }
  setBusy(true);
  let success = 0, failures = 0;
  try {
    for (let index = 0; index < chosen.length; index++) {
      const asset = chosen[index];
      notice(t('downloading', index + 1, chosen.length));
      let result = state.workerReady
        ? await sendToWorker('download:start', {asset, index: index + 1, domain: state.page?.domain})
        : null;
      if (!result) {
        armPopupDownloadFallback();
        result = await startDownloadLocal(asset, index + 1, state.page?.domain);
      }
      if (result && result.ok) success++;
      else failures++;
    }
    const suffix = skipped ? ` · ${t('streamSkipped', skipped)}` : '';
    notice(t('done', success, failures) + suffix, failures > 0 || skipped > 0);
    renderDownloads();
    renderDownloadStatus();
  } finally { setBusy(false); }
}

async function assembleStreamViaCompanion(asset) {
  if (!state.companion.connected) { notice(t('inspectUnavailable'), true); return; }
  const result = await sendToWorker('companion:assemble',
    {asset, index: state.jobs.size + 1, domain: state.page?.domain});
  if (result && result.ok) {
    notice(t('assemblyStarted'));
    renderDownloads();
  } else {
    notice((result && result.error) || t('assemblyFailed'), true);
  }
}

async function inspectStream(asset) {
  if (!state.companion.connected) { notice(t('inspectUnavailable'), true); return; }
  notice(t('inspecting'));
  const result = await sendToWorker('companion:probe', {url: asset.url});
  if (!result || result.status !== 'ok') {
    notice((result && result.error) || t('inspectFailed'), true);
    return;
  }
  openMediaPreview({
    ...asset, probed: true, durationSeconds: result.durationSeconds, bitRate: result.bitRate,
    sizeBytes: result.sizeBytes, videoTracks: result.videoTracks,
    audioTracks: result.audioTracks, drmSuspected: result.drmSuspected
  });
}

/* ------------------------------------------------------- manager rendering --
 * One card per tracked job: browser downloads and companion assemblies share
 * the same list, so the user sees one truth about what is happening.
 * -------------------------------------------------------------------------- */

function jobPercent(job) {
  if (job.state === 'complete') return 100;
  if (Number.isFinite(job.percent)) return Math.max(0, Math.min(100, job.percent));
  if (job.totalBytes > 0) return Math.min(100, Math.round((job.bytesReceived / job.totalBytes) * 100));
  return job.state === 'in_progress' ? 12 : 0;
}

function stateLabel(job) {
  switch (job.state) {
    case 'complete': return t('stateComplete');
    case 'interrupted': return t('stateInterrupted');
    case 'failed': return t('stateFailed');
    case 'cancelled': return t('stateCancelled');
    case 'pending': return t('statePending');
    default: return t('stateInProgress');
  }
}

function renderDownloads() {
  if (!ui.managerList) return;
  const items = [...state.jobs.values()].sort((a, b) => (a.updatedAt || 0) - (b.updatedAt || 0));
  ui.managerCount.textContent = items.length;
  if (!items.length) {
    ui.managerList.replaceChildren();
    const emptyBlock = document.createElement('div');
    emptyBlock.className = 'empty-downloads';
    const emptyGlyph = document.createElement('div');
    emptyGlyph.className = 'empty-orbit';
    emptyGlyph.textContent = '▽';
    emptyBlock.append(emptyGlyph);
    const label = document.createElement('div');
    label.textContent = t('noDownloads');
    emptyBlock.append(label);
    ui.managerList.append(emptyBlock);
    return;
  }
  const frag = document.createDocumentFragment();
  for (const item of items.slice().reverse()) {
    const card = document.createElement('div');
    card.className = `dl-card ${item.kind || 'chrome'}`;

    const top = document.createElement('div');
    top.className = 'dl-card-top';
    const name = document.createElement('div');
    name.className = 'dl-card-name';
    name.textContent = (item.filename || item.url || 'Download').split(/[\\/]/).pop();
    name.title = item.url || '';
    const badge = document.createElement('span');
    badge.className = `dl-state-badge ${item.state || 'in_progress'}`;
    badge.textContent = stateLabel(item);
    const kind = document.createElement('span');
    kind.className = 'dl-kind';
    kind.textContent = item.kind === 'companion' ? 'FFMPEG' : 'BROWSER';
    top.append(name, kind, badge);
    card.append(top);

    const progress = document.createElement('div');
    progress.className = 'dl-card-progress';
    const bar = document.createElement('div');
    bar.className = 'dl-card-progress-bar';
    bar.style.width = `${jobPercent(item)}%`;
    progress.append(bar);
    card.append(progress);

    const meta = document.createElement('div');
    meta.className = 'dl-card-meta';
    const sizeInfo = document.createElement('span');
    sizeInfo.className = 'dl-size';
    if (item.state === 'complete') {
      sizeInfo.textContent = `${formatBytes(item.fileSize || item.bytesReceived)} · ${jobPercent(item)}%`;
    } else if (item.totalBytes > 0) {
      sizeInfo.textContent = `${t('percentOf', item.bytesReceived, item.totalBytes)} (${jobPercent(item)}%)`;
    } else if (item.kind === 'companion' && item.bytesReceived > 0) {
      sizeInfo.textContent = `${formatBytes(item.bytesReceived)} · ${jobPercent(item)}%`;
    } else {
      sizeInfo.textContent = item.domain || '';
    }

    const actions = document.createElement('div');
    actions.className = 'dl-actions';
    const button = (label, handler, disabled) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'dl-action-btn';
      b.textContent = label;
      if (disabled) b.disabled = true; else b.addEventListener('click', handler);
      return b;
    };

    if (item.state === 'complete') {
      if (typeof item.id === 'number') {
        actions.append(
          button(t('openFile'), () => runAction(
            () => sendToWorker('download:open', {id: item.id}))),
          button(t('showFolder'), () => runAction(
            () => sendToWorker('download:show', {id: item.id}))));
      }
    } else if (['interrupted', 'failed', 'cancelled'].includes(item.state)) {
      actions.append(button(t('retry'), () => runAction(() => retryJob(item), t('blocked'))));
    } else if (['in_progress', 'pending'].includes(item.state)) {
      if (item.kind === 'companion') {
        actions.append(button(t('cancel'), () => runAction(
          () => sendToWorker('companion:cancel', {jobId: item.jobId}))));
      } else if (typeof item.id === 'number') {
        actions.append(button(t('cancel'), () => runAction(
          () => sendToWorker('download:cancel', {id: item.id}))));
      }
    }

    meta.append(sizeInfo, actions);
    card.append(meta);

    if (item.error || item.nestedAudit) {
      const detail = document.createElement('div');
      detail.className = 'dl-detail';
      const parts = [];
      if (item.error) parts.push(String(item.error).slice(0, 180));
      if (item.nestedAudit) {
        parts.push(item.nestedAudit.status === 'passed'
          ? t('auditPassed', item.nestedAudit.checked) : t('auditUnavailable'));
      }
      detail.textContent = parts.join(' · ');
      card.append(detail);
    }
    frag.append(card);
  }
  ui.managerList.replaceChildren(frag);
}

async function retryJob(item) {
  if (item.kind === 'companion') {
    // type must be carried through: safeDownloadName derives the extension from
    // it, and omitting it would retry an assembly into a .bin file.
    await assembleStreamViaCompanion({
      url: item.url, format: item.format, name: item.filename, type: 'video'
    });
    return;
  }
  let result = state.workerReady
    ? await sendToWorker('download:start', {
        asset: {url: item.url, type: item.format === 'image' ? 'image' : 'video',
                format: item.format, name: item.filename}, index: 1, domain: item.domain})
    : null;
  if (!result) {
    armPopupDownloadFallback();
    result = await startDownloadLocal(
      {url: item.url, type: item.format === 'image' ? 'image' : 'video',
       format: item.format, name: item.filename}, 1, item.domain);
  }
  if (!result || !result.ok) notice((result && result.error) || t('blocked'), true);
  renderDownloads();
}

function renderDownloadStatus() {
  if (!ui.downloadStatus) return;
  const items = [...state.jobs.values()];
  if (!items.length) { ui.downloadStatus.hidden = true; return; }
  const counts = {complete: 0, running: 0, failed: 0};
  for (const job of items) {
    if (job.state === 'complete') counts.complete++;
    else if (['failed', 'interrupted', 'cancelled'].includes(job.state)) counts.failed++;
    else counts.running++;
  }
  ui.downloadStatus.hidden = false;
  ui.downloadStatus.textContent = t('downloadProgress', counts.complete, counts.running, counts.failed);
}

/* -------------------------------------------------------------- preview UI */

function openMediaPreview(asset) {
  if (!ui.previewModal || !asset) return;
  state.previewingAsset = asset;
  ui.previewContent.replaceChildren();
  if (ui.previewDetails) ui.previewDetails.replaceChildren();
  ui.previewTitle.textContent = `${t('mediaPreview')} — ${asset.type.toUpperCase()}`;
  ui.previewMeta.textContent = `${asset.name} (${asset.resolution || asset.format || asset.type})`;

  const showFailure = () => {
    ui.previewContent.replaceChildren();
    const block = document.createElement('div');
    block.className = 'empty';
    const glyph = document.createElement('div');
    glyph.className = 'empty-orbit';
    glyph.textContent = '⚠';
    const label = document.createElement('div');
    label.textContent = t('corsNotice');
    block.append(glyph, label);
    ui.previewContent.append(block);
  };

  if (asset.type === 'video') {
    const video = document.createElement('video');
    video.controls = true;
    video.playsInline = true;
    video.preload = 'metadata';   // never stream a whole file into popup memory
    video.src = asset.url;
    if (asset.poster) video.poster = asset.poster;
    video.onerror = showFailure;
    ui.previewContent.append(video);
  } else if (asset.type === 'audio') {
    const audio = document.createElement('audio');
    audio.controls = true;
    audio.preload = 'metadata';
    audio.src = asset.url;
    audio.onerror = showFailure;
    ui.previewContent.append(audio);
  } else if (asset.type === 'image') {
    const img = document.createElement('img');
    img.src = asset.url;
    img.alt = asset.name;
    img.loading = 'lazy';
    img.onerror = showFailure;
    ui.previewContent.append(img);
  }

  if (ui.previewDetails) renderPreviewDetails(asset);
  if (ui.previewInspectBtn) {
    ui.previewInspectBtn.hidden = !(asset.type === 'video' && ['hls', 'dash'].includes(asset.format));
  }
  ui.previewActionBtn.disabled = !isDownloadableAsset(asset);
  ui.previewModal.hidden = false;
}

function renderPreviewDetails(asset) {
  const rows = [];
  const add = (label, value) => { if (value !== null && value !== undefined && value !== '') rows.push([label, String(value)]); };
  add(t('inspectDuration'), asset.duration ? `${asset.duration}s`
    : (asset.durationSeconds ? `${asset.durationSeconds.toFixed(1)}s` : null));
  add(t('inspectBitrate'), asset.bitRate ? `${Math.round(asset.bitRate / 1000)} kbps` : asset.bitrate);
  add('Resolution', asset.resolution);
  add('Codec', asset.codec);
  add(t('inspectSize'), asset.sizeBytes ? formatBytes(asset.sizeBytes) : null);
  if (asset.videoTracks?.length) {
    add(t('inspectTracks'), asset.videoTracks.map(v => `${v.width}×${v.height} ${v.codec}`).join(', ')
      + (asset.audioTracks?.length ? ` · ${asset.audioTracks.map(a => a.codec).join(', ')}` : ''));
  }
  if (asset.drmSuspected) add('DRM', t('inspectDrm'));
  ui.previewDetails.replaceChildren(...rows.map(([label, value]) => {
    const row = document.createElement('div');
    row.className = 'preview-detail-row';
    const k = document.createElement('span'); k.className = 'k'; k.textContent = label;
    const v = document.createElement('span'); v.className = 'v'; v.textContent = value;
    row.append(k, v);
    return row;
  }));
}

function closeMediaPreview() {
  if (!ui.previewModal) return;
  ui.previewModal.hidden = true;
  ui.previewContent.replaceChildren();
  if (ui.previewDetails) ui.previewDetails.replaceChildren();
  state.previewingAsset = null;
}

/* ---------------------------------------------------------------- wiring -- */

ui.managerToggleBtn?.addEventListener('click', () => {
  state.view = state.view === 'scanner' ? 'manager' : 'scanner';
  ui.scannerView.hidden = state.view === 'manager';
  ui.managerView.hidden = state.view !== 'manager';
  ui.managerToggleBtn.classList.toggle('active', state.view === 'manager');
  ui.managerToggleBtn.setAttribute('aria-pressed', String(state.view === 'manager'));
  if (state.view === 'manager') {
    renderDownloads();
    // Pull the authoritative list in case events fired while the view was closed.
    sendToWorker('jobs:list').then(reply => {
      if (!reply || !Array.isArray(reply.jobs)) return;
      state.jobs.clear();
      for (const job of reply.jobs) state.jobs.set(job.key, job);
      if (reply.companion) state.companion = reply.companion;
      renderDownloads();
      renderDownloadStatus();
      renderCompanion();
    }).catch(() => { /* the mirrored list is still usable as-is */ });
  }
});

ui.clearHistoryBtn?.addEventListener('click', async () => {
  await sendToWorker('jobs:clear');
  state.jobs.clear();
  ui.downloadStatus.hidden = true;
  renderDownloads();
});

ui.watchToggleBtn?.addEventListener('click', () => {
  state.liveWatch = !state.liveWatch;
  translate();
  if (state.liveWatch && state.tab?.id) armLiveWatch(state.tab.id);
  else chrome.scripting.executeScript({target: {tabId: state.tab?.id}, func: () => {
    if (window.__knouxGrabflowWatch) window.__knouxGrabflowWatch.disconnect();
  }}).catch(() => {});
});

ui.langBtn.addEventListener('click', async () => {
  state.lang = state.lang === 'en' ? 'ar' : 'en';
  translate();
  try { await chrome.storage.local.set({language: state.lang}); } catch (_) { /* optional */ }
});

ui.refreshBtn.addEventListener('click', () => runAction(scan, t('scanFail')));
ui.search.addEventListener('input', render);
ui.sortMode.addEventListener('change', render);
ui.largeImages.addEventListener('change', render);

ui.csvBtn?.addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(exportAssetsCsv(visibleAssets())); notice(t('csvCopied')); }
  catch (_) { notice(t('copyFail'), true); }
});

ui.exportJsonBtn?.addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(exportAssetsJson(visibleAssets())); notice(t('jsonCopied')); }
  catch (_) { notice(t('copyFail'), true); }
});

ui.previewCloseBtn?.addEventListener('click', closeMediaPreview);
ui.previewBackdrop?.addEventListener('click', closeMediaPreview);
ui.previewCopyBtn?.addEventListener('click', async () => {
  if (!state.previewingAsset?.url) return;
  try { await navigator.clipboard.writeText(state.previewingAsset.url); notice(t('copied')); }
  catch (_) { notice(t('copyFail'), true); }
});
ui.previewInspectBtn?.addEventListener('click', () => {
  if (state.previewingAsset) inspectStream(state.previewingAsset).catch(() => notice(t('inspectFailed'), true));
});
ui.previewActionBtn?.addEventListener('click', () => {
  if (state.previewingAsset && isDownloadableAsset(state.previewingAsset)) {
    const asset = state.previewingAsset;
    closeMediaPreview();
    state.selected.clear();
    state.selected.add(asset.url);
    render();
    runAction(downloadSelected, t('blocked'));
  }
});

document.querySelectorAll('[data-filter]').forEach(tab => tab.addEventListener('click', () => {
  state.filter = tab.dataset.filter;
  document.querySelectorAll('[data-filter]').forEach(node => {
    const isActive = node.dataset.filter === state.filter;
    node.classList.toggle('active', isActive);
    node.setAttribute('aria-pressed', String(isActive));
    node.setAttribute('aria-selected', String(isActive));
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

ui.downloadBtn.addEventListener('click', () => runAction(downloadSelected, t('blocked')));

document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !ui.previewModal?.hidden) closeMediaPreview();
});

// Worker events that are not job state.
chrome.runtime.onMessage?.addListener(message => {
  if (message && message.type === 'watch:changed') {
    notice(t('watchChanged', message.count || 1));
  }
});

(async () => {
  // The badge shows the version the browser actually loaded, not a literal in HTML.
  if (ui.buildTag && chrome.runtime?.getManifest) {
    ui.buildTag.textContent = `FULL ${chrome.runtime.getManifest().version}`;
  }
  try {
    const settings = await chrome.storage.local.get(['language']);
    state.lang = settings.language === 'ar' || settings.language === 'en'
      ? settings.language : (navigator.language.toLowerCase().startsWith('ar') ? 'ar' : 'en');
  } catch (_) { state.lang = 'en'; }
  connectWorker();
  translate();
  await scan();
  // Ask the worker for a truthful companion handshake rather than assuming one.
  const companionState = await sendToWorker('companion:ping');
  if (companionState && !companionState.error) {
    state.companion = companionState;
    renderCompanion();
    render();
  }
})().catch(() => {
  // Startup runs as one async unit. Without this handler a failure outside the
  // storage try-block would leave the popup half-rendered with no explanation,
  // and the rejection would be invisible to the user.
  empty(t('scanFail'));
  notice(t('scanFail'), true);
});

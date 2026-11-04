'use strict';
/**
 * KNOuX GrabFlow — MV3 service worker.
 *
 * It exists for two reasons that the popup genuinely cannot cover:
 *
 *  1. Download lifecycle ownership. `chrome.downloads.onChanged` only fires in a
 *     context that is alive. With the listener in the popup, every download
 *     silently stopped reporting the moment the popup closed. The worker keeps
 *     tracking completion, interruption and byte progress across popup sessions.
 *
 *  2. Native companion session ownership. A persistent `connectNative` port
 *     gives real assembly progress and a real cancel, both impossible with the
 *     one-shot `sendNativeMessage` call, whose host process dies with the popup.
 *
 * Privacy invariant, asserted by tests/test-utilities.cjs and documented in
 * PRIVACY.md: this worker holds no host permissions, installs no network
 * observers (no webRequest, no declarativeNetRequest), and never scans a page
 * on its own. Scanning stays on-demand, in the tab the user chose.
 */

importScripts('asset-utils.js');

const HOST_NAME = 'com.knoux.grabflow.companion';
const STORE_KEY = 'grabflowJobs';
const MAX_JOBS = 80;
const MAX_RECONCILE_PER_STARTUP = 25;
const PERSIST_THROTTLE_MS = 400;
const NATIVE_REQUEST_TIMEOUT_MS = 25000;
const NATIVE_PROBE_TIMEOUT_MS = 30000;
const NATIVE_START_TIMEOUT_MS = 15000;
const UI_PORT_NAME = 'grabflow-ui';

/** @type {Map<string, object>} */
const jobs = new Map();
/** @type {Set<chrome.runtime.Port>} */
const uiPorts = new Set();

let nativePort = null;
let nativeState = {connected: false, missingTools: false, version: null, capabilities: [],
                   localMediaPolicy: null, error: null};
/** @type {Map<string, {resolve: Function, reject: Function, timer: number}>} */
const pendingNative = new Map();
let requestCounter = 0;
let persistTimer = null;
let idleCloseTimer = null;

/* ------------------------------------------------------------------ job store */

function jobKeyForDownload(id) { return `chrome-${id}`; }

const TERMINAL_STATES = ['complete', 'failed', 'cancelled', 'interrupted', 'aborted'];

function updateJob(key, patch) {
  const merged = Object.assign({key, updatedAt: Date.now()}, jobs.get(key) || {}, patch);
  jobs.set(key, merged);
  // A terminal state is flushed immediately: throttling the last write is how a
  // finished download gets lost when the worker is suspended right after.
  if (TERMINAL_STATES.includes(merged.state)) persistNow();
  else schedulePersist();
  broadcast({type: 'job', job: merged});
  return merged;
}

function persistNow() {
  clearTimeout(persistTimer);
  persistTimer = null;
  dropFinishedOverflow();
  const records = [...jobs.values()].slice(-MAX_JOBS);
  return chrome.storage.local.set({[STORE_KEY]: records}).catch(() => { /* best effort */ });
}

function dropFinishedOverflow() {
  if (jobs.size <= MAX_JOBS) return;
  const finished = [...jobs.values()]
    .filter(job => ['complete', 'failed', 'cancelled', 'interrupted', 'aborted'].includes(job.state))
    .sort((a, b) => a.updatedAt - b.updatedAt);
  for (const job of finished) {
    if (jobs.size <= MAX_JOBS) break;
    jobs.delete(job.key);
  }
}

function schedulePersist() {
  if (persistTimer) return;
  persistTimer = setTimeout(persistNow, PERSIST_THROTTLE_MS);
}

async function loadJobs() {
  if (jobs.size) return;
  try {
    const stored = await chrome.storage.local.get([STORE_KEY]);
    for (const record of (Array.isArray(stored[STORE_KEY]) ? stored[STORE_KEY] : [])) {
      if (record && typeof record.key === 'string') jobs.set(record.key, record);
    }
  } catch (_) { /* start empty */ }
}

function broadcast(message) {
  for (const port of uiPorts) {
    try { port.postMessage(message); } catch (_) { uiPorts.delete(port); }
  }
}

/* -------------------------------------------------------------- download side */

chrome.downloads.onChanged.addListener(delta => {
  const key = jobKeyForDownload(delta.id);
  if (!jobs.has(key) && !delta.state && !delta.error) return;
  const patch = {};
  if (delta.state) patch.state = delta.state.current;
  if (delta.error) patch.error = delta.error.current;
  if (delta.bytesReceived !== undefined) patch.bytesReceived = delta.bytesReceived.current;
  if (delta.totalBytes !== undefined) patch.totalBytes = delta.totalBytes.current;
  if (delta.filename) patch.filename = delta.filename.current;
  updateJob(key, patch);
  // Deltas only carry what changed, so a finished job would otherwise never learn
  // its total byte count or final file size. One query per completion is cheap
  // and makes the Download Manager truthful.
  if (['complete', 'interrupted'].includes(delta.state && delta.state.current)) {
    enrichDownload(delta.id);
  }
});

async function enrichDownload(id) {
  try {
    const found = await chrome.downloads.search({id});
    const record = found && found[0];
    if (!record) return;
    updateJob(jobKeyForDownload(id), {
      state: record.state, bytesReceived: record.bytesReceived,
      totalBytes: record.totalBytes, fileSize: record.fileSize,
      filename: record.filename, error: record.error
    });
  } catch (_) { /* the delta values already stand */ }
}

async function startDownload(asset, index, domain) {
  const filename = safeDownloadName(asset, index, domain);
  try {
    const id = await chrome.downloads.download({
      url: asset.url, filename, conflictAction: 'uniquify', saveAs: false
    });
    if (typeof id !== 'number') throw new Error('The browser returned no download id');
    updateJob(jobKeyForDownload(id), {
      key: jobKeyForDownload(id), kind: 'chrome', id, url: asset.url, filename,
      domain, format: asset.format || asset.type, state: 'in_progress',
      bytesReceived: 0, totalBytes: 0
    });
    return {ok: true, id, filename};
  } catch (error) {
    return {ok: false, error: String(error && error.message || error), filename};
  }
}

async function reconcileDownloads() {
  await loadJobs();
  const unfinished = [...jobs.values()]
    .filter(job => job.kind === 'chrome' && typeof job.id === 'number'
      && !['complete', 'interrupted'].includes(job.state))
    .sort((a, b) => b.updatedAt - a.updatedAt)
    .slice(0, MAX_RECONCILE_PER_STARTUP);
  if (!unfinished.length) return;
  // Query by download id: a bounded list query would miss jobs older than the
  // newest N browser downloads, which is exactly the case that matters here.
  const records = await Promise.all(unfinished.map(job =>
    chrome.downloads.search({id: job.id}).then(found => found && found[0]).catch(() => null)));
  for (const record of records) {
    if (!record || !record.id) continue;
    updateJob(jobKeyForDownload(record.id), {
      id: record.id, url: record.url, filename: record.filename, state: record.state,
      bytesReceived: record.bytesReceived, totalBytes: record.totalBytes,
      fileSize: record.fileSize, error: record.error
    });
  }
}

/* ---------------------------------------------------------------- native side */

function nativeAlive() {
  return !!nativePort && nativeState.connected;
}

function connectNative() {
  if (nativePort) return nativePort;
  let port;
  try {
    port = chrome.runtime.connectNative(HOST_NAME);
  } catch (error) {
    setNativeState({connected: false, error: String(error && error.message || error)});
    return null;
  }
  nativePort = port;
  port.onMessage.addListener(handleNativeMessage);
  port.onDisconnect.addListener(() => {
    const lastError = chrome.runtime.lastError;
    nativePort = null;
    setNativeState({connected: false, error: lastError ? lastError.message : 'host closed'});
    for (const [requestId, waiter] of pendingNative) {
      clearTimeout(waiter.timer);
      pendingNative.delete(requestId);
      waiter.reject(new Error(lastError?.message || 'Companion disconnected before replying'));
    }
    broadcast({type: 'companion', state: nativeState});
  });
  return port;
}

function setNativeState(patch) {
  nativeState = Object.assign({}, nativeState, patch);
  broadcast({type: 'companion', state: nativeState});
}

function handleNativeMessage(message) {
  if (!message || typeof message !== 'object') return;

  if (message.action === 'pong') {
    setNativeState({
      connected: true,
      version: message.version || null,
      capabilities: Array.isArray(message.capabilities) ? message.capabilities : [],
      missingTools: !(message.ffmpegAvailable && message.ffprobeAvailable),
      localMediaPolicy: message.localMediaPolicy || null,
      error: null
    });
  } else if (message.action === 'assemble_progress') {
    updateJob(`companion-${message.jobId}`, {
      kind: 'companion', state: 'in_progress', bytesReceived: message.bytes || 0,
      percent: message.percent || 0, mediaTimeSeconds: message.mediaTimeSeconds || 0,
      elapsedSeconds: message.elapsedSeconds || 0
    });
  } else if (message.action === 'assemble_result') {
    const state = message.status === 'complete' ? 'complete'
      : (message.status === 'cancelled' ? 'cancelled'
        : (message.status === 'timeout' || message.status === 'aborted' ? 'interrupted' : 'failed'));
    updateJob(`companion-${message.jobId}`, {
      kind: 'companion', state, error: message.error || null,
      bytesReceived: message.bytes || 0, fileSize: message.bytes || 0,
      percent: state === 'complete' ? 100 : (message.percent || 0),
      filename: message.output || undefined, nestedAudit: message.nestedAudit || null,
      elapsedSeconds: message.elapsedSeconds || 0
    });
    scheduleIdleClose();
  }

  const waiter = message.requestId ? pendingNative.get(message.requestId) : null;
  if (waiter) {
    clearTimeout(waiter.timer);
    pendingNative.delete(message.requestId);
    waiter.resolve(message);
  }
}

function sendNative(payload, timeoutMs) {
  return new Promise((resolve, reject) => {
    if (!connectNative()) { reject(new Error('Companion host could not be started')); return; }
    const requestId = `r${Date.now().toString(36)}-${++requestCounter}`;
    const timer = setTimeout(() => {
      pendingNative.delete(requestId);
      reject(new Error('The companion did not answer in time'));
    }, timeoutMs || NATIVE_REQUEST_TIMEOUT_MS);
    pendingNative.set(requestId, {resolve, reject, timer});
    try {
      nativePort.postMessage(Object.assign({requestId}, payload));
    } catch (error) {
      clearTimeout(timer);
      pendingNative.delete(requestId);
      reject(error);
    }
  });
}

function scheduleIdleClose() {
  clearTimeout(idleCloseTimer);
  const stillRunning = [...jobs.values()].some(job => job.kind === 'companion'
    && ['in_progress', 'pending'].includes(job.state));
  if (stillRunning) return;
  // Close the host process when nothing is assembling: keeping a Python
  // interpreter parked for an idle extension would be wasteful and surprising.
  idleCloseTimer = setTimeout(disconnectNative, 20000);
}

function disconnectNative() {
  clearTimeout(idleCloseTimer);
  if (!nativePort) return;
  const port = nativePort;
  nativePort = null;
  setNativeState({connected: false, version: nativeState.version});
  try { port.disconnect(); } catch (_) { /* already gone */ }
}

async function pingCompanion() {
  try {
    await sendNative({action: 'ping'}, NATIVE_START_TIMEOUT_MS);
    // A ping alone is not a reason to keep a Python host process alive.
    scheduleIdleClose();
    return nativeState;
  } catch (error) {
    setNativeState({connected: false, missingTools: false, error: String(error.message || error)});
    return nativeState;
  }
}

async function probeStream(url) {
  try {
    return await sendNative({action: 'probe', url}, NATIVE_PROBE_TIMEOUT_MS);
  } catch (error) {
    return {action: 'probe_result', status: 'error', error: String(error.message || error)};
  }
}

async function assembleStream(asset, index, domain) {
  const jobId = `a${Date.now().toString(36)}${index}`;
  const filename = safeDownloadName(asset, index, domain);
  const key = `companion-${jobId}`;
  updateJob(key, {
    key, kind: 'companion', jobId, url: asset.url, filename, domain,
    format: asset.format, state: 'pending', bytesReceived: 0, totalBytes: 0, percent: 0
  });
  try {
    const started = await sendNative({
      action: 'assemble', url: asset.url, output: filename, jobId, async: true
    }, NATIVE_START_TIMEOUT_MS);
    if (started.action === 'error') throw new Error(started.error || 'Assembly refused');
    if (started.status !== 'started') throw new Error(started.error || 'Assembly did not start');
    updateJob(key, {state: 'in_progress', nestedAudit: started.nestedAudit || null});
    return {ok: true, jobId, filename};
  } catch (error) {
    updateJob(key, {state: 'failed', error: String(error.message || error)});
    return {ok: false, error: String(error.message || error)};
  }
}

async function cancelAssembly(jobId) {
  try {
    const result = await sendNative({action: 'cancel', jobId}, NATIVE_REQUEST_TIMEOUT_MS);
    return {ok: result.status === 'cancelled', status: result.status};
  } catch (error) {
    return {ok: false, error: String(error.message || error)};
  }
}

/* ------------------------------------------------------------------ messaging */

chrome.runtime.onConnect.addListener(port => {
  if (port.name !== UI_PORT_NAME) return;
  uiPorts.add(port);
  port.onDisconnect.addListener(() => uiPorts.delete(port));
  loadJobs().then(() => {
    port.postMessage({type: 'hydrate', jobs: [...jobs.values()], companion: nativeState});
  });
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  const type = message && message.type;
  if (!type) return false;
  const handlers = {
    'companion:ping': () => pingCompanion(),
    'companion:probe': () => probeStream(message.url),
    'companion:assemble': () => assembleStream(message.asset, message.index, message.domain),
    'companion:cancel': () => cancelAssembly(message.jobId),
    'download:start': () => startDownload(message.asset, message.index, message.domain),
    'download:cancel': async () => {
      const result = await chrome.downloads.cancel(message.id).catch(() => false);
      return {ok: !!result};
    },
    'download:open': async () => {
      await chrome.downloads.open(message.id).catch(() => {});
      return {ok: true};
    },
    'download:show': async () => {
      await chrome.downloads.show(message.id).catch(() => {});
      return {ok: true};
    },
    'jobs:list': async () => {
      await loadJobs();
      return {jobs: [...jobs.values()], companion: nativeState};
    },
    'jobs:clear': async () => {
      // Clearing history must never abandon a transfer that is still running.
      for (const [key, job] of jobs) {
        if (!['in_progress', 'pending'].includes(job.state)) jobs.delete(key);
      }
      await chrome.storage.local.set({[STORE_KEY]: [...jobs.values()]});
      broadcast({type: 'cleared', jobs: [...jobs.values()]});
      return {ok: true};
    }
  };
  const handler = handlers[type];
  if (!handler) return false;
  Promise.resolve().then(handler).then(sendResponse, error => sendResponse({error: String(error)}));
  return true;   // asynchronous reply
});

/* -------------------------------------------------------------------- startup */

chrome.runtime.onStartup.addListener(() => { reconcileDownloads(); });
chrome.runtime.onSuspend.addListener(() => { disconnectNative(); });

// Only download state is reconciled on wake. The companion is contacted lazily,
// when the popup asks, so an idle extension never leaves a host process running.
reconcileDownloads();

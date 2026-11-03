# KNOuX GrabFlow — Store Submission Kit (v0.6.1)

Status: **RELEASE CANDIDATE / NOT YET SUBMITTED OR PUBLISHED**
Product: KNOuX GrabFlow — Intelligent Media Discovery
Publisher: KNOuX LABS
Primary target: Google Chrome Manifest V3
Public privacy policy: https://gist.github.com/daynightae-cmyk/0af75547b262226946bc1b071f563a5f
Public support entry point: https://github.com/daynightae-cmyk
Private source repository: https://github.com/daynightae-cmyk/KNOuX-GrabFlow

## Chrome Web Store listing (English)

**Title:** KNOuX GrabFlow — Media & Video Finder

**Short description:** Discover accessible video, audio, streams, images, and documents on the page you choose. Download direct media locally.

**Category:** Productivity

**Detailed description:**

KNOuX GrabFlow finds accessible media on the webpage you choose, with a fast, video-first interface and Arabic/English language support.

Open any compatible page and select the KNOuX icon to scan the active tab on demand. Review exposed direct video and audio links, HLS/DASH playlist references, images, and downloadable resources. Filter, search, select, preview supported files, and request direct-file downloads through Chrome.

The download manager checks Chrome download states and file progress rather than claiming completion when only a request was accepted. Some media types, hosts, protected streams, and pages cannot be downloaded.

For advanced users on Windows, the separately installed KNOuX Native Media Companion can use FFmpeg/FFprobe to assemble supported, accessible, unprotected HLS/DASH playlists. The native companion is optional and must be installed and registered to the exact Chrome extension ID. Protected/DRM content, paywall bypass and YouTube protected video downloading are not supported.

GrabFlow has no advertising, tracker, remote KNOuX account, or hosted media-upload service. Your selected media source or CDN receives the ordinary requests needed to obtain the file. User-selected URLs may include query parameters and should not be shared carelessly.

**Key features:** on-demand media discovery; direct MP4/WebM/MKV/MOV detection; separate HLS/DASH classification; Arabic/English RTL/LTR; direct downloads; download history and errors; optional local Windows companion.

## بيانات المتجر بالعربية

**الاسم:** KNOuX GrabFlow — مكتشف وتحميل الوسائط

**الوصف المختصر:** اكتشف ملفات الفيديو والصوت والصور والمستندات المتاحة في الصفحة التي تختارها، ونزّل الملفات المباشرة إلى جهازك.

**الوصف:** إضافة خفيفة لاكتشاف الوسائط من صفحة الويب الحالية عند طلبك، مع واجهة عربية وإنجليزية، واكتشاف روابط الفيديو والصوت المباشرة وتصنيف قوائم HLS/DASH بصورة صادقة. يمكنك اختيار الملفات المتاحة وتحميلها عبر Chrome ومتابعة حالة التنزيل الفعلية. تتطلب معالجة البث المتكيف مساعد ويندوز اختياريًا وبرنامج FFmpeg منفصلًا. لا تدعم الإضافة تجاوز DRM أو القيود أو تنزيل المحتوى المحمي، ولا تضمن التوافق مع جميع المواقع.

## Store permission justifications

| Permission | Why required |
|---|---|
| activeTab | Restrict scanning to the tab the user explicitly invokes |
| scripting | Inject the page-media scanner only on demand |
| downloads | Start selected downloads, check their IDs/states, open downloaded files or folders |
| storage | Save language preference and local download-job metadata |
| nativeMessaging | Optional Windows host availability ping and user-selected unprotected HLS/DASH processing |

No persistent all-host access, background monitoring, remote code imports, accounts or telemetry are required.

## Review and verification notes

- This package is Chrome Manifest V3 and requires Chrome 110+.
- Real unpacked Chromium extension, Arabic RTL/English LTR, direct PNG + MP4 byte-verified downloads and FFprobe video/audio integrity were verified on Windows.
- Native Messaging handshake was tested with isolated Windows Chromium and temporary HKCU registration that was removed after testing.
- FFmpeg produced playable MP4s from local HLS master and DASH media fixtures in a separate CLI test.
- Physical Chrome toolbar-click `activeTab` grant, browser-to-native full HLS/DASH assembly, arbitrary websites, and cross-browser API compatibility still need target-browser verification.
- Native installation must be performed only when the user approves it and supplies their real Chrome extension ID. No Windows companion executable is shipped inside the browser ZIP.
- Mark the listing as free unless a paid service is actually introduced and disclosed.

## Graphics

Outside the browser ZIP, in the independently generated release QA directory:

- `GrabFlow-English-1280x800.png` — actual installed-extension screenshot.
- `GrabFlow-Arabic-1280x800.png` — actual RTL screenshot.
- `GrabFlow-Direct-Video-1280x800.png` — direct-download result from a synthetic local fixture.
- `GrabFlow-Promo-440x280.png` — branded promotional asset using the existing stag emblem.
- `GrabFlow-Marquee-1400x560.png` — optional promotional asset.
- `ASSET_SHA256.json` — dimensions, lengths and SHA-256 of all images.

## Publication destinations

| Platform | Official submission point | Readiness |
|---|---|---|
| Chrome Web Store | https://chrome.google.com/webstore/devconsole | Primary. Requires Google developer enrollment, one-time fee, 2FA, accurate listing/privacy and review. |
| Microsoft Edge Add-ons | https://developer.microsoft.com/en-us/microsoft-edge/extensions | Chromium target, free developer registration; must independently test Edge, then upload ZIP via Partner Center. |
| Opera Add-ons | https://addons.opera.com/developer/ | Requires Opera account and review; test Opera, and respect its screenshot/license requirements. |
| Mozilla Firefox AMO | https://addons.mozilla.org/developers/addon/submit/ | **Do not upload the Chrome build as already compatible**; port and verify nativeMessaging/chrome.downloads behavior first, then sign. |
| Apple Safari | https://appstoreconnect.apple.com/ | Separate Safari conversion, packaging, Apple Developer enrollment, TestFlight/review required. |
| GitHub Releases | https://github.com/daynightae-cmyk/KNOuX-GrabFlow/releases | The source repository is **PRIVATE**, so a release is not a public Store listing. |
| Brave and Vivaldi | https://chromewebstore.google.com/ | Chromium browsers can consume Chrome Web Store extensions subject to browser support; not separate universal Stores. |

## Non-negotiable release blockers

1. Actual toolbar-click activeTab verification; the automation uses an unpacked extension and synthetic fixture discovery.
2. Full browser-to-Native-Messaging stream assembly: CLI and native handshake are independently verified but not yet end-to-end together.
3. Untrusted redirects and nested media requests from the external FFmpeg process need SSRF/DNS rebinding hardening before advertising the native companion as broadly secure.
4. Cross-browser and Chrome Web Store human review, enrollment and publication are not yet completed.
5. The VS Code companion's full Extension Host runtime is not included in the Chrome CI browser checks.

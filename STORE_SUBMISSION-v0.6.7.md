# KNOuX GrabFlow — Store Submission Kit v0.6.7

**Status: PREPARED, NOT SUBMITTED, NOT APPROVED, NOT PUBLISHED.**

This kit is upload-ready material for a human operator with the required developer
accounts. It is not evidence of a Chrome Web Store or Microsoft Edge Add-ons
submission, certification or publication. No store URL exists yet.

| Field | Value |
|---|---|
| Product | KNOuX GrabFlow — Media & Video Finder |
| Publisher | KNOuX LABS |
| Version | `0.6.7` |
| Source tag | `v0.6.7` → `f72685077974d7c50806d7023b5011b4f215283e` |
| Browser packages | Chrome MV3 and Edge MV3, 12 files, 167,640 bytes each |
| Package SHA-256 | `313f4d2c4b62fb8304af173198814218caec6cc9f92df4de2bbb2ab0b713e028` |
| Public privacy policy | https://gist.github.com/daynightae-cmyk/0af75547b262226946bc1b071f563a5f |
| Public support | https://github.com/daynightae-cmyk |
| Source repository | https://github.com/daynightae-cmyk/KNOuX-GrabFlow (private) |
| Minimum Chrome/Edge version | Chromium 110+ (MV3) |
| Price | Free; no in-app purchases |
| Category | Productivity |
| Primary language | English (United States); Arabic localization included |

> The private source repository is **not** a valid public privacy-policy or support
> destination for store users. Use the public gist and public GitHub profile above.

## 1. Ready / not verified

**Prepared and locally verified**

- Chrome and Edge MV3 packages rebuilt deterministically from merged `main` and
  byte-identical to the published v0.6.7 release assets.
- Real unpacked Chromium and branded Edge runtime tests: popup, service worker,
  direct byte-verified downloads, RTL/LTR, worker persistence.
- Real branded Edge → registered Native Messaging host → FFmpeg HLS assembly:
  a 16.04 s H.264/AAC MP4 was produced and probed; progress and cancel paths were
  exercised; nested-reference audit passed.
- Truthful Inspector metadata for HLS/DASH: playlist size is labelled separately,
  media size is unknown until assembly/download, and unavailable bitrate is never
  shown as `0 kbps`.
- 23/23 local test programs pass; CI run `41891716674` on merged `main` passed all
  five jobs and SonarCloud.
- 1280×800 screenshots, 440×280 promo tile, optional 1400×560 marquee, 300×300
  Edge logo and 128×128 Chrome icon generated from real screenshots/brand art.

**Not verified / human acceptance still required**

- A physical toolbar click that grants `activeTab` in a normal installed browser.
- Real OS clipboard acceptance for the popup's copy actions.
- Third-party CDN streams, expiring signed URLs and multi-gigabyte stress.
- Firefox, Safari, Opera, Brave or Vivaldi runtime compatibility.
- Chrome Web Store or Edge Add-ons review, certification, approval or publication.
- Store console enrollment, fees, 2FA, identity verification and legal acceptance.

See `TEST-REPORT-v0.6.7.md` for the complete verification boundary.

## 2. Chrome Web Store listing — English

**Name (37 characters):**

```text
KNOuX GrabFlow - Media & Video Finder
```

**Short description (129 characters):**

```text
Find direct video, HLS/DASH streams, audio, images and documents on the page you choose. Download or assemble locally, privately.
```

**Category:** Productivity

**Language:** English (United States). Add Arabic (Saudi Arabia) as a localized
listing using Section 4 if the dashboard supports it.

**Detailed description:**

```text
KNOuX GrabFlow finds accessible media on the page you choose, with a video-first interface and Arabic/English support.

Open a page and click the GrabFlow toolbar icon. GrabFlow scans only that active tab, on demand, and lists exposed direct video and audio links, HLS/DASH playlist references, images, documents and subtitle files. Search, filter, sort, preview supported files, select items and download direct files through your browser.

The download manager follows the browser's actual download state and reports progress, completion and errors. It does not call a download complete merely because a request was accepted.

On Windows, the optional KNOuX Native Media Companion adds local FFprobe inspection and FFmpeg HLS/DASH assembly for streams you are permitted to access. The Inspector is explicit about what it knows: for a playlist it shows "Playlist file size" and "Media size - Unknown until assembled or downloaded", and it shows "Bitrate - Not available" instead of inventing 0 kbps. The companion is installed separately, is not bundled in the browser ZIP, and is not required for direct downloads.

GrabFlow has no account, advertising, analytics, tracking or KNOuX-hosted media-upload service. Scan results stay in the extension; the selected media source or CDN receives the ordinary requests needed to retrieve the file. URLs may contain sensitive query parameters, so treat them with care.

GrabFlow does not bypass DRM, paywalls or access controls, and does not download protected YouTube content. Not every media source is discoverable or downloadable. Only save media you have permission to use.

Free. No in-app purchases.
```

**Screenshot order and captions (1280×800):**

1. `GrabFlow-v0.6.7-English-1280x800.png` - real unpacked MV3 popup capture, English LTR, on a branded backdrop.
2. `GrabFlow-v0.6.7-Arabic-RTL-1280x800.png` - real unpacked MV3 popup capture, Arabic RTL, on a branded backdrop.
3. `GrabFlow-v0.6.7-Direct-Video-1280x800.png` - real direct-download completion from a local fixture, on a branded backdrop.

**Promotional images:**

- Small promo tile: `GrabFlow-v0.6.7-Promo-440x280.png`
- Marquee: `GrabFlow-v0.6.7-Marquee-1400x560.png` (optional)
- Store icon: `GrabFlow-v0.6.7-Icon-128x128.png`

## 3. Chrome Web Store — privacy practices

### Single purpose

```text
GrabFlow discovers accessible media on the active tab the user explicitly scans and downloads user-selected direct files. An optional, separately installed local Windows companion can inspect and assemble unprotected HLS/DASH streams using the user's own FFmpeg/FFprobe.
```

### Permission justifications

| Permission | Justification to paste |
|---|---|
| `activeTab` | Used only after the user clicks the GrabFlow toolbar icon. Grants temporary access to the active tab so the on-demand scanner can read media references. There are no host permissions and no persistent all-sites access. |
| `scripting` | Injects the packaged page-media scanner into the active tab only when the user invokes the extension. No remote code is loaded or executed. |
| `downloads` | Starts user-selected downloads, tracks their browser download IDs and state/progress, and offers open-file/open-folder actions. Download metadata is not uploaded to KNOuX. |
| `storage` | Stores the language preference and a bounded local list of GrabFlow download jobs (maximum 80 entries) in `chrome.storage.local`. It is not synchronized to a KNOuX account. |
| `nativeMessaging` | Connects only when the user requests it to a separately installed local Windows host for FFprobe inspection and FFmpeg HLS/DASH assembly. The host is registered for one explicit extension ID and is not required for direct downloads. |

### Remote code

Select **“No, I am not using remote code.”**

All extension JavaScript is packaged in the ZIP. The optional native companion is
a separately installed local program reached through Native Messaging; it is not
downloaded or executed by the extension as remotely hosted code.

### Data usage checkboxes

GrabFlow processes data locally on the user's device. Chrome policy still requires
disclosure of locally handled user data, so select the following categories:

| Data category | Select? | Why |
|---|---|---|
| Website content | **Yes** | Page URL, title, media URLs, markup metadata and visible media properties are read locally after the user invokes the scanner. They are not transmitted to KNOuX. |
| Web history | **Yes** | The active tab's URL/title is read on demand. GrabFlow does not read or list the browser's history. |
| User activity | **Yes** | Download job state, byte progress and recent GrabFlow jobs are kept locally so the popup can show them after reopening. |
| Personally identifiable information | No | No account, name, email, address or identifier is collected by KNOuX. |
| Health information | No | Not accessed. |
| Financial and payment information | No | No payments or financial data. |
| Authentication information | No | No passwords, cookies or tokens are read or transmitted by GrabFlow. |
| Personal communications | No | Not accessed. |
| Location | No | Not accessed. |

Select all three Limited Use certifications:

- Do not sell or transfer user data to third parties outside approved use cases.
- Do not use or transfer user data for purposes unrelated to the single purpose.
- Do not use or transfer user data to determine creditworthiness or for lending.

**Privacy policy URL:**

```text
https://gist.github.com/daynightae-cmyk/0af75547b262226946bc1b071f563a5f
```

### Distribution

- Visibility: **Public**
- Regions: all regions (or the owner's approved market list)
- Pricing: **Free**
- Mature content: **No**

### Review notes for Chrome

```text
No account or login is required. To test the core feature:
1. Load the ZIP unpacked at chrome://extensions with Developer mode enabled.
2. Open any page containing a direct MP4, PNG or audio link (a local fixture is fine).
3. Click the GrabFlow toolbar icon. The popup scans only that active tab on demand.
4. Select the file and use Download. Chrome's own download progress/state is used.
5. Switch the popup language between English and Arabic to see LTR/RTL.

The optional Windows native companion is NOT required and is NOT bundled in the
ZIP. Without it, the popup truthfully reports that the companion is not installed;
direct downloads still work. No host permissions, remote code, credentials or
telemetry are used. The extension does not bypass DRM, paywalls or access controls.
```

## 4. Arabic localized listing

Use this as an additional locale when the store dashboard supports localized
listings. The manifest already ships Arabic UI strings.

**الاسم:**

```text
KNOuX GrabFlow - اكتشاف الوسائط والفيديو
```

**الوصف المختصر (≤132 حرفًا):**

```text
اكتشف الفيديو المباشر وبثوث HLS/DASH والصوت والصور والمستندات في الصفحة التي تختارها، ونزّلها محليًا.
```

**الوصف التفصيلي:**

```text
يبحث KNOuX GrabFlow عن الوسائط المتاحة في الصفحة التي تختارها، بواجهة تركّز على الفيديو وتدعم العربية والإنجليزية.

افتح الصفحة واضغط أيقونة GrabFlow في شريط الأدوات. يفحص GrabFlow التبويب النشط فقط وعند الطلب، ويعرض روابط الفيديو والصوت المباشرة، ومراجع بث HLS/DASH، والصور، والمستندات، وملفات الترجمة. يمكنك البحث والتصفية والترتيب ومعاينة الملفات المدعومة وتحديد العناصر وتنزيل الملفات المباشرة عبر المتصفح.

يتابع مدير التنزيلات حالة التنزيل الفعلية ويعرض التقدم والاكتمال والأخطاء، ولا يعتبر التنزيل مكتملًا لمجرد قبول الطلب.

على Windows، يضيف رفيق KNOuX Native Media Companion الاختياري فحصًا محليًا عبر FFprobe وتجميعًا لبثوث HLS/DASH عبر FFmpeg، للبثوث المسموح لك بالوصول إليها. يوضّح المفتش ما يعرفه بدقة: يعرض "حجم ملف قائمة التشغيل" منفصلًا عن "حجم الوسائط - غير معروف حتى التجميع أو التنزيل"، ويعرض "معدل البت - غير متاح" بدلًا من اختراع 0 kbps. يُثبّت الرفيق بشكل منفصل، ولا تتضمن حزمة المتصفح FFmpeg، وهو غير مطلوب للتنزيلات المباشرة.

لا توجد حسابات أو إعلانات أو تحليلات أو تتبّع أو خدمة استضافة وسائط تابعة لـKNOuX. تبقى نتائج الفحص داخل الإضافة؛ ويتلقى مصدر الوسائط أو شبكة CDN التي تختارها الطلبات العادية اللازمة لجلب الملف. قد تتضمن الروابط معاملات استعلام حساسة، فتعامل معها بحذر.

لا تتجاوز GrabFlow أنظمة DRM أو جدران الدفع أو ضوابط الوصول، ولا تنزّل محتوى YouTube المحمي. ليست كل المصادر قابلة للاكتشاف أو التنزيل. نزّل فقط الوسائط التي تملك إذنًا باستخدامها.

مجاني. لا توجد مشتريات داخل التطبيق.
```

## 5. Microsoft Edge Add-ons listing

The Edge package is the same 12-file MV3 payload as Chrome. The manifest supplies
the extension name and short description; Partner Center reads them from the ZIP.

**Extension name:** `KNOuX GrabFlow - Media & Video Finder`

**Short description (from manifest, 129 characters):**

```text
Find direct video, HLS/DASH streams, audio, images and documents on the page you choose. Download or assemble locally, privately.
```

**Description (minimum 250 characters; use the Chrome detailed description in
Section 2):**

Use the same English detailed description. It is longer than the Edge minimum and
below the 10,000-character maximum.

**Category:** Productivity

**Website:** https://github.com/daynightae-cmyk (public profile)

**Support contact:** https://github.com/daynightae-cmyk

**Privacy policy:** https://gist.github.com/daynightae-cmyk/0af75547b262226946bc1b071f563a5f

**Search terms (7 terms, 14 words, each ≤30 characters):**

```text
video downloader
media finder
HLS downloader
DASH stream
stream inspector
FFmpeg companion
media discovery
```

**Assets for each language:**

- Logo: `GrabFlow-v0.6.7-Logo-300x300.png`
- Small promotional tile: `GrabFlow-v0.6.7-Promo-440x280.png`
- Large promotional tile: `GrabFlow-v0.6.7-Marquee-1400x560.png` (optional)
- Screenshots (maximum 6; use the three 1280×800 images in Section 2)
- YouTube video: none

**Edge privacy page:** use the same single-purpose text, permission
justifications, remote-code declaration and data-usage selections as Section 3.
Map the Edge labels to the same meanings; do not under-disclose locally processed
website content or download activity.

**Notes for certification:**

```text
No account, login or test credentials are required.

Basic test path:
1. Upload/install the ZIP in Microsoft Edge (Developer mode / Load unpacked).
2. Open a page with a direct MP4, PNG or audio link; a local fixture is fine.
3. Click the GrabFlow toolbar icon and scan the active tab.
4. Select the file and download it; Edge's download state is used.
5. Switch the popup language to Arabic to verify RTL.

The optional Windows native companion is separate and not bundled. Without it,
the popup reports the companion as not installed; direct downloads still work.
The package requests only activeTab, scripting, downloads, storage and
nativeMessaging. It contains no remote code, host permissions, analytics or
telemetry, and it does not bypass DRM or access controls.
```

## 6. Shared privacy and data-disclosure matrix

| Question | Answer |
|---|---|
| Does GrabFlow create an account? | No. |
| Does it use advertising, analytics or telemetry? | No. |
| Does it sell or transfer user data to KNOuX? | No. |
| Does it read cookies, passwords or authentication tokens? | No. |
| Does it read general browser history? | No; only the active tab's URL/title after invocation. |
| Where do scan results live? | In the extension's memory during use; job metadata may persist locally in `chrome.storage.local`. |
| What is stored locally? | Language choice and at most 80 GrabFlow job records (URL, filename, domain, format, state, byte counts, nested-audit result). |
| Is local data synchronized to a KNOuX server? | No. |
| Can the user clear it? | Yes, through the in-extension Clear History control; uninstalling the extension removes extension-local storage as managed by the browser. |
| Does the native companion receive browser cookies? | No. It receives the user-selected URL, output name and job/action metadata. |
| Does FFmpeg ship in the ZIP? | No. FFmpeg/FFprobe and the Python host are separately installed local dependencies. |
| Does it bypass DRM, paywalls or access controls? | No. |
| Does it download protected YouTube content? | No; YouTube media is excluded from the scanner by product policy. |
| Is remote code used? | No. |
| Is the native companion remote code? | No; it is a separately installed local program invoked through Native Messaging. |

## 7. Generated assets

All paths below are relative to `store-assets/0.6.7/` in the repository and to
the `assets/` subdirectory of the assembled submission bundle.

| File | Dimensions | Purpose |
|---|---|---|
| `GrabFlow-v0.6.7-English-1280x800.png` | 1280×800 | Chrome/Edge screenshot 1 (real MV3 popup, English LTR) |
| `GrabFlow-v0.6.7-Arabic-RTL-1280x800.png` | 1280×800 | Chrome/Edge screenshot 2 (real MV3 popup, Arabic RTL) |
| `GrabFlow-v0.6.7-Direct-Video-1280x800.png` | 1280×800 | Chrome/Edge screenshot 3 (real direct-download completion) |
| `GrabFlow-v0.6.7-Promo-440x280.png` | 440×280 | Chrome small promo tile / Edge small promotional tile |
| `GrabFlow-v0.6.7-Marquee-1400x560.png` | 1400×560 | Optional Chrome marquee / Edge large promotional tile |
| `GrabFlow-v0.6.7-Logo-300x300.png` | 300×300 | Edge extension logo (Chrome can use the 128×128 icon) |
| `GrabFlow-v0.6.7-Icon-128x128.png` | 128×128 | Chrome store icon |
| `ASSET_SHA256.json` | — | Dimensions, byte lengths and SHA-256 for every asset |

The popup imagery in all three screenshots is an unmodified crop of a real
unpacked-extension capture from the verified MV3 run, placed on a branded
1280×800 backdrop with descriptive text. No popup UI is simulated, redrawn or
replaced. The promo, marquee and logo use the repository's KNOuX stag emblem;
they are brand art, not screenshots of functionality.

## 8. Upload checklist

In the assembled `store-submission/` bundle, the two ZIPs are under `packages/`
and the images are under `assets/`. The repository release workspace keeps the
ZIPs at its root for direct GitHub Release use.

### Chrome Web Store

1. Confirm the developer account is enrolled, the one-time fee is paid, 2FA is
   enabled and the publisher identity is verified.
2. Upload `KNOuX-GrabFlow-CHROME-v0.6.7.zip` (manifest at the ZIP root).
3. Paste the name, short description, detailed description, category and language.
4. Add the three 1280×800 screenshots, 440×280 tile, optional 1400×560 marquee and
   128×128 icon.
5. Complete Privacy practices exactly as Section 3, including the public privacy
   policy URL and all three Limited Use certifications.
6. Set distribution to Public, Free, no mature content.
7. Use the review notes in Section 3, then submit for review.
8. After approval, record the live listing URL and verify it publicly. Until then,
   do not claim Chrome Web Store approval or publication.

### Microsoft Edge Add-ons

1. Confirm the Partner Center account is registered for the Edge program and the
   publisher identity is verified.
2. Create the extension, upload `KNOuX-GrabFlow-EDGE-v0.6.7.zip`, and confirm the
   package validates.
3. Complete Availability, Properties and Privacy. Use the same truthful
   declarations as Section 3 and 5.
4. Add the logo, small tile, optional large tile and the three 1280×800 screenshots
   for English (and Arabic if the locale is enabled).
5. Add the seven search terms and the certification notes.
6. Submit. Edge certification can take up to seven business days after submission.
7. After approval, record the live listing URL and verify it publicly. Until then,
   do not claim Edge Add-ons approval or publication.

## 9. Explicit non-claims and blockers

- This kit does **not** prove that any store accepted, approved or published the
  extension.
- The private repository is not a public support page, privacy policy or store
  listing.
- Do not upload `KNOuX-GrabFlow-CHROME-v0.6.2.zip` or the v0.6.1 kit; both are
  superseded.
- Do not add permissions, remote code, analytics or host access to “help” review.
- Do not bundle FFmpeg, FFprobe, Python or the native host inside the browser ZIP.
- Do not describe the native companion as required for direct downloads.
- Do not claim `activeTab` physical-click acceptance, OS clipboard acceptance,
  third-party CDN/multi-GB stress, non-Chromium compatibility or store review until
  a human has completed those checks.
- The v0.6.7 tag is immutable. Submission-kit and VS Code changes made after the tag
  do not change the browser package bytes; verify the SHA-256 before every upload.

## 10. Rebuild and verify

From the repository root:

```powershell
python scripts/package.py
python scripts/build-store-assets.py --version 0.6.7
python scripts/validate-store-kit.py
python scripts/assemble-store-submission.py
python scripts/package-vscode.py
```

`package.py` must print the same SHA-256 for both browser packages:
`313f4d2c4b62fb8304af173198814218caec6cc9f92df4de2bbb2ab0b713e028`.
`build-store-assets.py` must reproduce the tracked asset hashes without modifying
the real screenshots; it reads those captures and composites them onto the
branded backdrops. `validate-store-kit.py` must end with `STORE_KIT_VALID`.
`assemble-store-submission.py` writes the upload bundle under
`..\_releases\KNOuX-GrabFlow-v0.6.7\store-submission\`; it refuses to replace
different existing bytes. `package-vscode.py` writes the companion VSIX and its
SHA-256 under `dist/`. If any hash differs, stop and investigate; do not upload.

## 11. Public privacy policy

The public gist was updated from the v0.6.1 policy to the current v0.6.7 policy on
2026-11-04. It covers the MV3 service worker, bounded local job storage, the
optional native companion, nested-reference auditing and the deletion behavior.

URL: https://gist.github.com/daynightae-cmyk/0af75547b262226946bc1b071f563a5f

The same policy is tracked in `PRIVACY.md`; the gist and the repository file must
stay identical. If the policy changes, update both and re-check the store privacy
answers before uploading.

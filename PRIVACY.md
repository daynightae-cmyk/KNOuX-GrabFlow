# KNOuX GrabFlow — Privacy Policy

**Product:** KNOuX GrabFlow browser extension (Manifest V3, Chrome and Edge)
**Publisher:** KNOuX LABS
**Effective date:** November 4, 2026
**Applies to:** GrabFlow v0.6.5 and its optional separately installed Windows companion

## Overview

GrabFlow helps you inspect media references on a webpage you choose and, when you request it, download accessible direct media files. The optional Windows companion can use locally installed FFmpeg/FFprobe to process supported, unprotected HLS/DASH streams. GrabFlow does not have an analytics service, remote account system, advertising SDK, or KNOuX-hosted media-upload endpoint.

## Data accessed when you use the extension

When you invoke GrabFlow on a webpage, its on-demand scanner may read the active page's URL, title, visible media URLs, HTML media and link metadata, video/audio properties, subtitle references, supported structured metadata and resource entries. These page details can include URLs with query parameters, which may be sensitive. Scan results are used locally in the popup to show media sources and are not automatically uploaded to KNOuX LABS.

When you choose to preview or download media, Chrome or the optional media companion may contact the selected source's servers. Those servers can receive ordinary network information such as your IP address and the URL requested, including any URL query parameters. The destination site or its CDN controls its own data practices and redirects.

## Permissions and purpose

- **activeTab:** Temporary access to the current tab when you invoke the extension. No blanket all-sites host permission is requested.
- **scripting:** Execute the on-demand page-media scanner in the tab you selected.
- **downloads:** Start selected downloads, check their progress/completion/error status using their Chrome download IDs, and offer file/folder actions. Chrome's downloads permission can technically access wider browser-download metadata; GrabFlow's current code queries its tracked download IDs and does not upload Chrome download history.
- **storage:** Save language preference and a bounded local list of GrabFlow download jobs and their associated metadata in `chrome.storage.local`, including URLs, filenames, states and download IDs. You may clear GrabFlow's local history through its Clear History control; Chrome's separate download history and the files themselves are not erased by this action.
- **nativeMessaging:** Connect, when requested by the popup, to the optional locally installed `com.knoux.grabflow.companion` host for availability checks and user-selected media actions. The host can receive a stream URL, output filename and job/action metadata. The host is configured for one explicitly registered extension ID.

## Background service worker

GrabFlow v0.6.5 registers a Manifest V3 service worker. Its purpose is narrow and it is worth
stating plainly, because "background" is a word people reasonably read as "watching".

The worker does two things:

- It receives `chrome.downloads.onChanged` events so download progress, completion and failure
  keep being reported after you close the popup, and so the state is still there when you reopen
  it. Before this, that listener lived in the popup document and stopped working the moment the
  popup closed.
- It holds the native companion connection, so a long FFmpeg assembly can stream progress and be
  genuinely cancelled. The host process is closed once no assembly is running; an idle extension
  does not leave a process behind.

The worker does **not** and **cannot**: observe or modify network traffic (no `webRequest`, no
`declarativeNetRequest`), read cookies or browsing history, use the debugger, hold any host
permission, or scan a page on its own. It requests no permissions beyond the five above, and
`tests/test-scanner.cjs` and `tests/test-utilities.cjs` fail the build if the manifest or the
worker source drifts from that. Page scanning still happens only when you open the popup, only in
the tab you are looking at, and only by reading that page's markup.

## Storage, retention and deletion

Media scan results are held in extension memory during use; active job records and language choice can persist locally across popup sessions. Since v0.6.3 those records live under a single bounded `grabflowJobs` list in `chrome.storage.local` — at most 80 entries, oldest finished job removed first — written by the service worker rather than by the popup. Each record holds the media URL, the output filename, the domain, the format, a state, byte counts and, for companion assemblies, the nested-URL audit result. GrabFlow does not synchronize this state to a KNOuX cloud account. Use the in-extension Clear History control to clear its locally tracked download jobs (jobs still transferring are kept so they are not abandoned); Chrome's or Edge's separate download history and the files themselves are not erased by this action. Files already downloaded remain on your computer until you delete them separately.

## Native companion, FFmpeg and network access

The Windows native companion is optional and separately installed. When you explicitly request HLS/DASH assembly, the companion launches FFmpeg with argument-array subprocess execution and uses the media URLs you selected to retrieve playlist and segment resources. It does not receive browser cookies or read the browser's credential store as part of this workflow. It does not promise that a media URL is free from sensitive tokens in query parameters. FFmpeg is a separate local dependency; it is not packaged inside the extension.

Since v0.6.3 the companion also does the following, which reduces but does not eliminate the risk of a malicious media host:

- fetches the manifest itself before FFmpeg starts, over a connection pinned to an address that already passed validation, re-validating every redirect hop;
- validates every nested reference the manifest points to (keys, initializations, variants, segments), so a public playlist cannot make the tool reach a private or loopback address;
- confines FFmpeg to an explicit transport whitelist and playlist-extension whitelist;
- enforces ceilings on manifest size, nested reference count, output size, concurrent jobs and elapsed time, aborting rather than exhausting the machine.

The companion's media source may refer to multiple CDN hosts and may redirect. Do not use the companion with private, confidential, protected, or unauthorized media. It is not a VPN or anonymity service.

## Data sharing, advertising and tracking

No built-in advertising, behavioral analytics, cross-site tracking, user-profile sale, or automatic transfer of scan results to KNOuX servers is implemented. Requests made to a selected media source, and any third-party services that source depends on, are outside KNOuX's control. No user account is required.

## Limits and user responsibility

GrabFlow does not circumvent DRM, access controls, or paywalls and does not support downloading protected YouTube content. Not every media source is discoverable or downloadable. You should only download or assemble material you have permission to save.

## Changes and questions

This policy will be updated when features or data practices change. For questions or requests related to the extension, contact KNOuX LABS via: https://github.com/daynightae-cmyk (public profile). The project's source repository is private, so a public copy of this policy must be provided in store dashboards before submission.

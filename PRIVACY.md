# KNOuX GrabFlow — Privacy Policy

**Product:** KNOuX GrabFlow Chrome extension (Manifest V3)
**Publisher:** KNOuX LABS
**Effective date:** November 3, 2026
**Applies to:** GrabFlow v0.6.1 and its optional separately installed Windows companion

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

## Storage, retention and deletion

Media scan results are held in extension memory during use; active job records and language choice can persist locally across popup sessions. GrabFlow does not synchronize this state to a KNOuX cloud account. Use the in-extension Clear History control to clear its locally tracked download jobs; uninstalling the extension also removes its extension-local storage as managed by the browser. Files already downloaded remain on your computer until you delete them separately.

## Native companion, FFmpeg and network access

The Windows native companion is optional and separately installed. When you explicitly request HLS/DASH assembly, the companion launches FFmpeg with argument-array subprocess execution and uses the media URLs you selected to retrieve playlist and segment resources. It does not receive browser cookies or read the browser's credential store as part of this workflow. It does not promise that a media URL is free from sensitive tokens in query parameters. FFmpeg is a separate local dependency; it is not packaged inside the Chrome extension.

The native companion's media source may refer to multiple CDN hosts and may redirect. Do not use the companion with private, confidential, protected, or unauthorized media. It is not a VPN or anonymity service.

## Data sharing, advertising and tracking

No built-in advertising, behavioral analytics, cross-site tracking, user-profile sale, or automatic transfer of scan results to KNOuX servers is implemented. Requests made to a selected media source, and any third-party services that source depends on, are outside KNOuX's control. No user account is required.

## Limits and user responsibility

GrabFlow does not circumvent DRM, access controls, or paywalls and does not support downloading protected YouTube content. Not every media source is discoverable or downloadable. You should only download or assemble material you have permission to save.

## Changes and questions

This policy will be updated when features or data practices change. For questions or requests related to the extension, contact KNOuX LABS via: https://github.com/daynightae-cmyk (public profile). The project's source repository is private, so a public copy of this policy must be provided in store dashboards before submission.

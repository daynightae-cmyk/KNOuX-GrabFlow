# KNOuX GrabFlow™ — Privacy Disclosure (Draft for v0.1.0)

**Summary:** KNOuX GrabFlow does not maintain an account, collect analytics, transmit browsing history to a developer-operated server or load code from a third party.

### Website data

When a user clicks the extension on the currently active webpage, the extension reads that page's DOM (image URLs, video file URLs and direct document links, along with the page's hostname/title) in the active browser tab. The extracted information is passed to the extension popup **locally on the user's device** to enable display, search, selection and copying. It is not stored by the extension for future sessions. It does not inspect passwords, cookies or hidden authenticated content intentionally.

### Downloads

When the user chooses to download, Google Chrome's `downloads` API requests the selected file URL from its original web host as a regular browser download. That website/server may receive an ordinary browser download request, including standard browser request metadata. No file is uploaded to KNOuX-operated infrastructure. Actual download success depends on the original website's rules.

### Stored preferences

The extension stores only the interface language setting (`ar` or `en`) in Chrome's local extension storage. It does not intentionally collect names, email addresses, payment details or behavioral analytics.

### Third parties

No analytics, advertising SDKs or external script services are integrated. The files users download originate from websites chosen by those users, subject to those sites' own policies.

### Controls

Users control when scanning occurs by clicking the extension icon and can remove the language preference by clearing extension storage/uninstalling the extension.

### Contact and publication

This is a source-based draft. Before any public Chrome Web Store submission, the publisher must provide a real support contact, accurate developer identity and an accessible public URL to the finalized privacy policy. Verify actual runtime behavior and keep this disclosure aligned with the shipped version.

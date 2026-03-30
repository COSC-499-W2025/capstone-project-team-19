# Known Bugs

This document lists **specific cases where an implemented feature does not behave as expected** under normal use. Workarounds are noted when we have them.

**Optional integrations** (Groq, GitHub OAuth, Google Drive OAuth) need API keys and OAuth client settings in `.env` (see the installation guide). If those are missing, the related flows are unavailable or will prompt you to configure them—that is **expected configuration**, not a bug.

---

## Issues

- **Safari-specific rendering/loading issue on the Insights page:** In some cases, the Insights page does not fully load on the first refresh in Safari and may require multiple refreshes. This issue appears to be limited to Safari and was not observed consistently in other browsers. **Workaround:** If the page looks incomplete, try reloading again (sometimes more than once).
- **Google Drive - “Load Drive Files” not appearing after Connect:** After clicking **Connect** and returning to the app, the **Load Drive Files** action sometimes does not appear. **Workaround:** Disable the pop-up blocker.
- **No “forgot password” / account recovery:** Users who forget their password cannot reset it via email or a public flow. Logged-in users can change their password from the profile page if they know the current password.
- **Duplicate project - “new version” still asks for classification:** When a project is flagged as a duplicate from a *different* upload and the user chooses **new version of the same project**, the flow still prompts for classification even though the original project was already classified.
- **Intermittent “Failed to fetch” in the app:** The UI sometimes shows **Failed to fetch** (for example on a step such as Deduplication during upload). The underlying cause is not yet known. **Workaround:** Refresh or reload the page; repeating once or twice usually clears it. This does not appear to be limited to a particular browser.
# Known Bugs

This document lists **specific cases where an implemented feature does not behave as expected** under normal use. Workarounds are noted when we have them.

**Optional integrations** (Groq, GitHub OAuth, Google Drive OAuth) need API keys and OAuth client settings in `.env` (see the installation guide). If those are missing, the related flows are unavailable or will prompt you to configure them—that is **expected configuration**, not a bug.

---

## Issues

- **Safari-specific rendering/loading issue on the Insights page:** In some cases, the Insights page does not fully load on the first refresh in Safari and may require multiple refreshes. This issue appears to be limited to Safari and was not observed consistently in other browsers. **Workaround:** If the page looks incomplete, try reloading again (sometimes more than once).
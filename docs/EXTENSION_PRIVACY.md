# ResumeIQ Extension: Privacy Policy & Permissions Justification

**Extension Version:** 2.1.0  
**Last Updated:** October 2026  
**Target Platform:** Google Chrome, Microsoft Edge, Brave (Chromium Manifest V3)

---

## 1. Core Privacy Commitments

ResumeIQ operates on strict privacy and data minimization principles:
1. **Never Collect Unrelated Browsing Activity:** We only extract text when explicitly triggered by the user on job posting pages or when the user highlights job description text.
2. **Zero Password Storage:** The extension never handles, prompts for, or stores account passwords. Authentication is handled via short-lived pairing codes and scoped, revocable tokens.
3. **No Third-Party Ad Trackers or Telemetry:** The extension contains zero third-party advertising SDKs, analytic pixels, or tracker scripts.
4. **Zero-Hallucination & Evidence-First:** The extension processes resumes and job descriptions solely to compute compatibility against verified evidence provided by the user.

---

## 2. Manifest V3 Permissions Justification

Every permission requested in `manifest.json` is strictly required for the core product function:

| Permission | Technical Requirement | User-Facing Purpose |
| :--- | :--- | :--- |
| `sidePanel` | Chrome Side Panel API (`chrome.sidePanel`) | Renders the match dashboard, skill gaps, and quick actions alongside the active web page without covering job text. |
| `storage` | Local extension storage (`chrome.storage.local`) | Persists pairing tokens, active resume selection, score threshold preferences, and cached match results locally. |
| `contextMenus` | Context menu API (`chrome.contextMenus`) | Adds the *"Check resume match with ResumeIQ"* right-click shortcut on highlighted job text. |
| `tabs` | Tab inspection (`chrome.tabs.query`) | Identifies the URL and title of the active job tab to open the side panel and check if the page is a job post. |
| `activeTab` | Temporary active tab access | Allows extracting DOM text from the currently focused job tab when user presses `Alt+Shift+M` or clicks the action icon. |
| `scripting` | Programmatic script execution | Fallback injection mechanism on dynamic single-page applications. |
| `host_permissions: ["<all_urls>"]` | Content script execution | Enables job extraction across public job boards (LinkedIn, Indeed, Naukri, Glassdoor, Wellfound) and internal ATS portals (Workday, Greenhouse, Lever, company career domains). |

---

## 3. Data Processing & Security Architecture

### 3.1 Device Pairing Security
- Web App generates a single-use 6-character code (`PAIR-XXXXXX`) valid for 10 minutes.
- Extension sends the code to `/api/v1/extension/auth/pair`.
- Server returns a dedicated, scoped `extension_token` and `refresh_token`.
- User can revoke the token at any time in the web application or directly from the extension settings.

### 3.2 Job Text Sanitization & Defense
Before captured text is analyzed:
- Invisible unicode characters (zero-width spaces `\u200B`, soft hyphens, directional overrides) are stripped.
- HTML tags, scripts, navigation bars, and tracking elements are filtered out.
- Prompt injection patterns (e.g. `"Ignore previous instructions"`, `"System prompt override"`) are neutralized and flagged.

### 3.3 Storage Location
- Authentication tokens and preference settings are stored inside the browser's sandboxed `chrome.storage.local`.
- No sensitive profile data is stored unencrypted in public browser locations.

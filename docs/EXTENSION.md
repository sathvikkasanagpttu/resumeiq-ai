# ResumeIQ Browser Extension (v2.1)
**"JD → Resume Match in One Click"**

The ResumeIQ Browser Extension brings evidence-first resume matching, skill gap discovery, and grounded tailoring directly to job postings on LinkedIn, Indeed, Naukri, Glassdoor, Wellfound, Greenhouse, Lever, Workday, and any custom career page.

---

## 1. Core Philosophy & Rules

- **Strict Evidence Grounding:** Never invent candidate experience, metrics, titles, or skills. The extension only evaluates and suggests based on verifiable facts in the candidate's **Canonical Profile**.
- **Deterministic Match Verdicts:** Verdicts (*Strong Match*, *Good Match*, *Partial Match*, *Weak Match*) are derived exclusively from mathematically calculated threshold scores across 8 weighted evidence pillars—never from an LLM guess.
- **Two-Tier Response Architecture:**
  1. **Tier 1 (< 2 seconds):** Deterministic compatibility score, 8-pillar component bars, matched skills with proof snippets, transferable skills, and categorized gaps.
  2. **Tier 2 (Streamed SSE):** Evidence-grounded "Why this verdict" explanation streamed in real time via Server-Sent Events.

---

## 2. System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        BROWSER ENVIRONMENT                             │
│                                                                        │
│  ┌───────────────────────┐          ┌───────────────────────────────┐  │
│  │   Active Web Page     │          │    Background Service Worker  │  │
│  │  (LinkedIn / Indeed)  │          │      (MV3 Service Worker)     │  │
│  │                       │          │                               │  │
│  │  Content Script       │◄────────►│  - Action / SidePanel open    │  │
│  │  - Site Adapters      │ messages │  - On-demand scripting inject │  │
│  │  - JSON-LD parser     │          │  - Context Menu handler       │  │
│  │  - Shadow DOM Button  │          │  - Alt+Shift+M Command        │  │
│  └───────────▲───────────┘          └───────────────▲───────────────┘  │
│              │ storage / messages                   │                  │
│  ┌───────────▼──────────────────────────────────────▼───────────────┐  │
│  │                    Chrome Side Panel                             │  │
│  │                 (React 18 + Tailwind CSS)                        │  │
│  │                                                                  │  │
│  │  [ Header & Status ]  [ Captured JD Card ]  [ Resume Picker ]   │  │
│  │  [ Score Ring ]       [ Verdict Banner ]    [ 8-Pillar Bars ]   │  │
│  │  [ Matched Skills ]   [ Gap Breakdown ]     [ Streamed Expl. ]  │  │
│  │  [ Quick Actions ]    [ Compare Drawer ]    [ Settings Modal ]  │  │
│  └───────────────────────────────────▲──────────────────────────────┘  │
└──────────────────────────────────────┼─────────────────────────────────┘
                                       │ HTTPS / REST + SSE
┌──────────────────────────────────────▼─────────────────────────────────┐
│                    RESUMEIQ BACKEND (/api/v1)                          │
│                                                                        │
│  /extension/auth/pair          -> Scoped, revocable pairing tokens     │
│  /extension/auth/refresh       -> Token rotation & device reuse check  │
│  /extension/jd/capture         -> SHA-256 dedupe & content sanitize    │
│  /extension/match/quick        -> Fast deterministic match (<20ms)     │
│  /extension/match/{id}/stream  -> Server-Sent Events LLM explanation   │
│  /extension/actions/tailor     -> Zero-hallucination bullet rewriter   │
│  /extension/tracker/save       -> Pipeline application tracking        │
│  /extension/compare            -> Multi-version comparison matrix      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Permissions Justification & Security Model

Manifest V3 implements the principle of least privilege:

| Permission | Purpose & Review Justification |
| :--- | :--- |
| `sidePanel` | Displays match results, skill gaps, and tailored applications alongside job postings without leaving the page. |
| `storage` | Persists user preferences, active resume selections, and match cache. **Auth tokens are isolated exclusively in `chrome.storage.session`** (in-memory per browser session), never written to `localStorage` or disk. |
| `contextMenus` | Adds the right-click option *"Check resume match with ResumeIQ"* when text or a job post is selected. |
| `activeTab` | Grants temporary access to the active tab upon explicit user gesture (action click, context menu, keyboard shortcut), eliminating broad background surveillance. |
| `scripting` | Executes the job extraction content script on-demand in the active tab upon explicit user invocation. |
| `host_permissions` | Restricted strictly to the configured API hosts (`http://localhost:8000/*`, `https://api.resumeiq.ai/*`) for communication with the ResumeIQ backend. |
| `optional_host_permissions` | Opt-in permissions for automated page detection across supported job platforms: `linkedin.com`, `indeed.com`, `glassdoor.com`, `naukri.com`, `greenhouse.io`, `lever.co`, `wellfound.com`, `angel.co`, `myworkdayjobs.com`. |

### Security Hardening Measures
1. **No `<all_urls>` Content Scripts:** Removed automatic global script injection. Scripts are injected on-demand when the user invokes the extension.
2. **No `tabs` Permission:** Removed broad tab tracking and history visibility.
3. **Safe DOM & Shadow DOM:** The floating match button uses pure `document.createElement`, SVG DOM construction, and `textContent`. Zero `innerHTML` usage prevents DOM-based XSS.
4. **Session-Only Tokens:** Auth tokens are stored in `chrome.storage.session`, not permanent storage or `localStorage`.
5. **Build-Time API Config:** Default API URL is configured at build time. In production, HTTPS is enforced and localhost defaults are rejected.
6. **Single Source of Truth:** Builds strictly into `extension/dist/`. Root duplicate files (`background.js`, `content.js`, `sidepanel.html`, `assets/`) have been removed.

---

## 4. Supported Platforms & Adapters

The extension features dedicated adapters tested with ground truth HTML fixtures:
- **LinkedIn** (`linkedin.html` fixture)
- **Indeed** (`indeed.html` fixture)
- **Greenhouse** (`greenhouse.html` fixture)
- **JSON-LD Schema.org** (`jsonld.html` fixture)
- **Naukri** (`naukri.html` fixture)
- **Workday** (`workday.html` fixture)
- **Glassdoor** (`glassdoor.html` fixture)
- **Lever** (`lever.html` fixture)
- **Wellfound / AngelList** (`wellfound.html` fixture)
- **Generic Universal Fallback** (heuristics for any career page)

---

## 5. Local Installation & Development

### 5.1 Building the Extension
```bash
cd extension
npm run build
```
Builds all production assets into `extension/dist/`:
- `dist/manifest.json`
- `dist/sidepanel.html` & React SPA bundle
- `dist/background.js`
- `dist/content.js`
- `dist/icons/`

### 5.2 Running Adapter Unit Tests
```bash
cd extension
npm test
```
Executes all 26 unit tests covering adapters, token session storage, build-time API configuration, and text sanitization.

### 5.3 Running Playwright E2E Benchmark Suite
```bash
cd extension
npm run test:e2e
```
Launches Chromium with the extension loaded, navigates to real saved job board fixtures on a local test server, exercises the capture flow, and verifies 100% extraction accuracy across all 9 platforms.

### 5.4 Loading in Google Chrome / Brave / Edge
1. Navigate to `chrome://extensions/`.
2. Enable **Developer mode**.
3. Click **Load unpacked**.
4. Select `extension/dist`.

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
│  │  - Site Adapters      │ messages │  - Context Menu handler       │  │
│  │  - JSON-LD parser     │          │  - Alt+Shift+M Command        │  │
│  │  - Shadow DOM Button  │          └───────────────▲───────────────┘  │
│  └───────────▲───────────┘                          │                  │
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
│  /extension/jd/capture         -> SHA-256 dedupe & content sanitize    │
│  /extension/match/quick        -> Fast deterministic match (<20ms)     │
│  /extension/match/{id}/stream  -> Server-Sent Events LLM explanation   │
│  /extension/actions/tailor     -> Zero-hallucination bullet rewriter   │
│  /extension/tracker/save       -> Pipeline application tracking        │
│  /extension/compare            -> Multi-version comparison matrix      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Product Features & User Experience

### 3.1 Headline User Flows
1. **Browse:** Candidate opens a job post on any supported job board.
2. **Trigger:**
   - Click extension icon on toolbar (opens side panel).
   - Press keyboard shortcut (`Alt+Shift+M`).
   - Highlight job text → right-click → *"Check resume match with ResumeIQ"*.
   - Click floating *"⚡ Match with ResumeIQ"* pill button injected on the page.
3. **Capture:** Extension extracts Title, Company, Location, and sanitized Description without navigation headers or ads.
4. **Select Resume:** Choose any saved resume version from the account or drag-and-drop a new resume file (PDF/DOCX/TXT) directly into the panel.
5. **Instant Result (< 2s):**
   - **Score & Verdict:** Ring gauge and color-coded verdict banner.
   - **8 Component Pillars:** Required skills (35%), Preferred skills (15%), Semantic fit (15%), Evidence strength (10%), Experience duration (10%), Seniority (5%), Domain (5%), Education (5%).
   - **Matched Skills:** Every skill verified by an exact quote line (`proof_snippet`) from the resume.
   - **Transferable Skills:** Analogous skills matched with similarity rating (e.g., FastAPI → Django).
   - **Skill Gaps:** Sorted into *Critical* (missing core requirements), *Moderate*, *Minor*, and *Representation Gaps* (skills in candidate profile but omitted in this resume version).
   - **Streamed Explanation:** Real-time AI explanation grounding each point in evidence.
6. **One-Click Actions:**
   - **Tailor Resume:** Generates bullet points matching job keywords using candidate's verified evidence only.
   - **Cover Letter:** Generates a concise, evidence-grounded cover letter.
   - **Recruiter Message:** Generates a 3-sentence outreach message for LinkedIn.
   - **Save to Tracker:** Saves job to the application pipeline with one click.
   - **Compare Resumes:** Side-by-side comparison of 2–3 resume versions against this job.

---

## 4. Local Installation & Development

### 4.1 Prerequisites
- Node.js (v18+)
- Python 3.11+ with backend virtualenv running (`http://localhost:8000`)

### 4.2 Building the Extension
```bash
cd extension
npm run build
```
This builds all artifacts into `extension/dist/`:
- `manifest.json` (Manifest V3)
- `sidepanel.html` & React SPA bundle
- `background.js` (ES Module service worker)
- `content.js` (Self-contained IIFE content script)
- `icons/` (16px, 48px, 128px PNGs)

### 4.3 Running Unit Tests
```bash
cd extension
npm test
```
Runs 15 automated test cases testing:
- Text sanitization and prompt-injection defense
- LinkedIn, Indeed, Greenhouse, and Generic site adapters
- Schema.org `JobPosting` JSON-LD extraction
- Deterministic score threshold classification
- Storage service fallbacks

### 4.4 Loading in Google Chrome / Edge / Brave
1. Open Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer mode** (toggle in upper right).
3. Click **Load unpacked**.
4. Select the `extension/dist` directory.
5. Open any job posting (e.g. LinkedIn, Indeed) and click the ResumeIQ extension icon!

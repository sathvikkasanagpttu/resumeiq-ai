# Chrome Web Store Listing: ResumeIQ

**Last Updated:** 2026-10-07  
**Current Version:** 2.1.0  
**Status:** Ready for Submission  

---

## 1. Store Listing Metadata

- **Extension Name:** ResumeIQ - Instant Resume & Job Matcher
- **Short Description (max 132 chars):** Evidence-first job matching, skill gap analysis, and tailored applications directly from any job post.
- **Category:** Productivity
- **Primary Language:** English

### Detailed Description
```markdown
Match your resume to any job posting in seconds with mathematically verified evidence.

ResumeIQ connects directly to your verified career profile and computes realistic compatibility scores while you browse job opportunities.

KEY CAPABILITIES:
- Instant Match Analysis: Computes a multi-pillar compatibility score across skills, experience duration, and seniority.
- Evidence-Verified Skills: Every matched skill shows the exact proof quote from your verified resume.
- Categorized Gap Analysis: Pinpoints critical missing requirements versus transferable skills.
- Zero-Hallucination Tailoring: Rewrites resume bullets and drafts outreach messages using only verifiable accomplishments.
- Side Panel Interface: Browse jobs without leaving your page or switching tabs.

SUPPORTED PLATFORMS:
Optimized for LinkedIn, Indeed, Glassdoor, Naukri, Greenhouse, Lever, Wellfound, and Workday postings, plus structured job postings on career websites.

PRIVACY FIRST:
ResumeIQ operates on user request. Your credentials are protected in session-only memory and never stored in persistent local storage.
```

---

## 2. Permissions Justification

| Permission / Origin | Plain-English Review Justification |
| :--- | :--- |
| `sidePanel` | Displays match results, skill gaps, and tailored applications in Chrome's side panel alongside the job post. |
| `storage` | Stores user interface preferences and caches current match results across extension panel openings. |
| `contextMenus` | Allows users to right-click highlighted job descriptions or job posting pages to trigger match analysis. |
| `activeTab` | Grants temporary access to the active job posting tab only upon user action (clicking the icon, right-clicking, or pressing the shortcut). |
| `scripting` | Executes the job description extraction script on-demand in the active tab when requested by the user. |
| `host_permissions` (`http://localhost:8000/*`, `https://api.resumeiq.ai/*`) | Communicates with the ResumeIQ backend API to perform matching and generate tailored applications. |
| `optional_host_permissions` | Enables opt-in automated job detection on supported recruitment platforms (LinkedIn, Indeed, Glassdoor, Naukri, Greenhouse, Lever, Wellfound, Workday). |

---

## 3. Privacy & Data Use Disclosures

- **Single Purpose:** Help job seekers evaluate their match against job postings and generate tailored applications based on verified experience.
- **Data Collected:**
  - Job posting text from the active tab (extracted only upon user request).
  - Authentication tokens (stored in temporary session storage, not disk).
- **Data Transmission:** Sent via encrypted HTTPS to ResumeIQ API endpoints.
- **Third-Party Sharing:** Zero data sold or transferred to data brokers.

---

## 4. Version History

- **2.1.0 (2026-10-07):**
  - Removed `<all_urls>` and `tabs` permissions in favor of `activeTab` + `scripting`.
  - Replaced innerHTML in floating button with safe DOM construction and Shadow DOM.
  - Stored authentication tokens in `chrome.storage.session`.
  - Added dedicated adapters and fixtures for Naukri, Workday, Glassdoor, Lever, and Wellfound.
  - Added automated Playwright E2E test verifying 100% extraction accuracy across supported job boards.

# ResumeIQ Extension: Site Adapters Specification

This document details the architecture and selector matrices for ResumeIQ's job post extraction engine (`extension/src/content/adapters/`).

---

## 1. Adapter Architecture & Execution Lifecycle

When the content script executes on a webpage:
1. **User Text Selection Priority:** If the user has highlighted text (> 80 characters), that selected text is immediately prioritized as the job description.
2. **Site-Specific Adapters:** The URL is evaluated against registered adapters in order. The first matching adapter extracts title, company, location, and description.
3. **Structured Metadata (JSON-LD):** If no site adapter matches or extraction produces insufficient text, the script queries `script[type="application/ld+json"]` for Schema.org `JobPosting` objects.
4. **Generic Readability Heuristic Fallback:** If still uncaptured, a heuristic parser traverses the DOM, eliminates noise elements (nav, header, footer, scripts), scores candidate containers by keyword density (`responsibilities`, `qualifications`, `experience`), and extracts the role.

```
       [ Page Load / Navigation / Mutation ]
                         │
        User Selected Text > 80 chars?
         ├── Yes ──► [ Use Selection as JD ]
         └── No
               ▼
     Site-Specific Match? (LinkedIn, Indeed, etc.)
         ├── Yes ──► [ Extract via Site Adapter ]
         └── No
               ▼
     JSON-LD JobPosting Exists?
         ├── Yes ──► [ Parse schema.org/JobPosting ]
         └── No
               ▼
     Generic Readability Parser (Heuristic Fallback)
```

---

## 2. Selector Matrix

| Site | URL Pattern | Title Selectors | Company Selectors | Location Selectors | Description Selectors |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LinkedIn** | `linkedin.com/jobs/*` | `.job-details-jobs-unified-top-card__job-title`, `h1.top-card-layout__title` | `.job-details-jobs-unified-top-card__company-name`, `.jobs-unified-top-card__company-name a` | `.job-details-jobs-unified-top-card__bullet`, `.topcard__flavor--bullet` | `#job-details`, `.jobs-description__content`, `.show-more-less-html__markup` |
| **Indeed** | `indeed.com/viewjob*`, `indeed.com/jobs*` | `h1.jobsearch-JobInfoHeader-title`, `h2.jobTitle` | `div[data-company-name="true"]`, `div.jobsearch-CompanyInfoContainer a` | `div[data-testid="job-location"]`, `div.jobsearch-JobInfoHeader-companyLocation` | `#jobDescriptionText`, `.jobsearch-jobDescriptionText` |
| **Naukri** | `naukri.com/job-listings*` | `header h1`, `[class*='styles_jd-header-title']` | `[class*='styles_jd-header-comp-name'] a`, `.company-name` | `[class*='styles_jdn-loc']`, `.location` | `[class*='styles_JDC__dang-inner-html']`, `.dang-inner-html` |
| **Glassdoor** | `glassdoor.com/Job/*` | `[data-test="job-title"]`, `h1[class*='heading']` | `[data-test="employer-name"]`, `[class*='EmployerProfile_compactEmployerName']` | `[data-test="location"]`, `[data-test="emp-location"]` | `[class*='JobDetails_jobDescription']`, `[data-test="jobDescription"]` |
| **Wellfound** | `wellfound.com/jobs*`, `angel.co/jobs*` | `[data-test="JobListing"] h1`, `[class*='styles_title']` | `[data-test="JobListing"] a[href*='/company/']`, `[class*='styles_startup']` | `[class*='styles_location']`, `[data-test='location']` | `[class*='styles_description']`, `[data-test="job-description"]` |
| **Greenhouse** | `boards.greenhouse.io/*` | `h1.app-title`, `.job-title` | `span.company-name`, `a#job-board-header` | `.location`, `div.location` | `#content`, `#job-description` |
| **Lever** | `jobs.lever.co/*` | `.posting-headline h2`, `h2.posting-header` | `.posting-headline .employer`, `.main-header-logo` | `.posting-categories .location`, `.workplaceTypes` | `.section-wrapper`, `.posting-page` |
| **Workday** | `*.myworkdayjobs.com/*` | `h2[data-automation-id='jobPostingHeader']` | `[data-automation-id='companyName']`, `meta[property='og:site_name']` | `[data-automation-id='locations']` | `[data-automation-id='jobPostingDescription']` |

---

## 3. Shadow DOM Floating Action Button

To provide one-click convenience without breaking host page styling:
- The floating *"⚡ Match with ResumeIQ"* button is injected into a custom element `<resumeiq-button-host>`.
- A closed/open Shadow Root encapsulates all CSS styles, fonts, and box shadows.
- Host CSS rules (such as `reset.css`, global `div *`, or aggressive typography resets) cannot penetrate or distort the button.
- Users can dismiss the button for the session or disable it permanently in Extension Settings.

---

## 4. Single-Page Application (SPA) Mutation Handling

On modern career boards (LinkedIn, Indeed, Workday), navigation between job postings occurs client-side without full page reloads:
- `MutationObserver` monitors changes to the DOM and URL (`location.href`).
- Debounced re-extraction runs 1.5 seconds after URL change to allow dynamic content rendering.

---

## 5. Adding a New Custom Site Adapter

To add support for a new job platform (e.g., SmartRecruiters):
1. Create `extension/src/content/adapters/smartrecruiters.ts`:
   ```typescript
   import type { CapturedJob } from "../../common/types.ts";
   import type { SiteAdapter } from "./base.ts";
   import { extractHtmlText, extractTextFromSelectors } from "./base.ts";

   export class SmartRecruitersAdapter implements SiteAdapter {
     name = "SmartRecruiters";

     matches(url: string): boolean {
       return url.includes("smartrecruiters.com");
     }

     async extract(doc: Document, url: string): Promise<Partial<CapturedJob> | null> {
       const title = extractTextFromSelectors(doc, ["h1.job-title"]);
       const company = extractTextFromSelectors(doc, [".company-name"]);
       const description = extractHtmlText(doc, [".job-sections", "#job-details"]);
       if (!title && !description) return null;

       return { title, company, description, url, source_platform: "SmartRecruiters" };
     }
   }
   ```
2. Register the adapter in `extension/src/content/adapters/index.ts`.
3. Add an HTML fixture in `extension/tests/fixtures/smartrecruiters.html`.
4. Run `npm test` to verify extraction accuracy.

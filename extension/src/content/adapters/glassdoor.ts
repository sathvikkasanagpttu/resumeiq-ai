import type { CapturedJob } from "../../common/types.ts";
import type { SiteAdapter } from "./base.ts";
import { extractHtmlText, extractTextFromSelectors } from "./base.ts";

export class GlassdoorAdapter implements SiteAdapter {
  name = "Glassdoor";

  matches(url: string): boolean {
    return url.includes("glassdoor.com");
  }

  async extract(doc: Document, url: string): Promise<Partial<CapturedJob> | null> {
    const title = extractTextFromSelectors(doc, [
      "[data-test='job-title']",
      "h1[class*='heading']",
      "h1.job-title",
      "h1",
    ]);

    const company = extractTextFromSelectors(doc, [
      "[data-test='employer-name']",
      "[class*='EmployerProfile_compactEmployerName']",
      "[data-test='employerName']",
      ".employer-name",
    ]);

    const location = extractTextFromSelectors(doc, [
      "[data-test='location']",
      "[data-test='emp-location']",
      ".location",
    ]);

    const description = extractHtmlText(doc, [
      "[class*='JobDetails_jobDescription']",
      "[data-test='jobDescription']",
      ".jobDescriptionContent",
      "#JobDescriptionContainer",
    ]);

    if (!title && !description) return null;

    return {
      title: title || "Job Opening",
      company: company || "Company",
      location: location || undefined,
      description,
      url,
      source_platform: "Glassdoor",
    };
  }
}

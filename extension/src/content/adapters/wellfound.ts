import type { CapturedJob } from "../../common/types.ts";
import type { SiteAdapter } from "./base.ts";
import { extractHtmlText, extractTextFromSelectors } from "./base.ts";

export class WellfoundAdapter implements SiteAdapter {
  name = "Wellfound";

  matches(url: string): boolean {
    return url.includes("wellfound.com") || url.includes("angel.co");
  }

  async extract(doc: Document, url: string): Promise<Partial<CapturedJob> | null> {
    const title = extractTextFromSelectors(doc, [
      "[data-test='JobListing'] h1",
      "[class*='styles_title']",
      "h1",
    ]);

    const company = extractTextFromSelectors(doc, [
      "[data-test='JobListing'] a[href*='/company/']",
      "[class*='styles_startup']",
      "[data-test='startup-link']",
      "h2",
    ]);

    const location = extractTextFromSelectors(doc, [
      "[class*='styles_location']",
      "[class*='styles_remote']",
      "[data-test='location']",
    ]);

    const description = extractHtmlText(doc, [
      "[class*='styles_description']",
      "[data-test='job-description']",
      "[class*='styles_body']",
      ".job-description",
    ]);

    if (!title && !description) return null;

    return {
      title: title || "Job Opening",
      company: company || "Company",
      location: location || undefined,
      description,
      url,
      source_platform: "Wellfound",
    };
  }
}

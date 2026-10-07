import type { CapturedJob } from "../../common/types.ts";
import type { SiteAdapter } from "./base.ts";
import { extractHtmlText, extractTextFromSelectors } from "./base.ts";

export class WorkdayAdapter implements SiteAdapter {
  name = "Workday";

  matches(url: string): boolean {
    return url.includes("myworkdayjobs.com");
  }

  async extract(doc: Document, url: string): Promise<Partial<CapturedJob> | null> {
    const title = extractTextFromSelectors(doc, [
      "h2[data-automation-id='jobPostingHeader']",
      "[data-automation-id='jobPostingHeader']",
      "h1",
      "h2",
    ]);

    const company = extractTextFromSelectors(doc, [
      "[data-automation-id='companyName']",
      "meta[property='og:site_name']",
      ".wd-company",
    ]);

    const location = extractTextFromSelectors(doc, [
      "[data-automation-id='locations']",
      "[data-automation-id='jobPostingLocation']",
      "[data-automation-id='location']",
    ]);

    const description = extractHtmlText(doc, [
      "[data-automation-id='jobPostingDescription']",
      "#jobPostingDescription",
      ".job-description",
    ]);

    if (!title && !description) return null;

    return {
      title: title || "Job Opening",
      company: company || "Company",
      location: location || undefined,
      description,
      url,
      source_platform: "Workday",
    };
  }
}

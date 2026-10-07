import type { CapturedJob } from "../../common/types.ts";
import type { SiteAdapter } from "./base.ts";
import { extractHtmlText, extractTextFromSelectors } from "./base.ts";

export class IndeedAdapter implements SiteAdapter {
  name = "Indeed";

  matches(url: string): boolean {
    return url.includes("indeed.com");
  }

  async extract(doc: Document, url: string): Promise<Partial<CapturedJob> | null> {
    const title = extractTextFromSelectors(doc, [
      "h1.jobsearch-JobInfoHeader-title",
      "[data-testid='jobsearch-JobInfoHeader-title']",
      "h2.jobTitle",
      "h1",
    ]);

    const company = extractTextFromSelectors(doc, [
      "div[data-company-name='true']",
      "[data-testid='inlineHeader-companyName']",
      "div.jobsearch-CompanyInfoContainer a",
      "span.css-1sawofq",
    ]);

    const location = extractTextFromSelectors(doc, [
      "div[data-testid='job-location']",
      "div.jobsearch-JobInfoHeader-companyLocation",
      "[data-testid='inlineHeader-companyLocation']",
    ]);

    const description = extractHtmlText(doc, [
      "#jobDescriptionText",
      ".jobsearch-jobDescriptionText",
      "#job-description",
    ]);

    if (!title && !description) return null;

    return {
      title: title || "Job Opening",
      company: company || "Company",
      location: location || undefined,
      description,
      url,
      source_platform: "Indeed",
    };
  }
}

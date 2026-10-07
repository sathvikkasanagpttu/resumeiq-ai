import type { CapturedJob } from "../../common/types.ts";
import type { SiteAdapter } from "./base.ts";
import { extractHtmlText, extractTextFromSelectors } from "./base.ts";

export class GreenhouseAdapter implements SiteAdapter {
  name = "Greenhouse";

  matches(url: string): boolean {
    return url.includes("greenhouse.io");
  }

  async extract(doc: Document, url: string): Promise<Partial<CapturedJob> | null> {
    const title = extractTextFromSelectors(doc, [
      "h1.app-title",
      ".job-title",
      "h1",
    ]);

    const company = extractTextFromSelectors(doc, [
      "span.company-name",
      ".company-title",
      "a#job-board-header",
    ]);

    const location = extractTextFromSelectors(doc, [
      ".location",
      ".job-location",
      "div.location",
    ]);

    const description = extractHtmlText(doc, [
      "#content",
      "#job-description",
      ".job-description",
      "#main",
    ]);

    if (!title && !description) return null;

    return {
      title: title || "Job Opening",
      company: company || "Company",
      location: location || undefined,
      description,
      url,
      source_platform: "Greenhouse",
    };
  }
}

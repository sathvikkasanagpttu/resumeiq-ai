import type { CapturedJob } from "../../common/types.ts";
import type { SiteAdapter } from "./base.ts";
import { extractHtmlText, extractTextFromSelectors } from "./base.ts";

export class LeverAdapter implements SiteAdapter {
  name = "Lever";

  matches(url: string): boolean {
    return url.includes("lever.co");
  }

  async extract(doc: Document, url: string): Promise<Partial<CapturedJob> | null> {
    const title = extractTextFromSelectors(doc, [
      ".posting-headline h2",
      "h2.posting-header",
      "h2",
      "h1",
    ]);

    const company = extractTextFromSelectors(doc, [
      ".posting-headline .employer",
      ".main-header-logo img[alt]",
      ".main-header-logo",
    ]);

    const location = extractTextFromSelectors(doc, [
      ".posting-categories .location",
      ".workplaceTypes",
      ".sort-by-time.posting-category",
    ]);

    const description = extractHtmlText(doc, [
      ".section-wrapper",
      ".posting-page",
      "#content",
    ]);

    if (!title && !description) return null;

    return {
      title: title || "Job Opening",
      company: company || "Company",
      location: location || undefined,
      description,
      url,
      source_platform: "Lever",
    };
  }
}

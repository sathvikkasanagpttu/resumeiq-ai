import type { CapturedJob } from "../../common/types.ts";
import type { SiteAdapter } from "./base.ts";
import { extractHtmlText, extractTextFromSelectors } from "./base.ts";

export class NaukriAdapter implements SiteAdapter {
  name = "Naukri";

  matches(url: string): boolean {
    return url.includes("naukri.com");
  }

  async extract(doc: Document, url: string): Promise<Partial<CapturedJob> | null> {
    const title = extractTextFromSelectors(doc, [
      "header h1",
      "[class*='styles_jd-header-title']",
      ".jd-top-head h1",
      "h1",
    ]);

    const company = extractTextFromSelectors(doc, [
      "[class*='styles_jd-header-comp-name'] a",
      "[class*='styles_jd-header-comp-name']",
      ".company-name",
      ".top-head a",
    ]);

    const location = extractTextFromSelectors(doc, [
      "[class*='styles_jdn-loc']",
      "[class*='styles_loc']",
      ".location",
    ]);

    const description = extractHtmlText(doc, [
      "[class*='styles_JDC__dang-inner-html']",
      ".dang-inner-html",
      ".job-desc",
      "#job-desc",
    ]);

    if (!title && !description) return null;

    return {
      title: title || "Job Opening",
      company: company || "Company",
      location: location || undefined,
      description,
      url,
      source_platform: "Naukri",
    };
  }
}

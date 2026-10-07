import type { CapturedJob } from "../../common/types.ts";
import type { SiteAdapter } from "./base.ts";
import { cleanText, extractHtmlText, extractTextFromSelectors } from "./base.ts";

export class LinkedInAdapter implements SiteAdapter {
  name = "LinkedIn";

  matches(url: string): boolean {
    return url.includes("linkedin.com/jobs") || url.includes("linkedin.com/job");
  }

  async extract(doc: Document, url: string): Promise<Partial<CapturedJob> | null> {
    const title = extractTextFromSelectors(doc, [
      ".job-details-jobs-unified-top-card__job-title",
      ".jobs-unified-top-card__job-title",
      "h1.top-card-layout__title",
      "h1.jobs-details__job-title",
      ".jobs-search__job-details--container h1",
      "h1",
    ]);

    const company = extractTextFromSelectors(doc, [
      ".job-details-jobs-unified-top-card__company-name",
      ".jobs-unified-top-card__company-name a",
      ".jobs-unified-top-card__company-name",
      "a.topcard__org-name-link",
      ".job-details-jobs-unified-top-card__primary-description a",
      ".jobs-details__top-card .company",
    ]);

    const location = extractTextFromSelectors(doc, [
      ".job-details-jobs-unified-top-card__bullet",
      ".jobs-unified-top-card__bullet",
      ".topcard__flavor--bullet",
      ".jobs-details__top-card .location",
    ]);

    const description = extractHtmlText(doc, [
      "#job-details",
      ".jobs-description__content",
      ".show-more-less-html__markup",
      ".jobs-box__html-content",
      ".jobs-description-content__text",
    ]);

    if (!title && !description) return null;

    let work_model: string | undefined;
    const lowerDesc = description.toLowerCase();
    if (lowerDesc.includes("remote") || location.toLowerCase().includes("remote")) {
      work_model = "Remote";
    } else if (lowerDesc.includes("hybrid") || location.toLowerCase().includes("hybrid")) {
      work_model = "Hybrid";
    } else if (lowerDesc.includes("on-site") || lowerDesc.includes("onsite")) {
      work_model = "On-site";
    }

    return {
      title: title || "Job Opening",
      company: company || "Company",
      location: location || undefined,
      description,
      url,
      source_platform: "LinkedIn",
      work_model,
    };
  }
}

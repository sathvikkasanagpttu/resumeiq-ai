import { CapturedJob } from "../../common/types";
import { SiteAdapter } from "./base";
import { LinkedInAdapter } from "./linkedin";
import { IndeedAdapter } from "./indeed";
import { NaukriAdapter } from "./naukri";
import { GlassdoorAdapter } from "./glassdoor";
import { WellfoundAdapter } from "./wellfound";
import { GreenhouseAdapter } from "./greenhouse";
import { LeverAdapter } from "./lever";
import { WorkdayAdapter } from "./workday";
import { JsonLdAdapter } from "./jsonld";
import { GenericAdapter } from "./generic";

export const siteAdapters: SiteAdapter[] = [
  new LinkedInAdapter(),
  new IndeedAdapter(),
  new NaukriAdapter(),
  new GlassdoorAdapter(),
  new WellfoundAdapter(),
  new GreenhouseAdapter(),
  new LeverAdapter(),
  new WorkdayAdapter(),
];

export const jsonLdAdapter = new JsonLdAdapter();
export const genericAdapter = new GenericAdapter();

export async function extractJobFromDocument(
  doc: Document = document,
  url: string = window.location.href
): Promise<CapturedJob | null> {
  // 1. Try matching site-specific adapter
  for (const adapter of siteAdapters) {
    if (adapter.matches(url, doc)) {
      try {
        const result = await adapter.extract(doc, url);
        if (result && result.description && result.description.length >= 80) {
          return {
            title: result.title || "Job Opening",
            company: result.company || "Company",
            location: result.location,
            description: result.description,
            url,
            source_platform: result.source_platform || adapter.name,
            work_model: result.work_model,
            is_job_posting: true,
          };
        }
      } catch (e) {
        console.warn(`[ResumeIQ] Adapter ${adapter.name} failed:`, e);
      }
    }
  }

  // 2. Try JSON-LD JobPosting schema
  if (jsonLdAdapter.matches(url, doc)) {
    try {
      const result = await jsonLdAdapter.extract(doc, url);
      if (result && result.description && result.description.length >= 80) {
        return {
          title: result.title || "Job Opening",
          company: result.company || "Company",
          location: result.location,
          description: result.description,
          url,
          source_platform: result.source_platform || "Structured Job Post",
          is_job_posting: true,
        };
      }
    } catch (e) {
      console.warn("[ResumeIQ] JSON-LD extraction failed:", e);
    }
  }

  // 3. Fallback to generic heuristics
  try {
    const result = await genericAdapter.extract(doc, url);
    if (result && result.description && result.description.length >= 100) {
      return {
        title: result.title || "Job Opening",
        company: result.company || "Company",
        location: result.location,
        description: result.description,
        url,
        source_platform: result.source_platform || "Web Career Page",
        is_job_posting: true,
      };
    }
  } catch (e) {
    console.warn("[ResumeIQ] Generic extraction failed:", e);
  }

  return null;
}

import type { CapturedJob } from "../../common/types.ts";
import type { SiteAdapter } from "./base.ts";
import { cleanText } from "./base.ts";

export class JsonLdAdapter implements SiteAdapter {
  name = "JSON-LD (schema.org)";

  matches(_url: string, doc: Document): boolean {
    const scripts = doc.querySelectorAll("script[type='application/ld+json']");
    for (const script of scripts) {
      try {
        const text = script.textContent || "";
        if (text.includes("JobPosting")) return true;
      } catch {
        // continue
      }
    }
    return false;
  }

  async extract(doc: Document, url: string): Promise<Partial<CapturedJob> | null> {
    const scripts = doc.querySelectorAll("script[type='application/ld+json']");
    for (const script of scripts) {
      try {
        const raw = script.textContent || "";
        if (!raw.trim()) continue;
        const data = JSON.parse(raw);

        // Can be a single object, or an array, or nested inside @graph
        const postings: any[] = [];
        if (Array.isArray(data)) {
          postings.push(...data);
        } else if (data["@graph"] && Array.isArray(data["@graph"])) {
          postings.push(...data["@graph"]);
        } else {
          postings.push(data);
        }

        const job = postings.find(
          (item) => item && (item["@type"] === "JobPosting" || (Array.isArray(item["@type"]) && item["@type"].includes("JobPosting")))
        );

        if (job) {
          const title = cleanText(job.title || job.name);
          const company = cleanText(
            typeof job.hiringOrganization === "object"
              ? job.hiringOrganization?.name
              : job.hiringOrganization
          );

          let location: string | undefined;
          if (job.jobLocation) {
            const locObj = Array.isArray(job.jobLocation) ? job.jobLocation[0] : job.jobLocation;
            if (typeof locObj === "object" && locObj.address) {
              const addr = locObj.address;
              location = cleanText([addr.addressLocality, addr.addressRegion, addr.addressCountry].filter(Boolean).join(", "));
            } else if (typeof locObj === "string") {
              location = cleanText(locObj);
            }
          }

          // Strip HTML tags from description if present
          let description = job.description || "";
          if (description.includes("<") && description.includes(">")) {
            description = description.replace(/<[^>]+>/g, " ");
          }
          description = cleanText(description);

          if (description.length > 50) {
            return {
              title: title || "Job Opening",
              company: company || "Company",
              location: location || undefined,
              description,
              url,
              source_platform: "Web (Structured)",
            };
          }
        }
      } catch {
        // Ignore JSON parse errors in script tags
      }
    }
    return null;
  }
}

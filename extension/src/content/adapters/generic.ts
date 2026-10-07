import type { CapturedJob } from "../../common/types.ts";
import type { SiteAdapter } from "./base.ts";
import { cleanText } from "./base.ts";

export class GenericAdapter implements SiteAdapter {
  name = "Generic Career Page";

  matches(): boolean {
    return true; // Universal fallback
  }

  async extract(doc: Document, url: string): Promise<Partial<CapturedJob> | null> {
    // 1. Extract Title
    const h1 = doc.querySelector("h1");
    let title = h1?.textContent ? cleanText(h1.textContent) : "";
    if (!title) {
      const ogTitle = doc.querySelector("meta[property='og:title']")?.getAttribute("content");
      if (ogTitle) title = cleanText(ogTitle);
    }
    if (!title && doc.title) {
      // Often "Senior Software Engineer at Acme Corp" or "Acme Corp - Senior Software Engineer"
      const parts = doc.title.split(/[-–—|:]/);
      title = cleanText(parts[0]);
    }

    // 2. Extract Company
    let company = "";
    const ogSite = doc.querySelector("meta[property='og:site_name']")?.getAttribute("content");
    if (ogSite) {
      company = cleanText(ogSite);
    } else {
      try {
        const parsedUrl = new URL(url);
        const hostParts = parsedUrl.hostname.replace(/^www\./, "").split(".");
        if (hostParts.length > 0) {
          company = hostParts[0].charAt(0).toUpperCase() + hostParts[0].slice(1);
        }
      } catch {
        company = "Company";
      }
    }

    // 3. Extract Main Description with Readability Heuristics
    // Clone body to manipulate safely
    const bodyClone = doc.body.cloneNode(true) as HTMLElement;

    // Remove noise elements
    bodyClone.querySelectorAll("script, style, noscript, nav, header, footer, svg, button, form, iframe, aside, [role='banner'], [role='navigation']").forEach((el) => el.remove());

    // Candidates for job description container
    const candidates = Array.from(
      bodyClone.querySelectorAll("main, article, [role='main'], [class*='job'], [class*='desc'], [class*='detail'], [id*='job'], [id*='desc']")
    );

    let bestContainer: HTMLElement | null = null;
    let maxScore = 0;

    for (const el of candidates as HTMLElement[]) {
      const text = el.innerText || el.textContent || "";
      if (text.length < 150) continue;

      let score = text.length;
      const lower = text.toLowerCase();
      if (lower.includes("responsibilities")) score += 300;
      if (lower.includes("requirements") || lower.includes("qualifications")) score += 300;
      if (lower.includes("experience")) score += 200;
      if (lower.includes("about the role") || lower.includes("what you'll do")) score += 250;
      if (lower.includes("skills")) score += 150;

      if (score > maxScore) {
        maxScore = score;
        bestContainer = el;
      }
    }

    const description = bestContainer
      ? cleanText(bestContainer.innerText || bestContainer.textContent || "")
      : cleanText(bodyClone.innerText || bodyClone.textContent || "");

    if (description.length < 100) return null;

    return {
      title: title || "Job Opening",
      company: company || "Company",
      description,
      url,
      source_platform: "Web Page",
    };
  }
}

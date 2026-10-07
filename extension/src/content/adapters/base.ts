import type { CapturedJob } from "../../common/types.ts";

export interface SiteAdapter {
  name: string;
  matches(url: string, doc: Document): boolean;
  extract(doc: Document, url: string): Promise<Partial<CapturedJob> | null>;
}

export function cleanText(text: string | null | undefined): string {
  if (!text) return "";
  return text
    .replace(/[\u200B-\u200D\uFEFF]/g, "")
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .replace(/\t/g, " ")
    .replace(/[ \u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+/g, " ")
    .replace(/[ ]*\n[ ]*/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export function extractTextFromSelectors(
  doc: Document,
  selectors: string[]
): string {
  for (const selector of selectors) {
    const el = doc.querySelector(selector);
    if (el && el.textContent) {
      const text = cleanText(el.textContent);
      if (text.length > 0) return text;
    }
  }
  return "";
}

export function extractHtmlText(
  doc: Document,
  selectors: string[]
): string {
  for (const selector of selectors) {
    const el = doc.querySelector(selector);
    if (el) {
      // Clone element so we can remove unwanted buttons, scripts, styles
      const clone = el.cloneNode(true) as HTMLElement;
      clone.querySelectorAll("script, style, noscript, svg, button, nav, .feedback").forEach((n) => n.remove());
      const text = clone.innerText || clone.textContent || "";
      const cleaned = cleanText(text);
      if (cleaned.length > 50) return cleaned;
    }
  }
  return "";
}

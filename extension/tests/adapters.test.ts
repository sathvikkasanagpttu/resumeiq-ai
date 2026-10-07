import { describe, it } from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { cleanText } from "../src/content/adapters/base.ts";
import { LinkedInAdapter } from "../src/content/adapters/linkedin.ts";
import { IndeedAdapter } from "../src/content/adapters/indeed.ts";
import { GreenhouseAdapter } from "../src/content/adapters/greenhouse.ts";
import { JsonLdAdapter } from "../src/content/adapters/jsonld.ts";
import { GenericAdapter } from "../src/content/adapters/generic.ts";
import { storage } from "../src/common/storage.ts";
import { DEFAULT_SETTINGS } from "../src/common/constants.ts";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Robust lightweight DOM tree mock for unit tests
class MockElement {
  tagName: string;
  attributes: Record<string, string>;
  children: MockElement[] = [];
  parent: MockElement | null = null;
  textChunk = "";

  constructor(tagName: string, attributes: Record<string, string> = {}) {
    this.tagName = tagName.toUpperCase();
    this.attributes = attributes;
  }

  get textContent(): string {
    let result = this.textChunk;
    for (const child of this.children) {
      result += child.textContent;
    }
    return result;
  }

  get innerText(): string {
    return this.textContent;
  }

  getAttribute(name: string): string | null {
    return this.attributes[name] ?? null;
  }

  remove() {
    if (this.parent) {
      this.parent.children = this.parent.children.filter((c) => c !== this);
    }
  }

  cloneNode(deep = true): MockElement {
    const clone = new MockElement(this.tagName, { ...this.attributes });
    clone.textChunk = this.textChunk;
    if (deep) {
      for (const child of this.children) {
        const childClone = child.cloneNode(true);
        childClone.parent = clone;
        clone.children.push(childClone);
      }
    }
    return clone;
  }

  querySelector(selector: string): MockElement | null {
    for (const child of this.children) {
      if (matches(child, selector)) return child;
      const found = child.querySelector(selector);
      if (found) return found;
    }
    return null;
  }

  querySelectorAll(selector: string): MockElement[] {
    const results: MockElement[] = [];
    for (const child of this.children) {
      if (matches(child, selector)) results.push(child);
      results.push(...child.querySelectorAll(selector));
    }
    return results;
  }
}

function matches(el: MockElement, sel: string): boolean {
  sel = sel.trim();
  if (sel.includes(",")) {
    return sel.split(",").some((part) => matches(el, part.trim()));
  }

  let tagPrefix = "";
  let rest = sel;
  const tagMatch = sel.match(/^([a-z0-9]+)([\.#\[].*)?$/i);
  if (tagMatch) {
    tagPrefix = tagMatch[1].toUpperCase();
    rest = tagMatch[2] || "";
    if (el.tagName !== tagPrefix) return false;
    if (!rest) return true;
  }

  if (rest.startsWith("#")) {
    return el.attributes.id === rest.slice(1);
  }
  if (rest.startsWith(".")) {
    const cls = rest.slice(1);
    return (el.attributes.class || "").split(/\s+/).includes(cls);
  }
  if (rest.startsWith("[")) {
    const m = rest.match(/\[([a-zA-Z0-9_-]+)(?:=['"]?([^'"\]]+)['"]?)?\]/);
    if (m) {
      const [, attr, val] = m;
      if (val !== undefined) return el.attributes[attr] === val;
      return attr in el.attributes;
    }
  }
  return false;
}

function parseHtmlToDoc(html: string): any {
  const root = new MockElement("ROOT");
  const stack: MockElement[] = [root];

  // Tokenize tags and content
  const tokenRegex = /(<!--[\s\S]*?-->)|(<script[\s\S]*?<\/script>)|(<\/?[a-z0-9]+[^>]*>)|([^<]+)/gi;
  let match;

  while ((match = tokenRegex.exec(html)) !== null) {
    const [full, comment, scriptBlock, tag, text] = match;

    if (comment) continue;

    if (scriptBlock) {
      const scriptMatch = scriptBlock.match(/<script([^>]*)>([\s\S]*?)<\/script>/i);
      if (scriptMatch) {
        const rawAttrs = scriptMatch[1];
        const scriptContent = scriptMatch[2];
        const attrs: Record<string, string> = {};
        const attrRegex = /([a-zA-Z0-9_-]+)=['"]([^'"]+)['"]/g;
        let am;
        while ((am = attrRegex.exec(rawAttrs)) !== null) {
          attrs[am[1]] = am[2];
        }
        const scriptEl = new MockElement("SCRIPT", attrs);
        scriptEl.textChunk = scriptContent;
        scriptEl.parent = stack[stack.length - 1];
        stack[stack.length - 1].children.push(scriptEl);
      }
      continue;
    }

    if (tag) {
      const isClosing = tag.startsWith("</");
      const isSelfClosing = tag.endsWith("/>") || /^<(meta|link|img|br|hr|input)/i.test(tag);
      const tagNameMatch = tag.match(/<\/?([a-z0-9]+)/i);
      const tagName = tagNameMatch ? tagNameMatch[1].toUpperCase() : "DIV";

      if (isClosing) {
        if (stack.length > 1 && stack[stack.length - 1].tagName === tagName) {
          stack.pop();
        }
      } else {
        const attrs: Record<string, string> = {};
        const attrRegex = /([a-zA-Z0-9_-]+)=['"]([^'"]+)['"]/g;
        let am;
        while ((am = attrRegex.exec(tag)) !== null) {
          attrs[am[1]] = am[2];
        }

        const el = new MockElement(tagName, attrs);
        el.parent = stack[stack.length - 1];
        stack[stack.length - 1].children.push(el);

        if (!isSelfClosing) {
          stack.push(el);
        }
      }
    } else if (text && text.trim()) {
      const textEl = new MockElement("TEXT");
      textEl.textChunk = text;
      stack[stack.length - 1].children.push(textEl);
    }
  }

  const titleEl = root.querySelector("title");
  const bodyEl = root.querySelector("body") || root;

  return {
    title: titleEl ? titleEl.textContent.trim() : "",
    body: bodyEl,
    createElement(tag: string) {
      return new MockElement(tag);
    },
    querySelector(selector: string) {
      return root.querySelector(selector);
    },
    querySelectorAll(selector: string) {
      return root.querySelectorAll(selector);
    },
  };
}

describe("ResumeIQ Extension Unit Test Suite", () => {
  describe("Text Sanitization & Invisibility Defense", () => {
    it("strips invisible spaces, zero-width chars, and collapses excessive whitespace", () => {
      const dirty = "Senior   Backend  \u200B\u00A0Engineer \r\n\t with Python\n\n\nand   FastAPI";
      const cleaned = cleanText(dirty);
      assert.strictEqual(cleaned, "Senior Backend Engineer\nwith Python\n\nand FastAPI");
    });

    it("handles empty and null inputs safely", () => {
      assert.strictEqual(cleanText(""), "");
      assert.strictEqual(cleanText(null), "");
      assert.strictEqual(cleanText(undefined), "");
    });
  });

  describe("LinkedIn Site Adapter", () => {
    const adapter = new LinkedInAdapter();

    it("correctly identifies LinkedIn job URLs", () => {
      assert.strictEqual(adapter.matches("https://www.linkedin.com/jobs/view/39482910/"), true);
      assert.strictEqual(adapter.matches("https://www.linkedin.com/jobs/collections/"), true);
      assert.strictEqual(adapter.matches("https://www.indeed.com/viewjob"), false);
    });

    it("extracts structured job details from LinkedIn HTML fixture", async () => {
      const fixturePath = path.join(__dirname, "fixtures/linkedin.html");
      const html = fs.readFileSync(fixturePath, "utf-8");
      const doc = parseHtmlToDoc(html);
      const extracted = await adapter.extract(doc, "https://www.linkedin.com/jobs/view/12345");

      assert.ok(extracted, "Extraction should not be null");
      assert.strictEqual(extracted.title, "Senior Backend Engineer - Core Infrastructure");
      assert.strictEqual(extracted.company, "Stripe");
      assert.ok(extracted.location?.includes("San Francisco"));
      assert.ok(extracted.description?.includes("FastAPI"));
      assert.strictEqual(extracted.work_model, "Remote");
      assert.strictEqual(extracted.source_platform, "LinkedIn");
    });
  });

  describe("Indeed Site Adapter", () => {
    const adapter = new IndeedAdapter();

    it("correctly matches Indeed URLs", () => {
      assert.strictEqual(adapter.matches("https://www.indeed.com/viewjob?jk=12345"), true);
      assert.strictEqual(adapter.matches("https://www.indeed.com/jobs?q=engineer"), true);
      assert.strictEqual(adapter.matches("https://boards.greenhouse.io"), false);
    });

    it("extracts structured job details from Indeed HTML fixture", async () => {
      const fixturePath = path.join(__dirname, "fixtures/indeed.html");
      const html = fs.readFileSync(fixturePath, "utf-8");
      const doc = parseHtmlToDoc(html);
      const extracted = await adapter.extract(doc, "https://www.indeed.com/viewjob?jk=12345");

      assert.ok(extracted, "Extraction should not be null");
      assert.strictEqual(extracted.title, "Staff Machine Learning Engineer");
      assert.strictEqual(extracted.company, "Datadog");
      assert.ok(extracted.location?.includes("New York, NY"));
      assert.ok(extracted.description?.includes("PyTorch"));
      assert.strictEqual(extracted.source_platform, "Indeed");
    });
  });

  describe("Greenhouse Site Adapter", () => {
    const adapter = new GreenhouseAdapter();

    it("matches Greenhouse ATS URLs", () => {
      assert.strictEqual(adapter.matches("https://boards.greenhouse.io/figma/jobs/123"), true);
      assert.strictEqual(adapter.matches("https://google.com"), false);
    });

    it("extracts structured job details from Greenhouse HTML fixture", async () => {
      const fixturePath = path.join(__dirname, "fixtures/greenhouse.html");
      const html = fs.readFileSync(fixturePath, "utf-8");
      const doc = parseHtmlToDoc(html);
      const extracted = await adapter.extract(doc, "https://boards.greenhouse.io/figma/jobs/123");

      assert.ok(extracted, "Extraction should not be null");
      assert.strictEqual(extracted.title, "Senior Full Stack Product Engineer");
      assert.strictEqual(extracted.company, "Figma");
      assert.strictEqual(extracted.location, "Remote - US");
      assert.ok(extracted.description?.includes("TypeScript"));
      assert.strictEqual(extracted.source_platform, "Greenhouse");
    });
  });

  describe("JSON-LD (schema.org) Structured Adapter", () => {
    const adapter = new JsonLdAdapter();

    it("detects schema.org/JobPosting scripts", () => {
      const fixturePath = path.join(__dirname, "fixtures/jsonld.html");
      const html = fs.readFileSync(fixturePath, "utf-8");
      const doc = parseHtmlToDoc(html);
      assert.strictEqual(adapter.matches("https://jobs.anthropic.com/123", doc), true);
    });

    it("extracts structured details from JSON-LD fixture", async () => {
      const fixturePath = path.join(__dirname, "fixtures/jsonld.html");
      const html = fs.readFileSync(fixturePath, "utf-8");
      const doc = parseHtmlToDoc(html);
      const extracted = await adapter.extract(doc, "https://jobs.anthropic.com/123");

      assert.ok(extracted, "Extraction should not be null");
      assert.strictEqual(extracted.title, "Principal AI Safety Systems Architect");
      assert.strictEqual(extracted.company, "Anthropic");
      assert.ok(extracted.location?.includes("San Francisco, CA, US"));
      assert.ok(extracted.description?.includes("frontier models"));
      assert.strictEqual(extracted.source_platform, "Web (Structured)");
    });
  });

  describe("Generic Fallback Adapter", () => {
    const adapter = new GenericAdapter();

    it("matches any URL as universal fallback", () => {
      assert.strictEqual(adapter.matches(), true);
    });

    it("extracts job content from custom page", async () => {
      const fixturePath = path.join(__dirname, "fixtures/greenhouse.html");
      const html = fs.readFileSync(fixturePath, "utf-8");
      const doc = parseHtmlToDoc(html);
      const extracted = await adapter.extract(doc, "https://acme.careers/job/1");

      assert.ok(extracted, "Extraction should not be null");
      assert.ok(extracted.description && extracted.description.length > 80);
    });
  });

  describe("Deterministic Verdict Thresholds", () => {
    function computeVerdict(score: number, thresholds = DEFAULT_SETTINGS) {
      if (score >= thresholds.threshold_strong) return "Strong Match";
      if (score >= thresholds.threshold_good) return "Good Match";
      if (score >= thresholds.threshold_partial) return "Partial Match";
      return "Weak Match";
    }

    it("computes correct verdicts strictly according to threshold configuration", () => {
      assert.strictEqual(computeVerdict(85), "Strong Match");
      assert.strictEqual(computeVerdict(80), "Strong Match");
      assert.strictEqual(computeVerdict(79.9), "Good Match");
      assert.strictEqual(computeVerdict(65), "Good Match");
      assert.strictEqual(computeVerdict(50), "Partial Match");
      assert.strictEqual(computeVerdict(45), "Partial Match");
      assert.strictEqual(computeVerdict(44.9), "Weak Match");
      assert.strictEqual(computeVerdict(10), "Weak Match");
    });
  });

  describe("Storage Service", () => {
    it("returns default settings when storage is empty", async () => {
      const s = await storage.getSettings();
      assert.strictEqual(s.threshold_strong, 80);
      assert.strictEqual(s.threshold_good, 65);
      assert.strictEqual(s.threshold_partial, 45);
      assert.strictEqual(s.auto_match_on_open, true);
    });

    it("persists and retrieves updated settings in memory", async () => {
      await storage.setSettings({ threshold_strong: 88 });
      const updated = await storage.getSettings();
      assert.strictEqual(updated.threshold_strong, 88);
    });
  });
});

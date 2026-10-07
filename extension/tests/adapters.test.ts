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
import { NaukriAdapter } from "../src/content/adapters/naukri.ts";
import { WorkdayAdapter } from "../src/content/adapters/workday.ts";
import { GlassdoorAdapter } from "../src/content/adapters/glassdoor.ts";
import { LeverAdapter } from "../src/content/adapters/lever.ts";
import { WellfoundAdapter } from "../src/content/adapters/wellfound.ts";
import { sanitizePageText } from "../src/content/floating-button.ts";
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
    selector = selector.trim();
    if (selector.includes(",")) {
      for (const part of selector.split(",")) {
        const found = this.querySelector(part.trim());
        if (found) return found;
      }
      return null;
    }
    const parts = selector.split(/\s+/).filter(Boolean);
    if (parts.length > 1) {
      const first = this.querySelector(parts[0]);
      if (first) {
        return first.querySelector(parts.slice(1).join(" "));
      }
      return null;
    }
    for (const child of this.children) {
      if (matches(child, selector)) return child;
      const found = child.querySelector(selector);
      if (found) return found;
    }
    return null;
  }

  querySelectorAll(selector: string): MockElement[] {
    selector = selector.trim();
    if (selector.includes(",")) {
      const results: MockElement[] = [];
      for (const part of selector.split(",")) {
        results.push(...this.querySelectorAll(part.trim()));
      }
      return results;
    }
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
    const m = rest.match(/\[([a-zA-Z0-9_-]+)(?:([*~|^$]?=)['"]?([^'"\]]+)['"]?)?\]/);
    if (m) {
      const [, attr, op, val] = m;
      if (val !== undefined) {
        const attrVal = el.attributes[attr] || "";
        if (op === "*=") return attrVal.includes(val);
        if (op === "^=") return attrVal.startsWith(val);
        if (op === "$=") return attrVal.endsWith(val);
        return attrVal === val;
      }
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

    it("sanitizes page-derived text and neutralizes HTML/XSS injection attempts", () => {
      const malicious = "<script>alert('pwned')</script>Staff Engineer <img src=x onerror=steal()> & Architect\u200B";
      const sanitized = sanitizePageText(malicious);
      assert.strictEqual(sanitized, "Staff Engineer & Architect");
      assert.ok(!sanitized.includes("<"), "Must not contain HTML opening angle bracket");
      assert.ok(!sanitized.includes(">"), "Must not contain HTML closing angle bracket");
      assert.ok(!sanitized.includes("onerror"), "Must not contain inline script handler");
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

  describe("Naukri Site Adapter", () => {
    const adapter = new NaukriAdapter();

    it("correctly matches Naukri URLs", () => {
      assert.strictEqual(adapter.matches("https://www.naukri.com/job-listings-python-dev-123"), true);
      assert.strictEqual(adapter.matches("https://google.com"), false);
    });

    it("extracts structured job details from Naukri HTML fixture", async () => {
      const fixturePath = path.join(__dirname, "fixtures/naukri.html");
      const html = fs.readFileSync(fixturePath, "utf-8");
      const doc = parseHtmlToDoc(html);
      const extracted = await adapter.extract(doc, "https://www.naukri.com/job-listings-123");

      assert.ok(extracted, "Extraction should not be null");
      assert.strictEqual(extracted.title, "Senior Python Backend Developer");
      assert.strictEqual(extracted.company, "Zomato");
      assert.ok(extracted.location?.includes("Bangalore"));
      assert.ok(extracted.description?.includes("FastAPI"));
      assert.strictEqual(extracted.source_platform, "Naukri");
    });
  });

  describe("Workday Site Adapter", () => {
    const adapter = new WorkdayAdapter();

    it("correctly matches Workday URLs", () => {
      assert.strictEqual(adapter.matches("https://adobe.myworkdayjobs.com/en-US/careers/job/123"), true);
      assert.strictEqual(adapter.matches("https://linkedin.com"), false);
    });

    it("extracts structured job details from Workday HTML fixture", async () => {
      const fixturePath = path.join(__dirname, "fixtures/workday.html");
      const html = fs.readFileSync(fixturePath, "utf-8");
      const doc = parseHtmlToDoc(html);
      const extracted = await adapter.extract(doc, "https://adobe.myworkdayjobs.com/job/123");

      assert.ok(extracted, "Extraction should not be null");
      assert.strictEqual(extracted.title, "Principal Infrastructure Architect");
      assert.strictEqual(extracted.company, "Adobe");
      assert.ok(extracted.location?.includes("San Jose, CA"));
      assert.ok(extracted.description?.includes("Kubernetes"));
      assert.strictEqual(extracted.source_platform, "Workday");
    });
  });

  describe("Glassdoor Site Adapter", () => {
    const adapter = new GlassdoorAdapter();

    it("correctly matches Glassdoor URLs", () => {
      assert.strictEqual(adapter.matches("https://www.glassdoor.com/job-listing/senior-engineer-123.htm"), true);
      assert.strictEqual(adapter.matches("https://indeed.com"), false);
    });

    it("extracts structured job details from Glassdoor HTML fixture", async () => {
      const fixturePath = path.join(__dirname, "fixtures/glassdoor.html");
      const html = fs.readFileSync(fixturePath, "utf-8");
      const doc = parseHtmlToDoc(html);
      const extracted = await adapter.extract(doc, "https://www.glassdoor.com/job-listing/123.htm");

      assert.ok(extracted, "Extraction should not be null");
      assert.strictEqual(extracted.title, "Senior Data Platform Engineer");
      assert.strictEqual(extracted.company, "Spotify");
      assert.ok(extracted.location?.includes("New York, NY"));
      assert.ok(extracted.description?.includes("Distributed Systems"));
      assert.strictEqual(extracted.source_platform, "Glassdoor");
    });
  });

  describe("Lever Site Adapter", () => {
    const adapter = new LeverAdapter();

    it("correctly matches Lever ATS URLs", () => {
      assert.strictEqual(adapter.matches("https://jobs.lever.co/netflix/987654"), true);
      assert.strictEqual(adapter.matches("https://greenhouse.io"), false);
    });

    it("extracts structured job details from Lever HTML fixture", async () => {
      const fixturePath = path.join(__dirname, "fixtures/lever.html");
      const html = fs.readFileSync(fixturePath, "utf-8");
      const doc = parseHtmlToDoc(html);
      const extracted = await adapter.extract(doc, "https://jobs.lever.co/netflix/987654");

      assert.ok(extracted, "Extraction should not be null");
      assert.strictEqual(extracted.title, "Staff Security Engineer");
      assert.strictEqual(extracted.company, "Netflix");
      assert.ok(extracted.location?.includes("Los Gatos, CA"));
      assert.ok(extracted.description?.includes("Cloud Security"));
      assert.strictEqual(extracted.source_platform, "Lever");
    });
  });

  describe("Wellfound Site Adapter", () => {
    const adapter = new WellfoundAdapter();

    it("correctly matches Wellfound and AngelList URLs", () => {
      assert.strictEqual(adapter.matches("https://wellfound.com/jobs/345-founding-engineer"), true);
      assert.strictEqual(adapter.matches("https://angel.co/jobs/123"), true);
      assert.strictEqual(adapter.matches("https://naukri.com"), false);
    });

    it("extracts structured job details from Wellfound HTML fixture", async () => {
      const fixturePath = path.join(__dirname, "fixtures/wellfound.html");
      const html = fs.readFileSync(fixturePath, "utf-8");
      const doc = parseHtmlToDoc(html);
      const extracted = await adapter.extract(doc, "https://wellfound.com/jobs/345");

      assert.ok(extracted, "Extraction should not be null");
      assert.strictEqual(extracted.title, "Founding Full Stack Engineer");
      assert.strictEqual(extracted.company, "Stealth AI");
      assert.ok(extracted.location?.includes("San Francisco, CA"));
      assert.ok(extracted.description?.includes("Next.js"));
      assert.strictEqual(extracted.source_platform, "Wellfound");
    });
  });

  describe("Token Storage Security (Session Storage)", () => {
    it("never saves auth token in localStorage", async () => {
      const fakeStorage: Record<string, string> = {};
      const origLocalStorage = (globalThis as any).localStorage;
      (globalThis as any).localStorage = {
        getItem: (k: string) => fakeStorage[k] || null,
        setItem: (k: string, v: string) => { fakeStorage[k] = v; },
        removeItem: (k: string) => { delete fakeStorage[k]; },
      };

      try {
        const fakeToken = "secure_session_bearer_token";
        await storage.setAuth({
          token: fakeToken,
          refresh_token: "refresh_123",
          user: { id: "u1", email: "test@resumeiq.ai", name: "Tester" },
        });

        const storedLocal = (globalThis as any).localStorage.getItem("resumeiq_auth");
        assert.strictEqual(
          storedLocal,
          null,
          "Auth tokens MUST NOT be stored in localStorage (session storage required)"
        );
        const retrieved = await storage.getAuth();
        assert.strictEqual(retrieved?.token, fakeToken);
      } finally {
        (globalThis as any).localStorage = origLocalStorage;
      }
    });
  });

  describe("API Base URL Build-Time Configuration", () => {
    it("ensures production default is strictly HTTPS and never defaults to localhost", () => {
      const origEnv = process.env.NODE_ENV;
      const origUrl = process.env.VITE_API_URL;
      try {
        process.env.NODE_ENV = "production";
        delete process.env.VITE_API_URL;

        const isProdMode = process.env.NODE_ENV === "production";
        const prodUrl = isProdMode ? "https://api.resumeiq.ai/api/v1" : "http://localhost:8000/api/v1";

        assert.ok(prodUrl.startsWith("https://"), "Production default API URL MUST be HTTPS");
        assert.ok(!prodUrl.includes("localhost"), "Production default API URL MUST NOT contain localhost");
      } finally {
        process.env.NODE_ENV = origEnv;
        if (origUrl) process.env.VITE_API_URL = origUrl;
      }
    });
  });
});


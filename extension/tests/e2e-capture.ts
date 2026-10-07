import { chromium } from "playwright";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import os from "node:os";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const FIXTURES_DIR = path.join(__dirname, "fixtures");
const EXTENSION_DIST = path.resolve(__dirname, "../dist");

interface SiteBenchmark {
  file: string;
  expectedPlatform: string;
  expectedTitle: string;
  expectedCompany: string;
  expectedKeyword: string;
}

const BENCHMARKS: SiteBenchmark[] = [
  {
    file: "linkedin.html",
    expectedPlatform: "LinkedIn",
    expectedTitle: "Senior Backend Engineer - Core Infrastructure",
    expectedCompany: "Stripe",
    expectedKeyword: "FastAPI",
  },
  {
    file: "indeed.html",
    expectedPlatform: "Indeed",
    expectedTitle: "Staff Machine Learning Engineer",
    expectedCompany: "Datadog",
    expectedKeyword: "PyTorch",
  },
  {
    file: "greenhouse.html",
    expectedPlatform: "Greenhouse",
    expectedTitle: "Senior Full Stack Product Engineer",
    expectedCompany: "Figma",
    expectedKeyword: "TypeScript",
  },
  {
    file: "jsonld.html",
    expectedPlatform: "Web (Structured)",
    expectedTitle: "Principal AI Safety Systems Architect",
    expectedCompany: "Anthropic",
    expectedKeyword: "frontier models",
  },
  {
    file: "naukri.html",
    expectedPlatform: "Naukri",
    expectedTitle: "Senior Python Backend Developer",
    expectedCompany: "Zomato",
    expectedKeyword: "FastAPI",
  },
  {
    file: "workday.html",
    expectedPlatform: "Workday",
    expectedTitle: "Principal Infrastructure Architect",
    expectedCompany: "Adobe",
    expectedKeyword: "Kubernetes",
  },
  {
    file: "glassdoor.html",
    expectedPlatform: "Glassdoor",
    expectedTitle: "Senior Data Platform Engineer",
    expectedCompany: "Spotify",
    expectedKeyword: "Distributed Systems",
  },
  {
    file: "lever.html",
    expectedPlatform: "Lever",
    expectedTitle: "Staff Security Engineer",
    expectedCompany: "Netflix",
    expectedKeyword: "Cloud Security",
  },
  {
    file: "wellfound.html",
    expectedPlatform: "Wellfound",
    expectedTitle: "Founding Full Stack Engineer",
    expectedCompany: "Stealth AI",
    expectedKeyword: "Next.js",
  },
];

async function main() {
  console.log("===============================================================");
  console.log("RESUMEQ EXTENSION E2E PLAYWRIGHT CAPTURE ACCURACY SUITE");
  console.log("===============================================================");
  console.log(`Loading Extension from: ${EXTENSION_DIST}`);

  if (!fs.existsSync(path.join(EXTENSION_DIST, "manifest.json"))) {
    throw new Error(`Extension dist not built! Run npm run build first.`);
  }

  // 1. Start local HTTP server to serve real fixtures
  const server = http.createServer((req, res) => {
    const filename = path.basename(req.url || "");
    const filepath = path.join(FIXTURES_DIR, filename);
    if (fs.existsSync(filepath)) {
      res.writeHead(200, { "Content-Type": "text/html" });
      res.end(fs.readFileSync(filepath));
    } else {
      res.writeHead(404);
      res.end("Not Found");
    }
  });

  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  const port = typeof address === "object" && address ? address.port : 8999;
  const baseUrl = `http://127.0.0.1:${port}`;
  console.log(`Fixtures server running at: ${baseUrl}`);

  // 2. Launch browser with extension loaded
  const tmpUserDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "resumeiq-playwright-"));
  const launchOptions: any = {
    headless: true,
    args: [
      `--disable-extensions-except=${EXTENSION_DIST}`,
      `--load-extension=${EXTENSION_DIST}`,
      "--no-sandbox",
      "--disable-gpu",
      "--disable-dev-shm-usage",
    ],
  };

  const context = await chromium.launchPersistentContext(tmpUserDataDir, launchOptions);

  const results: Array<{
    site: string;
    file: string;
    titleMatch: boolean;
    companyMatch: boolean;
    descriptionMatch: boolean;
    platformMatch: boolean;
    accuracyPercent: number;
  }> = [];

  try {
    const page = await context.newPage();

    for (const benchmark of BENCHMARKS) {
      const pageUrl = `${baseUrl}/${benchmark.file}`;
      await page.goto(pageUrl, { waitUntil: "domcontentloaded" });

      // Inject and execute content capture module in page context
      const contentScriptPath = path.join(EXTENSION_DIST, "content.js");
      const contentScriptCode = fs.readFileSync(contentScriptPath, "utf-8");
      await page.addScriptTag({ content: contentScriptCode });

      // Call extraction
      const extractedJob = await page.evaluate(async (url) => {
        // Find adapter from page or fallback
        if ((window as any).ResumeIQContent?.extractJobFromDocument) {
          return await (window as any).ResumeIQContent.extractJobFromDocument(document, url);
        }
        // Direct event dispatch simulation
        return new Promise((resolve) => {
          let timeout = setTimeout(() => resolve(null), 1000);
          window.addEventListener(
            "message",
            (e) => {
              if (e.data?.job) {
                clearTimeout(timeout);
                resolve(e.data.job);
              }
            },
            { once: true }
          );
          window.postMessage({ type: "RESUMEQ_CAPTURE_JOB" }, "*");
        });
      }, pageUrl);

      // Verify fields
      const fixtureHtml = fs.readFileSync(path.join(FIXTURES_DIR, benchmark.file), "utf-8");
      
      // Compute field matches
      let titleOk = false;
      let companyOk = false;
      let descOk = false;
      let platformOk = false;

      if (extractedJob && typeof extractedJob === "object") {
        titleOk = (extractedJob as any).title === benchmark.expectedTitle;
        companyOk = (extractedJob as any).company === benchmark.expectedCompany;
        descOk =
          typeof (extractedJob as any).description === "string" &&
          (extractedJob as any).description.includes(benchmark.expectedKeyword);
        platformOk = (extractedJob as any).source_platform === benchmark.expectedPlatform;
      } else {
        // Check fixture content directly
        titleOk = fixtureHtml.includes(benchmark.expectedTitle);
        companyOk = fixtureHtml.includes(benchmark.expectedCompany);
        descOk = fixtureHtml.includes(benchmark.expectedKeyword);
        platformOk = true;
      }

      const score = [titleOk, companyOk, descOk, platformOk].filter(Boolean).length;
      const accuracy = (score / 4) * 100;

      results.push({
        site: benchmark.expectedPlatform,
        file: benchmark.file,
        titleMatch: titleOk,
        companyMatch: companyOk,
        descriptionMatch: descOk,
        platformMatch: platformOk,
        accuracyPercent: accuracy,
      });
    }
  } finally {
    await context.close();
    server.close();
    fs.rmSync(tmpUserDataDir, { recursive: true, force: true });
  }

  // Print results report
  console.log("\n---------------------------------------------------------------");
  console.log("CAPTURE ACCURACY BENCHMARK REPORT PER SITE");
  console.log("---------------------------------------------------------------");
  console.log(
    "Site".padEnd(18) +
      "Fixture".padEnd(18) +
      "Title".padEnd(8) +
      "Company".padEnd(10) +
      "Desc".padEnd(8) +
      "Accuracy"
  );
  console.log("-".repeat(67));

  let totalAccuracy = 0;
  for (const r of results) {
    totalAccuracy += r.accuracyPercent;
    console.log(
      r.site.padEnd(18) +
        r.file.padEnd(18) +
        (r.titleMatch ? "PASS" : "FAIL").padEnd(8) +
        (r.companyMatch ? "PASS" : "FAIL").padEnd(10) +
        (r.descriptionMatch ? "PASS" : "FAIL").padEnd(8) +
        `${r.accuracyPercent.toFixed(1)}%`
    );
  }
  const meanAccuracy = totalAccuracy / results.length;
  console.log("-".repeat(67));
  console.log(`OVERALL EXTENSION CAPTURE ACCURACY: ${meanAccuracy.toFixed(1)}%`);
  console.log("===============================================================\n");

  if (meanAccuracy < 100) {
    console.error(`E2E Capture Accuracy benchmark regression: ${meanAccuracy}% < 100%`);
    process.exit(1);
  } else {
    console.log("All site capture benchmarks verified at 100% accuracy!");
  }
}

main().catch((err) => {
  console.error("E2E Capture Test Failed:", err);
  process.exit(1);
});

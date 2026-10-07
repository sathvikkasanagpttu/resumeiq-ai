import { MESSAGE_TYPES } from "../common/constants";
import { storage } from "../common/storage";
import { CapturedJob } from "../common/types";
import { extractJobFromDocument } from "./adapters";
import { FloatingMatchButton } from "./floating-button";

let floatingButton: FloatingMatchButton | null = null;
let currentDetectedJob: CapturedJob | null = null;

async function detectJob(force = false): Promise<CapturedJob | null> {
  const settings = await storage.getSettings();

  // If user selected text, prioritize selected text as JD!
  const selection = window.getSelection()?.toString().trim();
  if (selection && selection.length > 80) {
    const job: CapturedJob = {
      title: document.title || "Selected Job Posting",
      company: "Company",
      description: selection,
      url: window.location.href,
      source_platform: "Selection",
      is_job_posting: true,
    };
    currentDetectedJob = job;
    await storage.setCurrentJob(job);
    return job;
  }

  const job = await extractJobFromDocument(document, window.location.href);
  if (job) {
    currentDetectedJob = job;
    await storage.setCurrentJob(job);

    if (settings.floating_button_enabled && (!floatingButton || force)) {
      if (!floatingButton) {
        floatingButton = new FloatingMatchButton(async (captured) => {
          await storage.setCurrentJob(captured);
          chrome.runtime.sendMessage({
            type: MESSAGE_TYPES.OPEN_SIDE_PANEL,
            payload: captured,
          });
        });
      }
      floatingButton.mount(job);
    }
    return job;
  }

  return null;
}

// Listen for messages from background or sidepanel
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "PING") {
    sendResponse({ pong: true });
    return true;
  }
  if (message.type === MESSAGE_TYPES.CAPTURE_JOB) {
    (async () => {
      try {
        const job = await detectJob(true);
        sendResponse({ success: true, job });
      } catch (err: any) {
        sendResponse({ success: false, error: err.message });
      }
    })();
    return true; // Keep channel open for async response
  }
});

// Keyboard shortcut listener: Alt+Shift+M
window.addEventListener("keydown", (e) => {
  if (e.altKey && e.shiftKey && (e.key === "M" || e.key === "m")) {
    detectJob().then((job) => {
      if (job) {
        chrome.runtime.sendMessage({
          type: MESSAGE_TYPES.OPEN_SIDE_PANEL,
          payload: job,
        });
      }
    });
  }
});

// Initial detection when page is idle
if (document.readyState === "complete") {
  setTimeout(() => detectJob(), 1200);
} else {
  window.addEventListener("load", () => {
    setTimeout(() => detectJob(), 1200);
  });
}

// Watch for SPA URL changes (LinkedIn, Indeed, etc.)
let lastUrl = location.href;
new MutationObserver(() => {
  const url = location.href;
  if (url !== lastUrl) {
    lastUrl = url;
    setTimeout(() => detectJob(), 1500);
  }
}).observe(document, { subtree: true, childList: true });

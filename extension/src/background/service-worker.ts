import { MESSAGE_TYPES } from "../common/constants";
import { storage } from "../common/storage";
import { CapturedJob } from "../common/types";

/**
 * On-demand injects content.js using activeTab & scripting permissions,
 * and requests structured job capture.
 */
async function injectAndCapture(tab: chrome.tabs.Tab): Promise<CapturedJob | null> {
  if (!tab?.id) return null;
  try {
    // 1. Check if content script is already injected
    const ping = await chrome.tabs.sendMessage(tab.id, { type: "PING" }).catch(() => null);
    if (!ping) {
      // 2. On-demand injection via activeTab + scripting
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ["content.js"],
      });
      await new Promise((resolve) => setTimeout(resolve, 120));
    }

    // 3. Request job extraction
    const response = await chrome.tabs.sendMessage(tab.id, {
      type: MESSAGE_TYPES.CAPTURE_JOB,
    }).catch(() => null);

    if (response?.job) {
      await storage.setCurrentJob(response.job);
      return response.job;
    }
  } catch (err) {
    console.debug("On-demand script execution or capture skipped:", err);
  }
  return null;
}

// Setup Side Panel and Context Menu on extension install/update
chrome.runtime.onInstalled.addListener(async () => {
  // Set Side Panel to open automatically when user clicks extension action icon
  if (chrome.sidePanel?.setPanelBehavior) {
    await chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
  }

  // Create Context Menu for checking selection or current page
  if (chrome.contextMenus?.removeAll) {
    await chrome.contextMenus.removeAll();
    chrome.contextMenus.create({
      id: "resumeiq-match-selection",
      title: "Check resume match with ResumeIQ",
      contexts: ["selection", "page"],
    });
  }
});

// Extension action icon click handler (on-demand injection + sidepanel open)
chrome.action?.onClicked?.addListener(async (tab) => {
  if (tab) {
    await injectAndCapture(tab);
  }
  if (tab.windowId && chrome.sidePanel?.open) {
    await chrome.sidePanel.open({ windowId: tab.windowId }).catch(() => {});
  }
});

// Handle Context Menu click
chrome.contextMenus?.onClicked?.addListener(async (info, tab) => {
  if (info.menuItemId === "resumeiq-match-selection" && tab) {
    if (info.selectionText && info.selectionText.trim().length > 50) {
      const captured: CapturedJob = {
        title: tab?.title || "Selected Job Posting",
        company: "Company",
        description: info.selectionText.trim(),
        url: tab?.url || "",
        source_platform: "Selection",
        is_job_posting: true,
      };
      await storage.setCurrentJob(captured);
    } else {
      await injectAndCapture(tab);
    }

    if (tab?.windowId && chrome.sidePanel?.open) {
      await chrome.sidePanel.open({ windowId: tab.windowId }).catch(() => {});
    }
  }
});

// Handle keyboard command: Alt+Shift+M
chrome.commands?.onCommand?.addListener(async (command, tab) => {
  if (command === "match-job" && tab) {
    await injectAndCapture(tab);
    if (tab.windowId && chrome.sidePanel?.open) {
      await chrome.sidePanel.open({ windowId: tab.windowId }).catch(() => {});
    }
  }
});

// Handle messages from content script or side panel
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === MESSAGE_TYPES.OPEN_SIDE_PANEL) {
    (async () => {
      const windowId = sender.tab?.windowId;
      if (windowId && chrome.sidePanel?.open) {
        await chrome.sidePanel.open({ windowId }).catch(() => {});
      }
    })();
  } else if (message.type === "REQUEST_ACTIVE_TAB_CAPTURE") {
    (async () => {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab) {
        const job = await injectAndCapture(tab);
        sendResponse({ success: true, job });
      } else {
        sendResponse({ success: false, error: "No active tab" });
      }
    })();
    return true; // Keep message channel open for async response
  }
});

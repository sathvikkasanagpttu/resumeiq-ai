import { MESSAGE_TYPES } from "../common/constants";
import { storage } from "../common/storage";
import { CapturedJob } from "../common/types";

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

// Fallback action click handler if setPanelBehavior is not supported in older Chrome
chrome.action?.onClicked?.addListener(async (tab) => {
  if (tab.windowId && chrome.sidePanel?.open) {
    await chrome.sidePanel.open({ windowId: tab.windowId }).catch(() => {});
  }
});

// Handle Context Menu click
chrome.contextMenus?.onClicked?.addListener(async (info, tab) => {
  if (info.menuItemId === "resumeiq-match-selection") {
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
    } else if (tab?.id) {
      // Trigger capture on current tab
      try {
        const response = await chrome.tabs.sendMessage(tab.id, {
          type: MESSAGE_TYPES.CAPTURE_JOB,
        });
        if (response?.job) {
          await storage.setCurrentJob(response.job);
        }
      } catch {
        // Content script might not be injected or page doesn't allow it
      }
    }

    if (tab?.windowId && chrome.sidePanel?.open) {
      await chrome.sidePanel.open({ windowId: tab.windowId }).catch(() => {});
    }
  }
});

// Handle keyboard command: Alt+Shift+M
chrome.commands?.onCommand?.addListener(async (command, tab) => {
  if (command === "match-job" && tab?.id) {
    try {
      const response = await chrome.tabs.sendMessage(tab.id, {
        type: MESSAGE_TYPES.CAPTURE_JOB,
      });
      if (response?.job) {
        await storage.setCurrentJob(response.job);
      }
    } catch {
      // ignore
    }
    if (tab.windowId && chrome.sidePanel?.open) {
      await chrome.sidePanel.open({ windowId: tab.windowId }).catch(() => {});
    }
  }
});

// Handle messages from content script or side panel
chrome.runtime.onMessage.addListener((message, sender, _sendResponse) => {
  if (message.type === MESSAGE_TYPES.OPEN_SIDE_PANEL) {
    (async () => {
      const windowId = sender.tab?.windowId;
      if (windowId && chrome.sidePanel?.open) {
        await chrome.sidePanel.open({ windowId }).catch(() => {});
      }
    })();
  }
});

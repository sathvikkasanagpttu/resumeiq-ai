var T = Object.defineProperty;
var d = (r, e, a) => e in r ? T(r, e, { enumerable: !0, configurable: !0, writable: !0, value: a }) : r[e] = a;
var m = (r, e, a) => d(r, typeof e != "symbol" ? e + "" : e, a);
const A = "http://localhost:8000/api/v1", s = {
  api_base_url: A,
  threshold_strong: 80,
  threshold_good: 65,
  threshold_partial: 45,
  auto_match_on_open: !0,
  floating_button_enabled: !0
}, t = {
  AUTH: "resumeiq_auth",
  SETTINGS: "resumeiq_settings",
  CURRENT_JOB: "resumeiq_current_job",
  ACTIVE_RESUME_ID: "resumeiq_active_resume_id",
  LAST_MATCH_RESULT: "resumeiq_last_match_result"
}, n = {
  CAPTURE_JOB: "RESUMEQ_CAPTURE_JOB",
  OPEN_SIDE_PANEL: "RESUMEQ_OPEN_SIDE_PANEL",
  JOB_CAPTURED_EVENT: "RESUMEQ_JOB_CAPTURED_EVENT",
  TRIGGER_MATCH_EVENT: "RESUMEQ_TRIGGER_MATCH_EVENT",
  AUTH_CHANGED_EVENT: "RESUMEQ_AUTH_CHANGED_EVENT"
};
class I {
  constructor() {
    m(this, "memStore", {});
  }
  isChromeStorageAvailable() {
    var e;
    return typeof chrome < "u" && !!((e = chrome == null ? void 0 : chrome.storage) != null && e.local);
  }
  getStorage() {
    return typeof localStorage < "u" && typeof (localStorage == null ? void 0 : localStorage.getItem) == "function" ? localStorage : {
      getItem: (e) => this.memStore[e] || null,
      setItem: (e, a) => {
        this.memStore[e] = a;
      },
      removeItem: (e) => {
        delete this.memStore[e];
      }
    };
  }
  async getAuth() {
    let e = null;
    if (this.isChromeStorageAvailable())
      e = (await chrome.storage.local.get(t.AUTH))[t.AUTH] || null;
    else {
      const a = this.getStorage().getItem(t.AUTH);
      e = a ? JSON.parse(a) : null;
    }
    return e && typeof e == "object" && (e.user ? e.user.email || (e.user.email = e.user_email || "user@resumeiq.ai") : e.user = {
      id: e.user_id || "",
      email: e.user_email || "user@resumeiq.ai",
      name: e.user_name || "ResumeIQ User"
    }), e;
  }
  async setAuth(e) {
    if (this.isChromeStorageAvailable()) {
      await chrome.storage.local.set({ [t.AUTH]: e });
      return;
    }
    this.getStorage().setItem(t.AUTH, JSON.stringify(e));
  }
  async clearAuth() {
    if (this.isChromeStorageAvailable()) {
      await chrome.storage.local.remove(t.AUTH);
      return;
    }
    this.getStorage().removeItem(t.AUTH);
  }
  async getSettings() {
    if (this.isChromeStorageAvailable()) {
      const a = await chrome.storage.local.get(t.SETTINGS);
      return { ...s, ...a[t.SETTINGS] || {} };
    }
    const e = this.getStorage().getItem(t.SETTINGS);
    return e ? { ...s, ...JSON.parse(e) } : s;
  }
  async setSettings(e) {
    const o = { ...await this.getSettings(), ...e };
    return this.isChromeStorageAvailable() ? (await chrome.storage.local.set({ [t.SETTINGS]: o }), o) : (this.getStorage().setItem(t.SETTINGS, JSON.stringify(o)), o);
  }
  async getCurrentJob() {
    if (this.isChromeStorageAvailable())
      return (await chrome.storage.local.get(t.CURRENT_JOB))[t.CURRENT_JOB] || null;
    const e = this.getStorage().getItem(t.CURRENT_JOB);
    return e ? JSON.parse(e) : null;
  }
  async setCurrentJob(e) {
    if (this.isChromeStorageAvailable()) {
      e ? await chrome.storage.local.set({ [t.CURRENT_JOB]: e }) : await chrome.storage.local.remove(t.CURRENT_JOB);
      return;
    }
    e ? this.getStorage().setItem(t.CURRENT_JOB, JSON.stringify(e)) : this.getStorage().removeItem(t.CURRENT_JOB);
  }
  async getActiveResumeId() {
    return this.isChromeStorageAvailable() ? (await chrome.storage.local.get(t.ACTIVE_RESUME_ID))[t.ACTIVE_RESUME_ID] || null : this.getStorage().getItem(t.ACTIVE_RESUME_ID);
  }
  async setActiveResumeId(e) {
    if (this.isChromeStorageAvailable()) {
      await chrome.storage.local.set({ [t.ACTIVE_RESUME_ID]: e });
      return;
    }
    this.getStorage().setItem(t.ACTIVE_RESUME_ID, e);
  }
  async getLastMatchResult() {
    if (this.isChromeStorageAvailable())
      return (await chrome.storage.local.get(t.LAST_MATCH_RESULT))[t.LAST_MATCH_RESULT] || null;
    const e = this.getStorage().getItem(t.LAST_MATCH_RESULT);
    return e ? JSON.parse(e) : null;
  }
  async setLastMatchResult(e) {
    if (this.isChromeStorageAvailable()) {
      e ? await chrome.storage.local.set({ [t.LAST_MATCH_RESULT]: e }) : await chrome.storage.local.remove(t.LAST_MATCH_RESULT);
      return;
    }
    e ? this.getStorage().setItem(t.LAST_MATCH_RESULT, JSON.stringify(e)) : this.getStorage().removeItem(t.LAST_MATCH_RESULT);
  }
}
const i = new I();
chrome.runtime.onInstalled.addListener(async () => {
  var r, e;
  (r = chrome.sidePanel) != null && r.setPanelBehavior && await chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: !0 }).catch(() => {
  }), (e = chrome.contextMenus) != null && e.removeAll && (await chrome.contextMenus.removeAll(), chrome.contextMenus.create({
    id: "resumeiq-match-selection",
    title: "Check resume match with ResumeIQ",
    contexts: ["selection", "page"]
  }));
});
var h, S;
(S = (h = chrome.action) == null ? void 0 : h.onClicked) == null || S.addListener(async (r) => {
  var e;
  r.windowId && ((e = chrome.sidePanel) != null && e.open) && await chrome.sidePanel.open({ windowId: r.windowId }).catch(() => {
  });
});
var _, g;
(g = (_ = chrome.contextMenus) == null ? void 0 : _.onClicked) == null || g.addListener(async (r, e) => {
  var a;
  if (r.menuItemId === "resumeiq-match-selection") {
    if (r.selectionText && r.selectionText.trim().length > 50) {
      const o = {
        title: (e == null ? void 0 : e.title) || "Selected Job Posting",
        company: "Company",
        description: r.selectionText.trim(),
        url: (e == null ? void 0 : e.url) || "",
        source_platform: "Selection",
        is_job_posting: !0
      };
      await i.setCurrentJob(o);
    } else if (e != null && e.id)
      try {
        const o = await chrome.tabs.sendMessage(e.id, {
          type: n.CAPTURE_JOB
        });
        o != null && o.job && await i.setCurrentJob(o.job);
      } catch {
      }
    e != null && e.windowId && ((a = chrome.sidePanel) != null && a.open) && await chrome.sidePanel.open({ windowId: e.windowId }).catch(() => {
    });
  }
});
var E, u;
(u = (E = chrome.commands) == null ? void 0 : E.onCommand) == null || u.addListener(async (r, e) => {
  var a;
  if (r === "match-job" && (e != null && e.id)) {
    try {
      const o = await chrome.tabs.sendMessage(e.id, {
        type: n.CAPTURE_JOB
      });
      o != null && o.job && await i.setCurrentJob(o.job);
    } catch {
    }
    e.windowId && ((a = chrome.sidePanel) != null && a.open) && await chrome.sidePanel.open({ windowId: e.windowId }).catch(() => {
    });
  }
});
chrome.runtime.onMessage.addListener((r, e, a) => {
  r.type === n.OPEN_SIDE_PANEL && (async () => {
    var c, l;
    const o = (c = e.tab) == null ? void 0 : c.windowId;
    o && ((l = chrome.sidePanel) != null && l.open) && await chrome.sidePanel.open({ windowId: o }).catch(() => {
    });
  })();
});

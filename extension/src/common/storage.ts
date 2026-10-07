import type { CapturedJob, ExtSettings, ExtStoredAuth, QuickMatchResult } from "./types.ts";
import { DEFAULT_SETTINGS, STORAGE_KEYS } from "./constants.ts";

class StorageService {
  private memStore: Record<string, string> = {};

  private isChromeStorageAvailable(): boolean {
    return typeof chrome !== "undefined" && !!chrome?.storage?.local;
  }

  private getStorage(): { getItem: (k: string) => string | null; setItem: (k: string, v: string) => void; removeItem: (k: string) => void } {
    if (typeof localStorage !== "undefined" && typeof localStorage?.getItem === "function") {
      return localStorage;
    }
    return {
      getItem: (k: string) => this.memStore[k] || null,
      setItem: (k: string, v: string) => { this.memStore[k] = v; },
      removeItem: (k: string) => { delete this.memStore[k]; },
    };
  }

  async getAuth(): Promise<ExtStoredAuth | null> {
    let auth: ExtStoredAuth | null = null;
    if (this.isChromeStorageAvailable()) {
      const data = await chrome.storage.local.get(STORAGE_KEYS.AUTH);
      auth = data[STORAGE_KEYS.AUTH] || null;
    } else {
      const raw = this.getStorage().getItem(STORAGE_KEYS.AUTH);
      auth = raw ? JSON.parse(raw) : null;
    }
    if (auth && typeof auth === "object") {
      if (!auth.user) {
        auth.user = {
          id: (auth as any).user_id || "",
          email: (auth as any).user_email || "user@resumeiq.ai",
          name: (auth as any).user_name || "ResumeIQ User",
        };
      } else if (!auth.user.email) {
        auth.user.email = (auth as any).user_email || "user@resumeiq.ai";
      }
    }
    return auth;
  }

  async setAuth(auth: ExtStoredAuth): Promise<void> {
    if (this.isChromeStorageAvailable()) {
      await chrome.storage.local.set({ [STORAGE_KEYS.AUTH]: auth });
      return;
    }
    this.getStorage().setItem(STORAGE_KEYS.AUTH, JSON.stringify(auth));
  }

  async clearAuth(): Promise<void> {
    if (this.isChromeStorageAvailable()) {
      await chrome.storage.local.remove(STORAGE_KEYS.AUTH);
      return;
    }
    this.getStorage().removeItem(STORAGE_KEYS.AUTH);
  }

  async getSettings(): Promise<ExtSettings> {
    if (this.isChromeStorageAvailable()) {
      const data = await chrome.storage.local.get(STORAGE_KEYS.SETTINGS);
      return { ...DEFAULT_SETTINGS, ...(data[STORAGE_KEYS.SETTINGS] || {}) };
    }
    const raw = this.getStorage().getItem(STORAGE_KEYS.SETTINGS);
    return raw ? { ...DEFAULT_SETTINGS, ...JSON.parse(raw) } : DEFAULT_SETTINGS;
  }

  async setSettings(settings: Partial<ExtSettings>): Promise<ExtSettings> {
    const current = await this.getSettings();
    const updated = { ...current, ...settings };
    if (this.isChromeStorageAvailable()) {
      await chrome.storage.local.set({ [STORAGE_KEYS.SETTINGS]: updated });
      return updated;
    }
    this.getStorage().setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(updated));
    return updated;
  }

  async getCurrentJob(): Promise<CapturedJob | null> {
    if (this.isChromeStorageAvailable()) {
      const data = await chrome.storage.local.get(STORAGE_KEYS.CURRENT_JOB);
      return data[STORAGE_KEYS.CURRENT_JOB] || null;
    }
    const raw = this.getStorage().getItem(STORAGE_KEYS.CURRENT_JOB);
    return raw ? JSON.parse(raw) : null;
  }

  async setCurrentJob(job: CapturedJob | null): Promise<void> {
    if (this.isChromeStorageAvailable()) {
      if (job) {
        await chrome.storage.local.set({ [STORAGE_KEYS.CURRENT_JOB]: job });
      } else {
        await chrome.storage.local.remove(STORAGE_KEYS.CURRENT_JOB);
      }
      return;
    }
    if (job) {
      this.getStorage().setItem(STORAGE_KEYS.CURRENT_JOB, JSON.stringify(job));
    } else {
      this.getStorage().removeItem(STORAGE_KEYS.CURRENT_JOB);
    }
  }

  async getActiveResumeId(): Promise<string | null> {
    if (this.isChromeStorageAvailable()) {
      const data = await chrome.storage.local.get(STORAGE_KEYS.ACTIVE_RESUME_ID);
      return data[STORAGE_KEYS.ACTIVE_RESUME_ID] || null;
    }
    return this.getStorage().getItem(STORAGE_KEYS.ACTIVE_RESUME_ID);
  }

  async setActiveResumeId(resumeId: string): Promise<void> {
    if (this.isChromeStorageAvailable()) {
      await chrome.storage.local.set({ [STORAGE_KEYS.ACTIVE_RESUME_ID]: resumeId });
      return;
    }
    this.getStorage().setItem(STORAGE_KEYS.ACTIVE_RESUME_ID, resumeId);
  }

  async getLastMatchResult(): Promise<QuickMatchResult | null> {
    if (this.isChromeStorageAvailable()) {
      const data = await chrome.storage.local.get(STORAGE_KEYS.LAST_MATCH_RESULT);
      return data[STORAGE_KEYS.LAST_MATCH_RESULT] || null;
    }
    const raw = this.getStorage().getItem(STORAGE_KEYS.LAST_MATCH_RESULT);
    return raw ? JSON.parse(raw) : null;
  }

  async setLastMatchResult(result: QuickMatchResult | null): Promise<void> {
    if (this.isChromeStorageAvailable()) {
      if (result) {
        await chrome.storage.local.set({ [STORAGE_KEYS.LAST_MATCH_RESULT]: result });
      } else {
        await chrome.storage.local.remove(STORAGE_KEYS.LAST_MATCH_RESULT);
      }
      return;
    }
    if (result) {
      this.getStorage().setItem(STORAGE_KEYS.LAST_MATCH_RESULT, JSON.stringify(result));
    } else {
      this.getStorage().removeItem(STORAGE_KEYS.LAST_MATCH_RESULT);
    }
  }
}

export const storage = new StorageService();

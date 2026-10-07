import {
  ActionResponse,
  ActionType,
  CapturedJob,
  CompareResponse,
  ExtStoredAuth,
  QuickMatchResult,
  ResumeSummary,
  TrackerSaveResponse,
} from "./types";
import { storage } from "./storage";

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class OfflineError extends ApiError {
  constructor(message = "ResumeIQ backend is currently unreachable. Please check connection.") {
    super(message, 0, "OFFLINE");
    this.name = "OfflineError";
  }
}

class ApiClient {
  private async getBaseUrl(): Promise<string> {
    const auth = await storage.getAuth();
    if (auth?.api_base_url) return auth.api_base_url.replace(/\/+$/, "");
    const settings = await storage.getSettings();
    return settings.api_base_url.replace(/\/+$/, "");
  }

  private async fetchWithAuth(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const baseUrl = await this.getBaseUrl();
    const url = `${baseUrl}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

    const auth = await storage.getAuth();
    const headers = new Headers(options.headers || {});

    if (auth?.token) {
      headers.set("Authorization", `Bearer ${auth.token}`);
    }

    if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }

    try {
      const response = await fetch(url, { ...options, headers });

      if (response.status === 401 && auth?.refresh_token) {
        // Attempt token refresh
        const refreshed = await this.refresh();
        if (refreshed) {
          headers.set("Authorization", `Bearer ${refreshed.token}`);
          return await fetch(url, { ...options, headers });
        }
      }

      return response;
    } catch (err: any) {
      if (!window.navigator.onLine || err.message?.includes("Failed to fetch") || err.name === "TypeError") {
        throw new OfflineError();
      }
      throw err;
    }
  }

  async pair(pairingCode: string, serverUrl?: string): Promise<ExtStoredAuth> {
    const baseUrl = (serverUrl || (await this.getBaseUrl())).replace(/\/+$/, "");
    const url = `${baseUrl}/extension/auth/pair`;

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pairing_code: pairingCode.trim(),
          device_name: "ResumeIQ Chrome Extension MV3",
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
          errorData.detail || `Pairing failed with status ${response.status}`,
          response.status
        );
      }

      const data = await response.json();
      const user = data.user || {
        id: data.user_id || "",
        email: data.user_email || "user@resumeiq.ai",
        name: data.user_name || "ResumeIQ User",
      };
      const storedAuth: ExtStoredAuth = {
        token: data.extension_token,
        refresh_token: data.refresh_token,
        user,
        paired_at: new Date().toISOString(),
        expires_at: data.expires_at,
        api_base_url: baseUrl,
      };

      await storage.setAuth(storedAuth);
      return storedAuth;
    } catch (err: any) {
      if (err instanceof ApiError) throw err;
      throw new OfflineError(`Could not connect to ${baseUrl}. Please ensure ResumeIQ server is running.`);
    }
  }

  async refresh(): Promise<ExtStoredAuth | null> {
    const auth = await storage.getAuth();
    if (!auth?.refresh_token) return null;

    const baseUrl = await this.getBaseUrl();
    try {
      const response = await fetch(`${baseUrl}/extension/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: auth.refresh_token }),
      });

      if (!response.ok) {
        await storage.clearAuth();
        return null;
      }

      const data = await response.json();
      const user = data.user || auth.user || {
        id: data.user_id || "",
        email: data.user_email || "user@resumeiq.ai",
        name: data.user_name || "ResumeIQ User",
      };
      const updated: ExtStoredAuth = {
        ...auth,
        token: data.extension_token,
        refresh_token: data.refresh_token || auth.refresh_token,
        expires_at: data.expires_at,
        user,
      };
      await storage.setAuth(updated);
      return updated;
    } catch {
      return null;
    }
  }

  async revoke(): Promise<void> {
    const auth = await storage.getAuth();
    if (auth?.token) {
      try {
        await this.fetchWithAuth("/extension/auth/revoke", {
          method: "POST",
          body: JSON.stringify({ token: auth.token }),
        });
      } catch {
        // Ignore errors on revoke
      }
    }
    await storage.clearAuth();
  }

  async getResumes(): Promise<ResumeSummary[]> {
    const res = await this.fetchWithAuth("/extension/resumes");
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new ApiError(err.detail || "Failed to load resumes", res.status);
    }
    return await res.json();
  }

  async uploadResume(file: File): Promise<ResumeSummary> {
    const formData = new FormData();
    formData.append("file", file);

    const res = await this.fetchWithAuth("/extension/resume/upload", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new ApiError(err.detail || "Failed to upload and parse resume", res.status);
    }
    return await res.json();
  }

  async captureJob(job: CapturedJob): Promise<{ job_id: string; status: string; is_job_posting: boolean }> {
    const res = await this.fetchWithAuth("/extension/jd/capture", {
      method: "POST",
      body: JSON.stringify(job),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new ApiError(err.detail || "Failed to capture job description", res.status);
    }
    return await res.json();
  }

  async quickMatch(
    resumeId: string,
    jobId?: string,
    jobData?: CapturedJob
  ): Promise<QuickMatchResult> {
    const payload: any = { resume_id: resumeId };
    if (jobId) {
      payload.jd_id = jobId;
      payload.job_id = jobId;
    }
    if (jobData) {
      payload.job_data = jobData;
      payload.raw_jd_text = jobData.description;
      payload.title = jobData.title;
      payload.company = jobData.company;
      payload.source_url = jobData.url;
      payload.capture_method = jobData.source_platform ? "site_adapter" : "selection";
    }

    const res = await this.fetchWithAuth("/extension/match/quick", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new ApiError(err.detail || "Failed to calculate match score", res.status);
    }

    const data: QuickMatchResult = await res.json();
    await storage.setLastMatchResult(data);
    return data;
  }

  async streamExplanation(
    matchId: string,
    onChunk: (chunk: string) => void,
    onDone: () => void,
    onError: (err: any) => void
  ): Promise<() => void> {
    const baseUrl = await this.getBaseUrl();
    const auth = await storage.getAuth();
    const url = `${baseUrl}/extension/match/${matchId}/stream-explanation`;

    const controller = new AbortController();

    fetch(url, {
      signal: controller.signal,
      headers: {
        Authorization: auth?.token ? `Bearer ${auth.token}` : "",
      },
    })
      .then(async (res) => {
        if (!res.ok || !res.body) {
          throw new ApiError(`Stream failed with status ${res.status}`, res.status);
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data:")) {
              const dataStr = line.slice(5).trim();
              if (dataStr === "[DONE]") {
                onDone();
                return;
              }
              try {
                const parsed = JSON.parse(dataStr);
                if (parsed.text) {
                  onChunk(parsed.text);
                }
              } catch {
                if (dataStr) onChunk(dataStr);
              }
            }
          }
        }
        onDone();
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          onError(err);
        }
      });

    return () => controller.abort();
  }

  async triggerAction(
    actionType: ActionType,
    resumeId: string,
    matchId?: string,
    targetPlatform = "generic"
  ): Promise<ActionResponse> {
    const endpointMap: Record<ActionType, string> = {
      tailor: "/extension/actions/tailor",
      cover_letter: "/extension/actions/cover-letter",
      recruiter_message: "/extension/actions/recruiter-message",
    };

    const res = await this.fetchWithAuth(endpointMap[actionType], {
      method: "POST",
      body: JSON.stringify({
        match_id: matchId,
        resume_id: resumeId,
        action_type: actionType,
        target_platform: targetPlatform,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new ApiError(err.detail || `Action ${actionType} failed`, res.status);
    }
    return await res.json();
  }

  async saveToTracker(
    matchId: string,
    status = "saved",
    notes = ""
  ): Promise<TrackerSaveResponse> {
    const res = await this.fetchWithAuth("/extension/tracker/save", {
      method: "POST",
      body: JSON.stringify({
        match_id: matchId,
        stage: status,
        status: status,
        notes,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new ApiError(err.detail || "Failed to save job to tracker", res.status);
    }
    return await res.json();
  }

  async compareResumes(
    resumeIds: string[],
    jobId?: string,
    jobData?: CapturedJob
  ): Promise<CompareResponse> {
    const payload: any = { resume_ids: resumeIds };
    if (jobId) {
      payload.jd_id = jobId;
      payload.job_id = jobId;
    }
    if (jobData) {
      payload.job_data = jobData;
      payload.raw_jd_text = jobData.description;
      payload.title = jobData.title;
      payload.company = jobData.company;
    }

    const res = await this.fetchWithAuth("/extension/compare", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new ApiError(err.detail || "Failed to compare resumes", res.status);
    }
    return await res.json();
  }
}

export const apiClient = new ApiClient();

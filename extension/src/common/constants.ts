import type { ExtSettings } from "./types.ts";

// Build-time configured API base URL:
// In production, default must be HTTPS (no localhost default allowed).
const isProd =
  (typeof process !== "undefined" && process.env?.NODE_ENV === "production") ||
  (typeof import.meta !== "undefined" && Boolean((import.meta as any).env?.PROD));

const configuredApiUrl =
  (typeof process !== "undefined" && process.env?.VITE_API_URL) ||
  (typeof import.meta !== "undefined" && (import.meta as any).env?.VITE_API_URL);

export const DEFAULT_API_BASE_URL =
  configuredApiUrl ||
  (isProd ? "https://api.resumeiq.ai/api/v1" : "http://localhost:8000/api/v1");

export const DEFAULT_SETTINGS: ExtSettings = {
  api_base_url: DEFAULT_API_BASE_URL,
  threshold_strong: 80,
  threshold_good: 65,
  threshold_partial: 45,
  auto_match_on_open: true,
  floating_button_enabled: true,
};

export const STORAGE_KEYS = {
  AUTH: "resumeiq_auth",
  SETTINGS: "resumeiq_settings",
  CURRENT_JOB: "resumeiq_current_job",
  ACTIVE_RESUME_ID: "resumeiq_active_resume_id",
  LAST_MATCH_RESULT: "resumeiq_last_match_result",
} as const;

export const MESSAGE_TYPES = {
  CAPTURE_JOB: "RESUMEQ_CAPTURE_JOB",
  OPEN_SIDE_PANEL: "RESUMEQ_OPEN_SIDE_PANEL",
  JOB_CAPTURED_EVENT: "RESUMEQ_JOB_CAPTURED_EVENT",
  TRIGGER_MATCH_EVENT: "RESUMEQ_TRIGGER_MATCH_EVENT",
  AUTH_CHANGED_EVENT: "RESUMEQ_AUTH_CHANGED_EVENT",
} as const;

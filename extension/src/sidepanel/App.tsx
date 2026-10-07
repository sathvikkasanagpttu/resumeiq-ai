import React, { useEffect, useState, useCallback, useRef } from "react";
import {
  ActionResponse,
  ActionType,
  CapturedJob,
  ExtSettings,
  ExtStoredAuth,
  QuickMatchResult,
  ResumeSummary,
} from "../common/types";
import { apiClient, OfflineError } from "../common/api-client";
import { storage } from "../common/storage";
import { DEFAULT_SETTINGS, MESSAGE_TYPES } from "../common/constants";
import { Header } from "./components/Header";
import { PairingView } from "./components/PairingView";
import { OfflineBanner } from "./components/OfflineBanner";
import { JDCaptureCard } from "./components/JDCaptureCard";
import { ResumePicker } from "./components/ResumePicker";
import { ScoreRing } from "./components/ScoreRing";
import { VerdictBadge } from "./components/VerdictBadge";
import { ComponentBars } from "./components/ComponentBars";
import { MatchedSkillsList } from "./components/MatchedSkillsList";
import { GapSeverityList } from "./components/GapSeverityList";
import { StreamedExplanation } from "./components/StreamedExplanation";
import { QuickActions } from "./components/QuickActions";
import { CompareDrawer } from "./components/CompareDrawer";
import { SettingsModal } from "./components/SettingsModal";
import { Sparkles, Loader2, ArrowRight } from "lucide-react";

export const App: React.FC = () => {
  // Global States
  const [auth, setAuth] = useState<ExtStoredAuth | null>(null);
  const [settings, setSettings] = useState<ExtSettings>(DEFAULT_SETTINGS);
  const [isOffline, setIsOffline] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);

  // Modals & Panels
  const [showSettings, setShowSettings] = useState(false);
  const [showCompare, setShowCompare] = useState(false);

  // Data States
  const [currentJob, setCurrentJob] = useState<CapturedJob | null>(null);
  const [isCapturingJob, setIsCapturingJob] = useState(false);
  const [resumes, setResumes] = useState<ResumeSummary[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string | null>(null);
  const [isUploadingResume, setIsUploadingResume] = useState(false);

  // Match State
  const [matchResult, setMatchResult] = useState<QuickMatchResult | null>(null);
  const [isMatching, setIsMatching] = useState(false);
  const [matchError, setMatchError] = useState<string | null>(null);

  // Streaming Explanation State
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedText, setStreamedText] = useState("");
  const abortStreamRef = useRef<(() => void) | null>(null);

  // Active Tab View in Results
  const [activeTab, setActiveTab] = useState<"overview" | "skills" | "gaps" | "actions">("overview");

  // Actions State
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [activeActionType, setActiveActionType] = useState<ActionType | null>(null);
  const [trackerSaved, setTrackerSaved] = useState(false);

  // 1. Initial Load & Auth Hydration
  useEffect(() => {
    async function init() {
      try {
        let storedAuth = await storage.getAuth();
        const storedSettings = await storage.getSettings();
        const storedJob = await storage.getCurrentJob();
        const storedResumeId = await storage.getActiveResumeId();

        if (storedAuth && (!storedAuth.token || typeof storedAuth.token !== "string")) {
          await storage.clearAuth();
          storedAuth = null;
        } else if (storedAuth) {
          if (!storedAuth.user) {
            storedAuth.user = { id: "", email: "user@resumeiq.ai", name: "ResumeIQ User" };
          } else if (!storedAuth.user.email) {
            storedAuth.user.email = "user@resumeiq.ai";
          }
        }

        setAuth(storedAuth);
        setSettings(storedSettings);
        if (storedJob) setCurrentJob(storedJob);
        if (storedResumeId) setSelectedResumeId(storedResumeId);

        if (storedAuth) {
          await loadResumesAndActiveJob(storedAuth, storedJob);
        }
      } catch (err: any) {
        if (err instanceof OfflineError) setIsOffline(true);
      } finally {
        setIsInitializing(false);
      }
    }
    init();
  }, []);

  // 2. Load Resumes and check current tab
  const loadResumesAndActiveJob = async (
    _storedAuth?: ExtStoredAuth,
    existingJob?: CapturedJob | null
  ) => {
    try {
      setIsOffline(false);
      const list = await apiClient.getResumes();
      setResumes(list);

      let activeId = selectedResumeId;
      if (!activeId && list.length > 0) {
        activeId = list[0].id;
        setSelectedResumeId(activeId);
        await storage.setActiveResumeId(activeId);
      }

      // If no job loaded yet, capture from active tab
      if (!existingJob) {
        await captureFromActiveTab();
      }
    } catch (err: any) {
      if (err instanceof OfflineError) setIsOffline(true);
    }
  };

  // 3. Capture Job from Active Tab
  const captureFromActiveTab = useCallback(async () => {
    if (typeof chrome === "undefined" || !chrome?.tabs?.query) return;

    setIsCapturingJob(true);
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab?.id) {
        const response = await chrome.tabs.sendMessage(tab.id, {
          type: MESSAGE_TYPES.CAPTURE_JOB,
        }).catch(() => null);

        if (response?.job) {
          setCurrentJob(response.job);
          await storage.setCurrentJob(response.job);
        }
      }
    } catch {
      // Content script may not be running on internal pages
    } finally {
      setIsCapturingJob(false);
    }
  }, []);

  // 4. Run Match Pipeline (Two-tier: Deterministic first, then SSE stream)
  const runMatch = useCallback(
    async (resumeIdOverride?: string, jobOverride?: CapturedJob) => {
      const rId = resumeIdOverride || selectedResumeId;
      const job = jobOverride || currentJob;

      if (!rId || !job || !job.description) return;

      setIsMatching(true);
      setMatchError(null);
      setTrackerSaved(false);
      if (abortStreamRef.current) abortStreamRef.current();

      try {
        setIsOffline(false);
        // Tier 1: Fast deterministic match (< 2s)
        const result = await apiClient.quickMatch(rId, undefined, job);
        setMatchResult(result);
        setIsMatching(false);

        // Tier 2: Stream explanation in background
        setIsStreaming(true);
        setStreamedText("");

        const abortFn = await apiClient.streamExplanation(
          result.match_id,
          (chunk) => {
            setStreamedText((prev) => prev + chunk);
          },
          () => {
            setIsStreaming(false);
          },
          () => {
            setIsStreaming(false);
          }
        );
        abortStreamRef.current = abortFn;
      } catch (err: any) {
        setIsMatching(false);
        setIsStreaming(false);
        if (err instanceof OfflineError) {
          setIsOffline(true);
        } else {
          setMatchError(err.message || "Failed to calculate match score.");
        }
      }
    },
    [selectedResumeId, currentJob]
  );

  // Auto match on selection change or initial job acquisition if configured
  useEffect(() => {
    if (auth && selectedResumeId && currentJob?.description && settings.auto_match_on_open && !matchResult) {
      runMatch();
    }
  }, [auth, selectedResumeId, currentJob, settings.auto_match_on_open, matchResult, runMatch]);

  // Handle Resume Selection
  const handleSelectResume = async (id: string) => {
    setSelectedResumeId(id);
    await storage.setActiveResumeId(id);
    runMatch(id);
  };

  // Handle Resume File Upload
  const handleUploadResumeFile = async (file: File) => {
    setIsUploadingResume(true);
    try {
      setIsOffline(false);
      const newResume = await apiClient.uploadResume(file);
      setResumes((prev) => [newResume, ...prev]);
      setSelectedResumeId(newResume.id);
      await storage.setActiveResumeId(newResume.id);
      runMatch(newResume.id);
    } catch (err: any) {
      if (err instanceof OfflineError) {
        setIsOffline(true);
      } else {
        alert(err.message || "Resume upload failed");
      }
    } finally {
      setIsUploadingResume(false);
    }
  };

  // Handle Job Edit / Update
  const handleUpdateJob = async (updated: CapturedJob) => {
    setCurrentJob(updated);
    await storage.setCurrentJob(updated);
    runMatch(selectedResumeId || undefined, updated);
  };

  // Actions
  const handleTriggerAction = async (type: ActionType): Promise<ActionResponse> => {
    if (!selectedResumeId) throw new Error("Please select a resume first");
    setIsActionLoading(true);
    setActiveActionType(type);
    try {
      setIsOffline(false);
      const res = await apiClient.triggerAction(type, selectedResumeId, matchResult?.match_id, currentJob?.source_platform);
      return res;
    } catch (err: any) {
      if (err instanceof OfflineError) setIsOffline(true);
      throw err;
    } finally {
      setIsActionLoading(false);
      setActiveActionType(null);
    }
  };

  const handleSaveToTracker = async () => {
    if (!matchResult?.match_id) return;
    setIsActionLoading(true);
    try {
      setIsOffline(false);
      await apiClient.saveToTracker(matchResult.match_id, "saved", `Captured from ${currentJob?.source_platform || "Web"}`);
      setTrackerSaved(true);
    } catch (err: any) {
      if (err instanceof OfflineError) setIsOffline(true);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleOpenWebApp = () => {
    const baseUrl = settings.api_base_url.replace(/\/api\/v1\/?$/, "");
    if (typeof chrome !== "undefined" && chrome?.tabs?.create) {
      chrome.tabs.create({ url: `${baseUrl}/tracker` });
    } else {
      window.open(`${baseUrl}/tracker`, "_blank");
    }
  };

  const handleDisconnect = async () => {
    await apiClient.revoke();
    setAuth(null);
    setMatchResult(null);
  };

  if (isInitializing) {
    return (
      <div className="h-screen flex items-center justify-center bg-slate-50">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col antialiased text-slate-900">
      {/* Header */}
      <Header
        auth={auth}
        isOffline={isOffline}
        onRefreshJob={captureFromActiveTab}
        onToggleCompare={() => setShowCompare(true)}
        onOpenSettings={() => setShowSettings(true)}
        onDisconnect={handleDisconnect}
        compareMode={showCompare}
      />

      {/* Offline Alert */}
      {isOffline && <OfflineBanner onRetry={() => loadResumesAndActiveJob(auth || undefined, currentJob)} />}

      {/* Main Container */}
      <main className="flex-1 p-3.5 space-y-3.5 max-w-lg mx-auto w-full">
        {!auth ? (
          <PairingView
            onPaired={async (newAuth) => {
              if (newAuth && !newAuth.user) {
                newAuth.user = { id: "", email: "user@resumeiq.ai", name: "ResumeIQ User" };
              }
              setAuth(newAuth);
              await loadResumesAndActiveJob(newAuth);
            }}
            defaultServerUrl={settings.api_base_url}
          />
        ) : (
          <>
            {/* Captured JD Card */}
            <JDCaptureCard
              job={currentJob}
              onUpdateJob={handleUpdateJob}
              onRefreshFromTab={captureFromActiveTab}
              isLoading={isCapturingJob}
            />

            {/* Resume Version Picker */}
            <ResumePicker
              resumes={resumes}
              selectedResumeId={selectedResumeId}
              onSelectResume={handleSelectResume}
              onUploadFile={handleUploadResumeFile}
              isUploading={isUploadingResume}
            />

            {/* Match Trigger Button if not yet matched or re-evaluating */}
            {currentJob && selectedResumeId && (
              <button
                onClick={() => runMatch()}
                disabled={isMatching}
                className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 disabled:bg-slate-300 text-white font-semibold text-xs rounded-xl shadow-sm flex items-center justify-center gap-2 transition-all cursor-pointer disabled:cursor-not-allowed"
              >
                {isMatching ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Computing Evidence Match (17ms)...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 text-indigo-200" />
                    Calculate Match Compatibility
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            )}

            {matchError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800">
                {matchError}
              </div>
            )}

            {/* Match Results Display */}
            {matchResult && (
              <div className="space-y-3 pt-1 animate-in fade-in">
                {/* Score & Verdict Card */}
                <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs flex items-center justify-between gap-4">
                  <ScoreRing score={matchResult.overall_score} />
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                      Compatibility Verdict
                    </span>
                    <VerdictBadge verdict={matchResult.verdict} />
                    <p className="text-[11px] text-slate-500 leading-snug">
                      Derived deterministically from 8 weighted evidence pillars.
                    </p>
                  </div>
                </div>

                {/* Sub-navigation Tabs */}
                <div className="flex items-center gap-1 p-1 bg-slate-200/70 rounded-xl text-xs">
                  <button
                    onClick={() => setActiveTab("overview")}
                    className={`flex-1 py-1.5 rounded-lg font-semibold transition-all ${
                      activeTab === "overview"
                        ? "bg-white text-indigo-700 shadow-2xs"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    Breakdown
                  </button>
                  <button
                    onClick={() => setActiveTab("skills")}
                    className={`flex-1 py-1.5 rounded-lg font-semibold transition-all ${
                      activeTab === "skills"
                        ? "bg-white text-indigo-700 shadow-2xs"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    Skills ({matchResult.matched_skills.length})
                  </button>
                  <button
                    onClick={() => setActiveTab("gaps")}
                    className={`flex-1 py-1.5 rounded-lg font-semibold transition-all ${
                      activeTab === "gaps"
                        ? "bg-white text-indigo-700 shadow-2xs"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    Gaps ({matchResult.skill_gaps.critical.length + matchResult.skill_gaps.representation.length})
                  </button>
                  <button
                    onClick={() => setActiveTab("actions")}
                    className={`flex-1 py-1.5 rounded-lg font-semibold transition-all ${
                      activeTab === "actions"
                        ? "bg-white text-indigo-700 shadow-2xs"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    Actions
                  </button>
                </div>

                {/* Tab Views */}
                {activeTab === "overview" && (
                  <div className="space-y-3 animate-in fade-in">
                    <ComponentBars scores={matchResult.component_scores} />
                    <StreamedExplanation
                      bullets={matchResult.why_this_verdict}
                      isStreaming={isStreaming}
                      streamedText={streamedText}
                      onRefreshStream={() => runMatch()}
                    />
                  </div>
                )}

                {activeTab === "skills" && (
                  <div className="animate-in fade-in">
                    <MatchedSkillsList
                      matchedSkills={matchResult.matched_skills}
                      transferableSkills={matchResult.transferable_skills}
                    />
                  </div>
                )}

                {activeTab === "gaps" && (
                  <div className="animate-in fade-in">
                    <GapSeverityList gaps={matchResult.skill_gaps} />
                  </div>
                )}

                {activeTab === "actions" && (
                  <div className="animate-in fade-in">
                    <QuickActions
                      onTriggerAction={handleTriggerAction}
                      onSaveToTracker={handleSaveToTracker}
                      onOpenWebApp={handleOpenWebApp}
                      isActionLoading={isActionLoading}
                      activeActionType={activeActionType}
                      trackerSaved={trackerSaved}
                    />
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </main>

      {/* Compare Resumes Drawer */}
      {showCompare && (
        <CompareDrawer
          resumes={resumes}
          activeJobId={matchResult?.match_id}
          onClose={() => setShowCompare(false)}
          onSelectResume={handleSelectResume}
        />
      )}

      {/* Settings Modal */}
      {showSettings && (
        <SettingsModal
          settings={settings}
          onSave={async (newSettings) => {
            const updated = await storage.setSettings(newSettings);
            setSettings(updated);
          }}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
};

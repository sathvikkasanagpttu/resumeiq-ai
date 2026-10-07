import React, { useState } from "react";
import {
  Wand2,
  FileCheck,
  Mail,
  BookmarkPlus,
  ExternalLink,
  Copy,
  Check,
  Loader2,
  ShieldCheck,
  X,
} from "lucide-react";
import { ActionResponse, ActionType } from "../../common/types";

interface QuickActionsProps {
  onTriggerAction: (type: ActionType) => Promise<ActionResponse>;
  onSaveToTracker: () => Promise<void>;
  onOpenWebApp: () => void;
  isActionLoading: boolean;
  activeActionType: ActionType | null;
  trackerSaved: boolean;
}

export const QuickActions: React.FC<QuickActionsProps> = ({
  onTriggerAction,
  onSaveToTracker,
  onOpenWebApp,
  isActionLoading,
  activeActionType,
  trackerSaved,
}) => {
  const [modalContent, setModalContent] = useState<ActionResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const handleAction = async (type: ActionType) => {
    try {
      const result = await onTriggerAction(type);
      setModalContent(result);
      setCopied(false);
    } catch {
      // Error handled by parent
    }
  };

  const handleCopy = () => {
    if (modalContent?.generated_content) {
      navigator.clipboard.writeText(modalContent.generated_content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getActionTitle = (type: ActionType) => {
    switch (type) {
      case "tailor":
        return "Tailored Resume Bullet Suggestions";
      case "cover_letter":
        return "Grounded Cover Letter";
      case "recruiter_message":
        return "Personalized Recruiter Message";
    }
  };

  return (
    <div className="space-y-2.5">
      <h4 className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
        One-Click Actions
      </h4>

      <div className="grid grid-cols-2 gap-2">
        {/* Tailor Resume */}
        <button
          onClick={() => handleAction("tailor")}
          disabled={isActionLoading}
          className="p-2.5 bg-white hover:bg-slate-50 active:bg-slate-100 border border-slate-200 hover:border-indigo-300 rounded-xl text-left shadow-2xs transition-all flex flex-col justify-between gap-2 group cursor-pointer disabled:cursor-not-allowed"
        >
          <div className="flex items-center justify-between w-full">
            <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Wand2 className="w-4 h-4" />
            </div>
            {isActionLoading && activeActionType === "tailor" && (
              <Loader2 className="w-3.5 h-3.5 text-indigo-600 animate-spin" />
            )}
          </div>
          <div>
            <span className="font-bold text-xs text-slate-900 block">Tailor Resume</span>
            <span className="text-[10px] text-slate-500 block leading-tight">
              Align verified bullet points
            </span>
          </div>
        </button>

        {/* Cover Letter */}
        <button
          onClick={() => handleAction("cover_letter")}
          disabled={isActionLoading}
          className="p-2.5 bg-white hover:bg-slate-50 active:bg-slate-100 border border-slate-200 hover:border-indigo-300 rounded-xl text-left shadow-2xs transition-all flex flex-col justify-between gap-2 group cursor-pointer disabled:cursor-not-allowed"
        >
          <div className="flex items-center justify-between w-full">
            <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <FileCheck className="w-4 h-4" />
            </div>
            {isActionLoading && activeActionType === "cover_letter" && (
              <Loader2 className="w-3.5 h-3.5 text-emerald-600 animate-spin" />
            )}
          </div>
          <div>
            <span className="font-bold text-xs text-slate-900 block">Cover Letter</span>
            <span className="text-[10px] text-slate-500 block leading-tight">
              Evidence-based draft
            </span>
          </div>
        </button>

        {/* Recruiter Outreach */}
        <button
          onClick={() => handleAction("recruiter_message")}
          disabled={isActionLoading}
          className="p-2.5 bg-white hover:bg-slate-50 active:bg-slate-100 border border-slate-200 hover:border-indigo-300 rounded-xl text-left shadow-2xs transition-all flex flex-col justify-between gap-2 group cursor-pointer disabled:cursor-not-allowed"
        >
          <div className="flex items-center justify-between w-full">
            <div className="w-7 h-7 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Mail className="w-4 h-4" />
            </div>
            {isActionLoading && activeActionType === "recruiter_message" && (
              <Loader2 className="w-3.5 h-3.5 text-violet-600 animate-spin" />
            )}
          </div>
          <div>
            <span className="font-bold text-xs text-slate-900 block">Recruiter Message</span>
            <span className="text-[10px] text-slate-500 block leading-tight">
              Concise LinkedIn pitch
            </span>
          </div>
        </button>

        {/* Save to Job Tracker */}
        <button
          onClick={onSaveToTracker}
          disabled={isActionLoading || trackerSaved}
          className={`p-2.5 border rounded-xl text-left shadow-2xs transition-all flex flex-col justify-between gap-2 group cursor-pointer disabled:cursor-not-allowed ${
            trackerSaved
              ? "bg-emerald-50 border-emerald-200"
              : "bg-white hover:bg-slate-50 border-slate-200 hover:border-amber-300"
          }`}
        >
          <div className="flex items-center justify-between w-full">
            <div
              className={`w-7 h-7 rounded-lg flex items-center justify-center group-hover:scale-105 transition-transform ${
                trackerSaved ? "bg-emerald-100 text-emerald-700" : "bg-amber-50 text-amber-600"
              }`}
            >
              {trackerSaved ? <Check className="w-4 h-4" /> : <BookmarkPlus className="w-4 h-4" />}
            </div>
          </div>
          <div>
            <span className="font-bold text-xs text-slate-900 block">
              {trackerSaved ? "Saved to Tracker" : "Save to Tracker"}
            </span>
            <span className="text-[10px] text-slate-500 block leading-tight">
              {trackerSaved ? "Logged in database" : "Add to pipeline"}
            </span>
          </div>
        </button>
      </div>

      {/* Web App Link */}
      <button
        onClick={onOpenWebApp}
        className="w-full py-2 px-3 bg-slate-100 hover:bg-slate-200 active:bg-slate-300 text-slate-700 font-medium text-xs rounded-lg transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
      >
        <span>Open Deep Analysis in Web App</span>
        <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
      </button>

      {/* Action Results Modal */}
      {modalContent && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-3 animate-in fade-in">
          <div className="bg-white rounded-2xl shadow-xl w-full max-h-[85vh] flex flex-col border border-slate-200 overflow-hidden">
            <div className="p-3.5 border-b border-slate-100 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <h3 className="font-bold text-xs text-slate-900">
                  {getActionTitle(modalContent.action_type)}
                </h3>
              </div>
              <button
                onClick={() => setModalContent(null)}
                className="p-1 text-slate-400 hover:text-slate-700 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-3 bg-emerald-50/50 border-b border-emerald-100 text-[11px] text-emerald-800 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              <span>
                Evidence-grounded: Strictly generated from {modalContent.grounded_evidence_count} verified facts in your profile. Zero hallucinated metrics.
              </span>
            </div>

            <div className="p-4 overflow-y-auto flex-1 font-sans text-xs text-slate-800 leading-relaxed whitespace-pre-wrap select-text">
              {modalContent.generated_content}
            </div>

            <div className="p-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between gap-2">
              <span className="text-[10px] text-slate-400">
                Ready to review and copy
              </span>
              <button
                onClick={handleCopy}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors shadow-2xs cursor-pointer"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5" />
                    Copied to Clipboard!
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    Copy Text
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

import React from "react";
import { Sparkles, RefreshCw, Settings, SplitSquareVertical, LogOut } from "lucide-react";
import { ExtStoredAuth } from "../../common/types";

interface HeaderProps {
  auth: ExtStoredAuth | null;
  isOffline: boolean;
  onRefreshJob: () => void;
  onToggleCompare: () => void;
  onOpenSettings: () => void;
  onDisconnect: () => void;
  compareMode: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  auth,
  isOffline,
  onRefreshJob,
  onToggleCompare,
  onOpenSettings,
  onDisconnect,
  compareMode,
}) => {
  return (
    <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-slate-200 px-4 py-3 flex items-center justify-between shadow-xs">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-linear-to-tr from-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-sm font-bold text-xs">
          <Sparkles className="w-4 h-4" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <span className="font-bold text-slate-900 text-sm tracking-tight">ResumeIQ</span>
            <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
              v2.1
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isOffline
                  ? "bg-rose-500 animate-pulse"
                  : auth
                  ? "bg-emerald-500"
                  : "bg-amber-500"
              }`}
            />
            <span className="text-[10px] text-slate-500">
              {isOffline
                ? "Backend Offline"
                : auth?.user?.email
                ? `Connected (${auth.user.email.split("@")[0]})`
                : auth
                ? "Connected"
                : "Unpaired"}
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-1">
        {auth && (
          <>
            <button
              onClick={onRefreshJob}
              title="Re-capture job from active tab"
              className="p-1.5 text-slate-500 hover:text-indigo-600 hover:bg-slate-100 rounded-md transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={onToggleCompare}
              title="Compare Resume Versions"
              className={`p-1.5 rounded-md transition-colors ${
                compareMode
                  ? "bg-indigo-100 text-indigo-700"
                  : "text-slate-500 hover:text-indigo-600 hover:bg-slate-100"
              }`}
            >
              <SplitSquareVertical className="w-4 h-4" />
            </button>
          </>
        )}
        <button
          onClick={onOpenSettings}
          title="Settings"
          className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-md transition-colors"
        >
          <Settings className="w-4 h-4" />
        </button>
        {auth && (
          <button
            onClick={onDisconnect}
            title="Disconnect Extension"
            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        )}
      </div>
    </header>
  );
};

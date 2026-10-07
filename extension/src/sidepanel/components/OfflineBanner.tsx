import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface OfflineBannerProps {
  onRetry: () => void;
  message?: string;
}

export const OfflineBanner: React.FC<OfflineBannerProps> = ({
  onRetry,
  message = "ResumeIQ backend server is unreachable. Please verify that your local or cloud backend is running.",
}) => {
  return (
    <div className="bg-rose-50 border-b border-rose-200 px-4 py-2.5 text-xs text-rose-800 flex items-center justify-between gap-2 animate-in fade-in">
      <div className="flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
        <span>{message}</span>
      </div>
      <button
        onClick={onRetry}
        className="px-2 py-1 bg-white hover:bg-rose-100 text-rose-700 font-medium border border-rose-300 rounded shadow-2xs flex items-center gap-1 shrink-0"
      >
        <RefreshCw className="w-3 h-3" />
        Retry
      </button>
    </div>
  );
};

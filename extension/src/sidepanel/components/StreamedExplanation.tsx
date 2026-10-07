import React from "react";
import { Sparkles, MessageSquare, CheckCircle, RefreshCw } from "lucide-react";

interface StreamedExplanationProps {
  bullets: string[];
  isStreaming: boolean;
  streamedText: string;
  onRefreshStream?: () => void;
}

export const StreamedExplanation: React.FC<StreamedExplanationProps> = ({
  bullets,
  isStreaming,
  streamedText,
  onRefreshStream,
}) => {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-[11px] font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          Why This Verdict (Evidence-Grounded)
        </h4>
        {isStreaming ? (
          <span className="flex items-center gap-1 text-[10px] font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-200 animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-600" />
            Analyzing...
          </span>
        ) : (
          onRefreshStream && (
            <button
              onClick={onRefreshStream}
              title="Re-stream explanation"
              className="text-slate-400 hover:text-indigo-600 p-0.5"
            >
              <RefreshCw className="w-3 h-3" />
            </button>
          )
        )}
      </div>

      {isStreaming && streamedText && (
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700 font-sans leading-relaxed whitespace-pre-wrap animate-in fade-in">
          {streamedText}
          <span className="inline-block w-1.5 h-3.5 bg-indigo-600 ml-1 animate-pulse" />
        </div>
      )}

      {(!isStreaming || !streamedText) && bullets.length > 0 && (
        <ul className="space-y-2 text-xs text-slate-700">
          {bullets.map((b, idx) => (
            <li key={idx} className="flex items-start gap-2 leading-relaxed">
              <CheckCircle className="w-3.5 h-3.5 text-indigo-500 shrink-0 mt-0.5" />
              <span>{b}</span>
            </li>
          ))}
        </ul>
      )}

      {!isStreaming && bullets.length === 0 && !streamedText && (
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center text-xs text-slate-500 flex items-center justify-center gap-1.5">
          <MessageSquare className="w-4 h-4 text-slate-400" />
          <span>Generating verdict explanation...</span>
        </div>
      )}
    </div>
  );
};

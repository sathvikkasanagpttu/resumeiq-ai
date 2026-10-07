import React, { useState } from "react";
import { SplitSquareVertical, ArrowRight, CheckCircle2, AlertCircle, Loader2, X } from "lucide-react";
import { CompareResponse, ResumeSummary } from "../../common/types";
import { apiClient } from "../../common/api-client";
import { VerdictBadge } from "./VerdictBadge";

interface CompareDrawerProps {
  resumes: ResumeSummary[];
  activeJobId?: string;
  onClose: () => void;
  onSelectResume: (id: string) => void;
}

export const CompareDrawer: React.FC<CompareDrawerProps> = ({
  resumes,
  activeJobId,
  onClose,
  onSelectResume,
}) => {
  const [selectedIds, setSelectedIds] = useState<string[]>(
    resumes.slice(0, 2).map((r) => r.id)
  );
  const [loading, setLoading] = useState(false);
  const [comparison, setComparison] = useState<CompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const toggleSelect = (id: string) => {
    if (selectedIds.includes(id)) {
      if (selectedIds.length > 1) {
        setSelectedIds(selectedIds.filter((item) => item !== id));
      }
    } else {
      if (selectedIds.length < 3) {
        setSelectedIds([...selectedIds, id]);
      }
    }
  };

  const handleRunCompare = async () => {
    if (selectedIds.length < 2) {
      setError("Please select at least 2 resume versions to compare.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await apiClient.compareResumes(selectedIds, activeJobId);
      setComparison(data);
    } catch (err: any) {
      setError(err.message || "Failed to compare resumes");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-3 animate-in fade-in">
      <div className="bg-white rounded-2xl shadow-xl w-full max-h-[90vh] flex flex-col border border-slate-200 overflow-hidden">
        {/* Header */}
        <div className="p-3.5 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2">
            <SplitSquareVertical className="w-4 h-4 text-indigo-600" />
            <h3 className="font-bold text-xs text-slate-900">
              Side-by-Side Resume Comparison
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-700 rounded-md"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto space-y-4 flex-1">
          <p className="text-xs text-slate-600 leading-snug">
            Compare which of your resume versions has higher evidence match and fewer gaps for this specific job.
          </p>

          {/* Selection pills */}
          <div className="space-y-1.5">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
              Select 2 to 3 Resumes ({selectedIds.length}/3)
            </span>
            <div className="flex flex-wrap gap-1.5">
              {resumes.map((r) => {
                const isSelected = selectedIds.includes(r.id);
                return (
                  <button
                    key={r.id}
                    onClick={() => toggleSelect(r.id)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-all ${
                      isSelected
                        ? "bg-indigo-600 border-indigo-600 text-white shadow-2xs"
                        : "bg-white border-slate-200 text-slate-700 hover:border-slate-300"
                    }`}
                  >
                    {r.title || r.filename} (v{r.version})
                  </button>
                );
              })}
            </div>
          </div>

          <button
            onClick={handleRunCompare}
            disabled={loading || selectedIds.length < 2}
            className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors cursor-pointer disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Computing Comparison...
              </>
            ) : (
              <>
                Compare Selected ({selectedIds.length})
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>

          {error && (
            <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800">
              {error}
            </div>
          )}

          {/* Comparison Cards */}
          {comparison && (
            <div className="space-y-3 pt-2">
              <h4 className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                Results for: {comparison.job_title}
              </h4>

              <div className="grid grid-cols-1 gap-2.5">
                {comparison.resumes.map((item) => (
                  <div
                    key={item.resume_id}
                    className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-bold text-xs text-slate-900 block truncate">
                          {item.resume_name} (v{item.version})
                        </span>
                        <span className="text-[10px] text-slate-500">
                          {item.skill_coverage_pct}% skill coverage
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-extrabold text-slate-900 font-mono">
                          {Math.round(item.overall_score)}%
                        </span>
                        <VerdictBadge verdict={item.verdict} />
                      </div>
                    </div>

                    {/* Strengths */}
                    {item.key_strengths.length > 0 && (
                      <div className="text-[11px] space-y-0.5">
                        <span className="font-semibold text-emerald-800 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          Key Strengths:
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {item.key_strengths.map((s) => (
                            <span key={s} className="px-1.5 py-0.5 bg-white border border-emerald-200 text-emerald-800 rounded text-[10px]">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Critical Gaps */}
                    {item.critical_gaps.length > 0 && (
                      <div className="text-[11px] space-y-0.5">
                        <span className="font-semibold text-rose-800 flex items-center gap-1">
                          <AlertCircle className="w-3 h-3 text-rose-600" />
                          Missing Must-Haves:
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {item.critical_gaps.map((g) => (
                            <span key={g} className="px-1.5 py-0.5 bg-white border border-rose-200 text-rose-800 rounded text-[10px]">
                              {g}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="pt-1 flex justify-end">
                      <button
                        onClick={() => {
                          onSelectResume(item.resume_id);
                          onClose();
                        }}
                        className="text-[11px] text-indigo-600 hover:text-indigo-800 font-semibold"
                      >
                        Use this resume version →
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

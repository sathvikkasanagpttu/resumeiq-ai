import React, { useState } from "react";
import { CheckCircle2, ArrowRight, Quote, Sparkles, Filter } from "lucide-react";
import { MatchedSkillItem, TransferableSkillItem } from "../../common/types";

interface MatchedSkillsListProps {
  matchedSkills: MatchedSkillItem[];
  transferableSkills: TransferableSkillItem[];
}

export const MatchedSkillsList: React.FC<MatchedSkillsListProps> = ({
  matchedSkills,
  transferableSkills,
}) => {
  const [filter, setFilter] = useState<"all" | "required" | "preferred" | "transferable">("all");
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const filteredMatches = matchedSkills.filter((m) => {
    if (filter === "all") return true;
    if (filter === "required") return m.importance === "required";
    if (filter === "preferred") return m.importance === "preferred";
    return false;
  });

  const showTransferable = filter === "all" || filter === "transferable";

  return (
    <div className="space-y-3">
      {/* Filter Tabs */}
      <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-lg text-xs overflow-x-auto">
        <button
          onClick={() => setFilter("all")}
          className={`px-2.5 py-1 rounded-md font-medium transition-all ${
            filter === "all" ? "bg-white text-indigo-700 shadow-2xs font-semibold" : "text-slate-600 hover:text-slate-900"
          }`}
        >
          All ({matchedSkills.length + transferableSkills.length})
        </button>
        <button
          onClick={() => setFilter("required")}
          className={`px-2.5 py-1 rounded-md font-medium transition-all ${
            filter === "required" ? "bg-white text-indigo-700 shadow-2xs font-semibold" : "text-slate-600 hover:text-slate-900"
          }`}
        >
          Required ({matchedSkills.filter((m) => m.importance === "required").length})
        </button>
        <button
          onClick={() => setFilter("preferred")}
          className={`px-2.5 py-1 rounded-md font-medium transition-all ${
            filter === "preferred" ? "bg-white text-indigo-700 shadow-2xs font-semibold" : "text-slate-600 hover:text-slate-900"
          }`}
        >
          Preferred ({matchedSkills.filter((m) => m.importance === "preferred").length})
        </button>
        {transferableSkills.length > 0 && (
          <button
            onClick={() => setFilter("transferable")}
            className={`px-2.5 py-1 rounded-md font-medium transition-all ${
              filter === "transferable" ? "bg-white text-indigo-700 shadow-2xs font-semibold" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Transferable ({transferableSkills.length})
          </button>
        )}
      </div>

      {/* Direct Matched Skills List */}
      {filter !== "transferable" && (
        <div className="space-y-2">
          {filteredMatches.length === 0 ? (
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-center text-xs text-slate-500">
              No matching skills in this category.
            </div>
          ) : (
            filteredMatches.map((item, idx) => {
              const isExpanded = expandedIndex === idx;
              return (
                <div
                  key={`${item.skill}-${idx}`}
                  className="bg-white border border-slate-200 rounded-xl p-3 shadow-2xs hover:border-slate-300 transition-all space-y-1.5"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span className="font-semibold text-xs text-slate-900 truncate">
                        {item.skill}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <span
                        className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                          item.importance === "required"
                            ? "bg-rose-50 text-rose-700 border border-rose-200"
                            : "bg-indigo-50 text-indigo-700 border border-indigo-200"
                        }`}
                      >
                        {item.importance === "required" ? "Required" : "Bonus"}
                      </span>
                      <span className="text-[10px] font-mono font-medium text-slate-400">
                        {Math.round(item.confidence * 100)}%
                      </span>
                    </div>
                  </div>

                  {item.proof_snippet && (
                    <div
                      onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                      className="cursor-pointer bg-slate-50 hover:bg-slate-100 border border-slate-200/80 rounded-lg p-2 text-[11px] text-slate-600 flex items-start gap-1.5 transition-colors"
                      title="Click to view full proof line"
                    >
                      <Quote className="w-3 h-3 text-indigo-500 shrink-0 mt-0.5" />
                      <p className={`italic ${isExpanded ? "" : "line-clamp-2"}`}>
                        "{item.proof_snippet}"
                      </p>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Transferable Skills Section */}
      {showTransferable && transferableSkills.length > 0 && (
        <div className="space-y-2 pt-2">
          <div className="flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-amber-600" />
            <h5 className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
              Transferable Skills ({transferableSkills.length})
            </h5>
          </div>

          <div className="space-y-2">
            {transferableSkills.map((t, idx) => (
              <div
                key={`trans-${idx}`}
                className="bg-amber-50/50 border border-amber-200/80 rounded-xl p-3 shadow-2xs space-y-1.5"
              >
                <div className="flex items-center justify-between text-xs font-semibold text-slate-900">
                  <div className="flex items-center gap-1.5">
                    <span className="text-amber-800">{t.candidate_skill}</span>
                    <ArrowRight className="w-3 h-3 text-slate-400" />
                    <span className="text-slate-800 font-bold">{t.job_skill}</span>
                  </div>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 bg-amber-100 text-amber-800 rounded font-bold">
                    {Math.round(t.similarity * 100)}% fit
                  </span>
                </div>
                <p className="text-[11px] text-slate-600 leading-snug">
                  {t.reasoning}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

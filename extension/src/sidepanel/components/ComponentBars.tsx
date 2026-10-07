import React, { useState } from "react";
import { ChevronDown, ChevronUp, Layers } from "lucide-react";
import { ComponentScoresBreakdown } from "../../common/types";

interface ComponentBarsProps {
  scores: ComponentScoresBreakdown;
}

interface ComponentItem {
  key: keyof ComponentScoresBreakdown;
  label: string;
  weight: string;
  description: string;
}

const COMPONENTS: ComponentItem[] = [
  { key: "required_skill_coverage", label: "Required Skills", weight: "35%", description: "Direct evidence for mandatory qualifications" },
  { key: "preferred_skill_coverage", label: "Preferred Skills", weight: "15%", description: "Coverage of bonus and nice-to-have skills" },
  { key: "semantic_similarity", label: "Semantic Fit", weight: "15%", description: "Embedding similarity between resume and job context" },
  { key: "evidence_strength", label: "Evidence Strength", weight: "10%", description: "Quality, metrics, and verifiable proof depth" },
  { key: "experience_duration", label: "Experience Duration", weight: "10%", description: "Years of demonstrated hands-on experience" },
  { key: "seniority_alignment", label: "Seniority Alignment", weight: "5%", description: "Alignment with role scope (Lead, Senior, Staff)" },
  { key: "domain_relevance", label: "Domain Relevance", weight: "5%", description: "Industry and product domain background" },
  { key: "education_fit", label: "Education & Certs", weight: "5%", description: "Degrees, academic background, and certifications" },
];

export const ComponentBars: React.FC<ComponentBarsProps> = ({ scores }) => {
  const [showAll, setShowAll] = useState(false);

  // Show top 4 by default, expand to all 8
  const displayedComponents = showAll ? COMPONENTS : COMPONENTS.slice(0, 4);

  const getBarColor = (val: number) => {
    if (val >= 80) return "bg-emerald-500";
    if (val >= 60) return "bg-indigo-500";
    if (val >= 40) return "bg-amber-500";
    return "bg-rose-500";
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-[11px] font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-indigo-600" />
          Component Breakdown (8 Pillars)
        </h4>
        <button
          onClick={() => setShowAll(!showAll)}
          className="text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-0.5"
        >
          {showAll ? (
            <>
              Show Less <ChevronUp className="w-3 h-3" />
            </>
          ) : (
            <>
              Show All 8 <ChevronDown className="w-3 h-3" />
            </>
          )}
        </button>
      </div>

      <div className="space-y-2.5">
        {displayedComponents.map(({ key, label, weight }) => {
          const val = Math.round(scores[key] ?? 0);
          return (
            <div key={key} className="space-y-1">
              <div className="flex justify-between items-center text-xs">
                <span className="font-medium text-slate-700 flex items-center gap-1.5">
                  {label}
                  <span className="text-[10px] text-slate-400 font-normal">({weight})</span>
                </span>
                <span className="font-bold text-slate-800 text-[11px] font-mono">{val}%</span>
              </div>
              <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${getBarColor(val)}`}
                  style={{ width: `${Math.min(100, Math.max(0, val))}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

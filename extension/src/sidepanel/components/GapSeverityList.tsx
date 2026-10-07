import React from "react";
import { AlertCircle, AlertTriangle, Info, Sparkles, Check } from "lucide-react";
import { SkillGapsBreakdown } from "../../common/types";

interface GapSeverityListProps {
  gaps: SkillGapsBreakdown;
  onAutoAddRepresentationGap?: (skill: string) => void;
}

export const GapSeverityList: React.FC<GapSeverityListProps> = ({ gaps }) => {
  const totalGaps =
    gaps.critical.length +
    gaps.moderate.length +
    gaps.minor.length +
    gaps.representation.length;

  if (totalGaps === 0) {
    return (
      <div className="p-6 bg-emerald-50 border border-emerald-200 rounded-xl text-center space-y-2">
        <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-600 mx-auto flex items-center justify-center">
          <Check className="w-5 h-5" />
        </div>
        <h4 className="font-bold text-xs text-emerald-900">Zero Skill Gaps Detected</h4>
        <p className="text-[11px] text-emerald-700">
          Your resume fully covers every required and preferred skill listed in this job post!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* 1. Critical Gaps */}
      {gaps.critical.length > 0 && (
        <div className="bg-white border border-rose-200 rounded-xl p-3.5 shadow-2xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-rose-800 font-bold text-xs">
              <AlertCircle className="w-4 h-4 text-rose-600" />
              <span>Critical Gaps ({gaps.critical.length})</span>
            </div>
            <span className="text-[10px] font-bold px-1.5 py-0.5 bg-rose-50 text-rose-700 rounded border border-rose-200">
              Must-Have
            </span>
          </div>
          <p className="text-[11px] text-slate-500 leading-snug">
            Core requirements not found in your resume. These could cause an ATS filter rejection.
          </p>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {gaps.critical.map((skill) => (
              <span
                key={skill}
                className="px-2 py-1 bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold rounded-md shadow-2xs"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 2. Representation Gaps */}
      {gaps.representation.length > 0 && (
        <div className="bg-indigo-50/70 border border-indigo-200 rounded-xl p-3.5 shadow-2xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-indigo-900 font-bold text-xs">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              <span>Representation Gaps ({gaps.representation.length})</span>
            </div>
            <span className="text-[10px] font-bold px-1.5 py-0.5 bg-indigo-100 text-indigo-800 rounded border border-indigo-200">
              Quick Win
            </span>
          </div>
          <p className="text-[11px] text-slate-600 leading-snug">
            You possess verified evidence for these skills in your Canonical Profile, but they were omitted in this specific resume version!
          </p>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {gaps.representation.map((skill) => (
              <span
                key={skill}
                className="px-2 py-1 bg-white border border-indigo-200 text-indigo-800 text-xs font-semibold rounded-md shadow-2xs flex items-center gap-1"
              >
                <Check className="w-3 h-3 text-emerald-600" />
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 3. Moderate Gaps */}
      {gaps.moderate.length > 0 && (
        <div className="bg-white border border-amber-200 rounded-xl p-3.5 shadow-2xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-amber-800 font-bold text-xs">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>Moderate Gaps ({gaps.moderate.length})</span>
            </div>
            <span className="text-[10px] font-bold px-1.5 py-0.5 bg-amber-50 text-amber-700 rounded border border-amber-200">
              Important
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {gaps.moderate.map((skill) => (
              <span
                key={skill}
                className="px-2 py-1 bg-amber-50 border border-amber-200 text-amber-800 text-xs font-medium rounded-md shadow-2xs"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 4. Minor Gaps */}
      {gaps.minor.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-slate-700 font-bold text-xs">
              <Info className="w-4 h-4 text-slate-500" />
              <span>Minor Gaps ({gaps.minor.length})</span>
            </div>
            <span className="text-[10px] font-medium px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded">
              Preferred
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {gaps.minor.map((skill) => (
              <span
                key={skill}
                className="px-2 py-0.5 bg-slate-50 border border-slate-200 text-slate-600 text-[11px] rounded"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

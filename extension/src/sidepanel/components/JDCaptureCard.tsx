import React, { useState } from "react";
import { Briefcase, Building, MapPin, Globe, Edit3, ChevronDown, ChevronUp, AlertCircle, RefreshCw, Check } from "lucide-react";
import { CapturedJob } from "../../common/types";

interface JDCaptureCardProps {
  job: CapturedJob | null;
  onUpdateJob: (updated: CapturedJob) => void;
  onRefreshFromTab: () => void;
  isLoading: boolean;
}

export const JDCaptureCard: React.FC<JDCaptureCardProps> = ({
  job,
  onUpdateJob,
  onRefreshFromTab,
  isLoading,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(job?.title || "");
  const [editCompany, setEditCompany] = useState(job?.company || "");
  const [editDesc, setEditDesc] = useState(job?.description || "");

  const handleStartEdit = () => {
    setEditTitle(job?.title || "");
    setEditCompany(job?.company || "");
    setEditDesc(job?.description || "");
    setIsEditing(true);
  };

  const handleSaveEdit = () => {
    if (!job) return;
    onUpdateJob({
      ...job,
      title: editTitle.trim() || "Job Opening",
      company: editCompany.trim() || "Company",
      description: editDesc.trim(),
    });
    setIsEditing(false);
  };

  if (!job) {
    return (
      <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-center space-y-3">
        <div className="w-10 h-10 rounded-full bg-slate-200 text-slate-500 mx-auto flex items-center justify-center">
          <Briefcase className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-xs font-semibold text-slate-800">No Job Post Captured Yet</h3>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Open a job post on LinkedIn, Indeed, Naukri, or any career page, or extract from the current tab.
          </p>
        </div>
        <button
          onClick={onRefreshFromTab}
          disabled={isLoading}
          className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded-lg inline-flex items-center gap-1.5 transition-colors shadow-2xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          Capture Active Tab
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs space-y-2.5 transition-all">
      <div className="flex items-start justify-between gap-2">
        <div className="space-y-1 flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 flex items-center gap-1 border border-slate-200">
              <Globe className="w-3 h-3 text-slate-500" />
              {job.source_platform || "Web"}
            </span>
            {job.work_model && (
              <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                {job.work_model}
              </span>
            )}
          </div>

          <h3 className="font-bold text-slate-900 text-sm leading-snug truncate" title={job.title}>
            {job.title}
          </h3>

          <div className="flex items-center gap-3 text-xs text-slate-600">
            <span className="flex items-center gap-1 truncate font-medium">
              <Building className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              {job.company}
            </span>
            {job.location && (
              <span className="flex items-center gap-1 truncate text-slate-500">
                <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                {job.location}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={handleStartEdit}
            title="Edit captured text"
            className="p-1 text-slate-400 hover:text-indigo-600 hover:bg-slate-100 rounded transition-colors"
          >
            <Edit3 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setExpanded(!expanded)}
            title={expanded ? "Collapse details" : "Expand details"}
            className="p-1 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded transition-colors"
          >
            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {isEditing ? (
        <div className="pt-2 border-t border-slate-100 space-y-2 animate-in fade-in">
          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase">Job Title</label>
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="w-full text-xs px-2 py-1 bg-slate-50 border border-slate-200 rounded"
            />
          </div>
          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase">Company</label>
            <input
              type="text"
              value={editCompany}
              onChange={(e) => setEditCompany(e.target.value)}
              className="w-full text-xs px-2 py-1 bg-slate-50 border border-slate-200 rounded"
            />
          </div>
          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase">Job Description Text</label>
            <textarea
              rows={5}
              value={editDesc}
              onChange={(e) => setEditDesc(e.target.value)}
              className="w-full text-xs p-2 bg-slate-50 border border-slate-200 rounded font-sans leading-relaxed resize-y"
            />
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button
              onClick={() => setIsEditing(false)}
              className="px-2.5 py-1 text-xs text-slate-600 hover:bg-slate-100 rounded"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveEdit}
              className="px-3 py-1 text-xs bg-indigo-600 hover:bg-indigo-700 text-white rounded font-medium flex items-center gap-1"
            >
              <Check className="w-3 h-3" />
              Save Changes
            </button>
          </div>
        </div>
      ) : (
        expanded && (
          <div className="pt-2 border-t border-slate-100 text-xs text-slate-700 space-y-2 animate-in fade-in">
            <p className="font-semibold text-slate-500 text-[10px] uppercase tracking-wider">
              Captured Description ({job.description.length} chars)
            </p>
            <div className="max-h-48 overflow-y-auto bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-[11px] leading-relaxed whitespace-pre-line text-slate-600">
              {job.description}
            </div>
          </div>
        )
      )}

      {job.description.length < 150 && (
        <div className="p-2 bg-amber-50 border border-amber-200 rounded text-[11px] text-amber-800 flex items-center gap-1.5">
          <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
          <span>Short description detected. Click edit to paste full JD if needed.</span>
        </div>
      )}
    </div>
  );
};

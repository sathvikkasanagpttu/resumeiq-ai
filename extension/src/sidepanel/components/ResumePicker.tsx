import React, { useRef, useState } from "react";
import { FileText, UploadCloud, ChevronDown, Check, Loader2, Plus } from "lucide-react";
import { ResumeSummary } from "../../common/types";

interface ResumePickerProps {
  resumes: ResumeSummary[];
  selectedResumeId: string | null;
  onSelectResume: (id: string) => void;
  onUploadFile: (file: File) => Promise<void>;
  isUploading: boolean;
}

export const ResumePicker: React.FC<ResumePickerProps> = ({
  resumes,
  selectedResumeId,
  onSelectResume,
  onUploadFile,
  isUploading,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [showUploadZone, setShowUploadZone] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const selectedResume = resumes.find((r) => r.id === selectedResumeId) || resumes[0];

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await onUploadFile(file);
      setShowUploadZone(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      await onUploadFile(file);
      setShowUploadZone(false);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-[11px] font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
          <FileText className="w-3.5 h-3.5 text-indigo-600" />
          Active Resume Version
        </label>
        <button
          onClick={() => setShowUploadZone(!showUploadZone)}
          className="text-[11px] text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-0.5"
        >
          <Plus className="w-3 h-3" />
          Upload New
        </button>
      </div>

      {showUploadZone && (
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-indigo-200 hover:border-indigo-400 bg-indigo-50/50 hover:bg-indigo-50 rounded-xl p-4 text-center cursor-pointer transition-all animate-in fade-in"
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,.docx,.txt"
            className="hidden"
          />
          {isUploading ? (
            <div className="flex flex-col items-center justify-center space-y-1.5">
              <Loader2 className="w-6 h-6 text-indigo-600 animate-spin" />
              <p className="text-xs font-semibold text-slate-800">
                Parsing Canonical Profile...
              </p>
              <p className="text-[10px] text-slate-500">
                Extracting structured facts & evidence graph
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center space-y-1">
              <UploadCloud className="w-6 h-6 text-indigo-600" />
              <p className="text-xs font-semibold text-slate-800">
                Drop your resume here, or <span className="text-indigo-600 underline">browse</span>
              </p>
              <p className="text-[10px] text-slate-400">PDF, DOCX, or TXT up to 10MB</p>
            </div>
          )}
        </div>
      )}

      {resumes.length === 0 ? (
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-500 text-center">
          No resumes found. Please upload a resume to match.
        </div>
      ) : (
        <div className="relative">
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className="w-full bg-white border border-slate-300 hover:border-slate-400 rounded-lg p-2.5 flex items-center justify-between text-left shadow-2xs transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-7 h-7 rounded bg-indigo-50 border border-indigo-100 text-indigo-600 flex items-center justify-center shrink-0">
                <FileText className="w-4 h-4" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="font-semibold text-xs text-slate-900 truncate">
                    {selectedResume?.title || selectedResume?.filename}
                  </span>
                  <span className="text-[10px] font-bold px-1.5 py-0.2 bg-slate-100 text-slate-600 rounded">
                    v{selectedResume?.version || 1}
                  </span>
                </div>
                <div className="text-[10px] text-slate-500">
                  {selectedResume?.skills_count || 0} skills · {selectedResume?.experience_count || 0} roles
                </div>
              </div>
            </div>
            <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" />
          </button>

          {isOpen && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg z-20 max-h-56 overflow-y-auto divide-y divide-slate-100">
              {resumes.map((resume) => {
                const isSelected = resume.id === selectedResume?.id;
                return (
                  <div
                    key={resume.id}
                    onClick={() => {
                      onSelectResume(resume.id);
                      setIsOpen(false);
                    }}
                    className={`p-2.5 flex items-center justify-between cursor-pointer transition-colors ${
                      isSelected ? "bg-indigo-50/70" : "hover:bg-slate-50"
                    }`}
                  >
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="font-medium text-xs text-slate-900 truncate">
                          {resume.title || resume.filename}
                        </span>
                        <span className="text-[9px] font-bold px-1.5 py-0.2 bg-slate-100 text-slate-600 rounded">
                          v{resume.version}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-500">
                        {resume.skills_count} verified skills
                      </div>
                    </div>
                    {isSelected && <Check className="w-4 h-4 text-indigo-600 shrink-0" />}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import {
  Wand2, FileText, Download, CheckCircle2, AlertCircle, RefreshCw,
  Eye, EyeOff, ShieldCheck, Sparkles, HelpCircle, Layers, ArrowRight,
  Check, X, Edit2, ChevronDown, Award
} from 'lucide-react';
import { api } from '../services/api';
import {
  Resume, ResumeVersion, ResumeDiffItem, BuilderMode, BuilderTemplate,
  GenerateResumeRequest, CanonicalProfile
} from '../types';
import { WizardModal } from '../components/WizardModal';
import { QualityModal } from '../components/QualityModal';

interface ResumeStudioPageProps {
  selectedResumeId: string | null;
  resumes: Resume[];
  onSelectResume: (id: string) => void;
}

export const ResumeStudioPage: React.FC<ResumeStudioPageProps> = ({
  selectedResumeId,
  resumes,
  onSelectResume
}) => {
  // Generation Options
  const [mode, setMode] = useState<BuilderMode>('clean_rebuild');
  const [templateId, setTemplateId] = useState<BuilderTemplate>('modern_minimal');
  const [pageTarget, setPageTarget] = useState<1 | 2>(1);
  const [targetRole, setTargetRole] = useState<string>('');
  const [jobDescription, setJobDescription] = useState<string>('');

  // Versions and State
  const [versions, setVersions] = useState<ResumeVersion[]>([]);
  const [activeVersion, setActiveVersion] = useState<ResumeVersion | null>(null);
  const [loadingVersions, setLoadingVersions] = useState<boolean>(false);
  const [generating, setGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Modals & Display Options
  const [isWizardOpen, setIsWizardOpen] = useState<boolean>(false);
  const [isQualityOpen, setIsQualityOpen] = useState<boolean>(false);
  const [redactPii, setRedactPii] = useState<boolean>(false);
  const [viewMode, setViewMode] = useState<'paper' | 'html'>('paper');
  const [exportingFormat, setExportingFormat] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'diffs' | 'versions'>('diffs');

  // Editing Diff State
  const [editingDiffId, setEditingDiffId] = useState<string | null>(null);
  const [editedDiffText, setEditedDiffText] = useState<string>('');

  useEffect(() => {
    if (selectedResumeId) {
      loadVersions(selectedResumeId);
    }
  }, [selectedResumeId]);

  const loadVersions = async (resumeId: string) => {
    setLoadingVersions(true);
    setError(null);
    try {
      const vList = await api.listResumeVersions(resumeId);
      setVersions(vList);
      if (vList.length > 0) {
        setActiveVersion(vList[0]);
      } else {
        setActiveVersion(null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load resume versions.');
    } finally {
      setLoadingVersions(false);
    }
  };

  const handleGenerate = async () => {
    if (!selectedResumeId) return;
    setGenerating(true);
    setError(null);
    try {
      const payload: GenerateResumeRequest = {
        resume_id: selectedResumeId,
        mode,
        template_id: templateId,
        page_target: pageTarget,
        target_role: targetRole.trim() || undefined,
        job_description_text: jobDescription.trim() || undefined
      };

      const newVersion = await api.generateResumeVersion(payload);
      // Reload versions and set active
      await loadVersions(selectedResumeId);
      setActiveVersion(newVersion);
      setActiveTab('diffs');
    } catch (err: any) {
      setError(err.message || 'Failed to generate resume version.');
    } finally {
      setGenerating(false);
    }
  };

  const handleDiffAction = async (diffId: string, action: 'accept' | 'reject' | 'edit', customText?: string) => {
    try {
      await api.reviewBulletDiff({
        diff_id: diffId,
        action,
        edited_text: customText
      });
      // Refresh current version
      if (activeVersion) {
        const refreshed = await api.getResumeVersion(activeVersion.id);
        setActiveVersion(refreshed);
        setVersions((prev) => prev.map((v) => (v.id === refreshed.id ? refreshed : v)));
      }
      setEditingDiffId(null);
      setEditedDiffText('');
    } catch (err: any) {
      setError(err.message || 'Failed to update bullet modification.');
    }
  };

  const handleExport = async (format: string) => {
    if (!activeVersion) return;
    setExportingFormat(format);
    try {
      await api.downloadResumeExport(activeVersion.id, format, redactPii);
    } catch (err: any) {
      setError(err.message || `Failed to export as ${format.toUpperCase()}`);
    } finally {
      setExportingFormat(null);
    }
  };

  // Helper for rendering profile in paper mode
  const profile: CanonicalProfile | null = activeVersion?.canonical_profile || null;

  return (
    <div className="space-y-6">
      {/* Top Banner & Title */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500/20 to-emerald-500/20 border border-teal-500/40 flex items-center justify-center text-teal-400">
              <Wand2 className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
                Resume Studio v2
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-teal-500/20 text-teal-300 font-mono font-semibold">
                  Auto Builder
                </span>
              </h1>
              <p className="text-xs text-slate-400">
                Evidence-grounded auto resume generation, ATS round-trip validation, and STAR bullet rewriting.
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <button
            onClick={() => setIsWizardOpen(true)}
            disabled={!selectedResumeId}
            className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-semibold text-slate-200 transition-colors flex items-center gap-2"
          >
            <HelpCircle className="w-4 h-4 text-teal-400" />
            <span>Missing-Info Wizard</span>
          </button>

          <button
            onClick={() => setIsQualityOpen(true)}
            disabled={!selectedResumeId}
            className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-semibold text-slate-200 transition-colors flex items-center gap-2"
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Quality & Gap Audit</span>
          </button>
        </div>
      </div>

      {/* Resume Selector & Core Configuration Bar */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
          {/* Active Resume Selector */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Candidate Resume
            </label>
            <select
              value={selectedResumeId || ''}
              onChange={(e) => onSelectResume(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-teal-500"
            >
              {resumes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.filename} ({r.skills_count} skills, {r.experience_count} roles)
                </option>
              ))}
            </select>
          </div>

          {/* Builder Mode Selector */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Generation Mode
            </label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value as BuilderMode)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-teal-500"
            >
              <option value="clean_rebuild">Clean Rebuild (Polish & Structure)</option>
              <option value="role_targeted">Role-Targeted (Tailor to JD)</option>
              <option value="fresher">Fresher / Student (Spotlight Education)</option>
              <option value="experienced">Experienced (Leadership & Metrics)</option>
            </select>
          </div>

          {/* Template Selector */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
              ATS-Safe Template
            </label>
            <select
              value={templateId}
              onChange={(e) => setTemplateId(e.target.value as BuilderTemplate)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-teal-500"
            >
              <option value="modern_minimal">Modern Minimalist (Clean Sans)</option>
              <option value="classic">Classic Professional (Serif Standard)</option>
              <option value="compact">Compact Dense (High Data Density)</option>
              <option value="fresher">Fresher Spotlight (Education & Skills)</option>
            </select>
          </div>

          {/* Length & Generate Button */}
          <div className="flex items-end gap-2">
            <div className="w-24">
              <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Pages
              </label>
              <select
                value={pageTarget}
                onChange={(e) => setPageTarget(Number(e.target.value) as 1 | 2)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-teal-500"
              >
                <option value={1}>1 Page</option>
                <option value={2}>2 Pages</option>
              </select>
            </div>

            <button
              onClick={handleGenerate}
              disabled={generating || !selectedResumeId}
              className="flex-1 px-4 py-2 bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-400 hover:to-emerald-500 disabled:opacity-50 text-white font-semibold text-xs rounded-xl shadow-lg shadow-teal-500/20 transition-all flex items-center justify-center gap-2 h-[38px]"
            >
              {generating ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Building...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Build Resume</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Role-targeted inputs if active */}
        {mode === 'role_targeted' && (
          <div className="pt-3 border-t border-slate-800/80 grid grid-cols-1 md:grid-cols-3 gap-3 animate-in fade-in duration-200">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Target Role / Title:
              </label>
              <input
                type="text"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                placeholder="e.g. Senior Backend Engineer"
                className="w-full px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Job Description Text (Optional, for targeted keyword ranking):
              </label>
              <input
                type="text"
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste key JD responsibilities or requirements..."
                className="w-full px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500"
              />
            </div>
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-400 hover:text-rose-200">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Studio Split Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Control Column: Diffs & Versions (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Version Header Card */}
          {activeVersion && (
            <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-teal-500/20 text-teal-300 font-bold">
                    Version #{activeVersion.version_num}
                  </span>
                  <span className="ml-2 text-xs text-slate-400 capitalize">
                    {activeVersion.mode.replace(/_/g, ' ')} ({activeVersion.template_id})
                  </span>
                </div>

                {/* ATS Round-Trip Score Badge */}
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-950/80 border border-emerald-800 text-emerald-300 text-[11px] font-semibold">
                  <Award className="w-3.5 h-3.5 text-emerald-400" />
                  <span>
                    ATS Loss: {activeVersion.ats_loss_score.toFixed(1)}% (
                    {Math.round((1 - activeVersion.ats_loss_score) * 100)}% Retained)
                  </span>
                </div>
              </div>

              {activeVersion.change_summary && (
                <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/60">
                  {activeVersion.change_summary}
                </p>
              )}
            </div>
          )}

          {/* Tab buttons for Left Panel */}
          <div className="flex border-b border-slate-800 bg-slate-900/60 rounded-xl p-1 gap-1">
            <button
              onClick={() => setActiveTab('diffs')}
              className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all flex items-center justify-center gap-2 ${
                activeTab === 'diffs'
                  ? 'bg-slate-800 text-teal-400 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>Bullet Diffs</span>
              {activeVersion && (
                <span className="px-1.5 py-0.2 rounded-full bg-slate-700 text-slate-300 text-[10px] font-mono">
                  {activeVersion.diffs.length}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('versions')}
              className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all flex items-center justify-center gap-2 ${
                activeTab === 'versions'
                  ? 'bg-slate-800 text-teal-400 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>Version History</span>
              <span className="px-1.5 py-0.2 rounded-full bg-slate-700 text-slate-300 text-[10px] font-mono">
                {versions.length}
              </span>
            </button>
          </div>

          {/* Tab 1: Diffs Review Drawer */}
          {activeTab === 'diffs' && (
            <div className="space-y-3">
              {!activeVersion ? (
                <div className="p-8 text-center bg-slate-900/60 rounded-2xl border border-slate-800 text-xs text-slate-400 space-y-2">
                  <Sparkles className="w-8 h-8 text-teal-500 mx-auto opacity-60" />
                  <p>Click "Build Resume" to generate your first verified resume version.</p>
                </div>
              ) : activeVersion.diffs.length === 0 ? (
                <div className="p-8 text-center bg-slate-900/60 rounded-2xl border border-slate-800 text-xs text-slate-400 space-y-2">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
                  <p>All bullet points match your verified profile with zero outstanding diffs.</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
                  {activeVersion.diffs.map((diff: ResumeDiffItem) => (
                    <div
                      key={diff.id}
                      className={`p-4 rounded-xl border text-xs space-y-2.5 transition-all ${
                        diff.status === 'accepted'
                          ? 'bg-emerald-950/20 border-emerald-900/40'
                          : diff.status === 'rejected'
                          ? 'bg-rose-950/20 border-rose-900/40 opacity-70'
                          : 'bg-slate-900 border-slate-800'
                      }`}
                    >
                      {/* Diff Header */}
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-[10px] text-slate-500 uppercase">
                          {diff.field_path}
                        </span>
                        <div className="flex items-center gap-1.5">
                          {diff.risk_flag && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-950 text-amber-400 border border-amber-800">
                              {diff.risk_flag}
                            </span>
                          )}
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono ${
                              diff.status === 'accepted'
                                ? 'bg-emerald-900 text-emerald-300'
                                : diff.status === 'rejected'
                                ? 'bg-rose-900 text-rose-300'
                                : 'bg-slate-800 text-slate-300'
                            }`}
                          >
                            {diff.status}
                          </span>
                        </div>
                      </div>

                      {/* Original vs Proposed */}
                      {diff.original_text && (
                        <div className="space-y-1">
                          <span className="text-[10px] text-slate-500 uppercase font-semibold">Original:</span>
                          <p className="line-through text-slate-500 bg-slate-950/40 p-2 rounded border border-slate-800/40 font-serif">
                            {diff.original_text}
                          </p>
                        </div>
                      )}

                      <div className="space-y-1">
                        <span className="text-[10px] text-teal-400 uppercase font-semibold">
                          Proposed (STAR Formatted):
                        </span>
                        {editingDiffId === diff.id ? (
                          <div className="space-y-2">
                            <textarea
                              rows={3}
                              value={editedDiffText}
                              onChange={(e) => setEditedDiffText(e.target.value)}
                              className="w-full p-2 bg-slate-950 border border-teal-500 rounded text-xs text-slate-200"
                            />
                            <div className="flex justify-end gap-2">
                              <button
                                onClick={() => setEditingDiffId(null)}
                                className="px-2 py-1 text-[10px] text-slate-400 hover:text-slate-200"
                              >
                                Cancel
                              </button>
                              <button
                                onClick={() => handleDiffAction(diff.id, 'edit', editedDiffText)}
                                className="px-2.5 py-1 text-[10px] rounded bg-teal-600 text-white font-semibold"
                              >
                                Save Edit
                              </button>
                            </div>
                          </div>
                        ) : (
                          <p className="text-slate-200 bg-teal-950/20 p-2 rounded border border-teal-900/40 font-serif leading-relaxed">
                            {diff.edited_text || diff.proposed_text}
                          </p>
                        )}
                      </div>

                      {diff.change_reason && (
                        <p className="text-[11px] text-slate-400 italic">
                          Reason: {diff.change_reason}
                        </p>
                      )}

                      {/* Action buttons */}
                      {editingDiffId !== diff.id && (
                        <div className="flex items-center justify-end gap-2 pt-1 border-t border-slate-800/60">
                          <button
                            onClick={() => {
                              setEditingDiffId(diff.id);
                              setEditedDiffText(diff.edited_text || diff.proposed_text);
                            }}
                            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium flex items-center gap-1 transition-colors"
                          >
                            <Edit2 className="w-3 h-3" /> Edit
                          </button>
                          <button
                            onClick={() => handleDiffAction(diff.id, 'reject')}
                            disabled={diff.status === 'rejected'}
                            className="px-2.5 py-1 rounded bg-rose-950/60 hover:bg-rose-900 border border-rose-800/80 text-rose-300 text-[11px] font-medium flex items-center gap-1 transition-colors disabled:opacity-40"
                          >
                            <X className="w-3 h-3" /> Revert
                          </button>
                          <button
                            onClick={() => handleDiffAction(diff.id, 'accept')}
                            disabled={diff.status === 'accepted'}
                            className="px-2.5 py-1 rounded bg-emerald-950/60 hover:bg-emerald-900 border border-emerald-800/80 text-emerald-300 text-[11px] font-medium flex items-center gap-1 transition-colors disabled:opacity-40"
                          >
                            <Check className="w-3 h-3" /> Accept
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tab 2: Version History */}
          {activeTab === 'versions' && (
            <div className="space-y-3">
              {versions.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-400">No versions generated yet.</div>
              ) : (
                versions.map((ver) => (
                  <button
                    key={ver.id}
                    onClick={() => setActiveVersion(ver)}
                    className={`w-full text-left p-3.5 rounded-xl border transition-all ${
                      activeVersion?.id === ver.id
                        ? 'bg-slate-800/90 border-teal-500/50 shadow-sm'
                        : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-xs text-slate-200">
                        Version #{ver.version_num}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {ver.created_at ? new Date(ver.created_at).toLocaleDateString() : 'Recent'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                      <span className="capitalize">{ver.mode.replace(/_/g, ' ')} • {ver.template_id}</span>
                      <span className="text-emerald-400 font-mono">
                        ATS {Math.round((1 - ver.ats_loss_score) * 100)}%
                      </span>
                    </div>
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        {/* Right Preview Column: Paper / HTML View & Exporters (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Action & Toggle Toolbar */}
          <div className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-900 border border-slate-800 flex-wrap gap-3">
            {/* Left toolbar items */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setRedactPii(!redactPii)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all flex items-center gap-1.5 ${
                  redactPii
                    ? 'bg-teal-500/20 text-teal-300 border-teal-500/40'
                    : 'bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700'
                }`}
              >
                {redactPii ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                <span>Blind Screening {redactPii ? '(Redacted)' : '(Full PII)'}</span>
              </button>

              <div className="h-4 w-px bg-slate-800" />

              <button
                onClick={() => setViewMode(viewMode === 'paper' ? 'html' : 'paper')}
                className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-950 text-slate-400 border border-slate-800 hover:border-slate-700 transition-colors flex items-center gap-1.5"
              >
                <Layers className="w-3.5 h-3.5" />
                <span>{viewMode === 'paper' ? 'View Semantic HTML' : 'View Paper Preview'}</span>
              </button>
            </div>

            {/* Right Export Buttons */}
            <div className="flex items-center gap-1.5 flex-wrap">
              {(['pdf', 'docx', 'txt', 'json'] as const).map((fmt) => (
                <button
                  key={fmt}
                  onClick={() => handleExport(fmt)}
                  disabled={!activeVersion || exportingFormat !== null}
                  className="px-2.5 py-1.5 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-[11px] font-bold uppercase font-mono text-slate-300 hover:text-white transition-colors flex items-center gap-1 disabled:opacity-50"
                >
                  {exportingFormat === fmt ? (
                    <RefreshCw className="w-3 h-3 animate-spin" />
                  ) : (
                    <Download className="w-3 h-3 text-teal-400" />
                  )}
                  <span>{fmt}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Paper View Container */}
          <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6 overflow-hidden shadow-2xl min-h-[700px]">
            {!activeVersion || !profile ? (
              <div className="flex flex-col items-center justify-center h-[500px] text-slate-500 space-y-3">
                <FileText className="w-12 h-12 stroke-[1.5] text-slate-600" />
                <p className="text-sm font-medium">Select a resume and click "Build Resume" to preview.</p>
              </div>
            ) : viewMode === 'html' ? (
              /* Semantic HTML Preview */
              <div className="p-4 bg-slate-900 rounded-xl border border-slate-800 overflow-x-auto font-mono text-xs text-slate-300 max-h-[700px] overflow-y-auto">
                <pre>{activeVersion.rendered_html || 'No raw HTML rendered.'}</pre>
              </div>
            ) : (
              /* Authentic Paper Preview */
              <div className="bg-white text-slate-900 p-8 md:p-12 rounded-xl shadow-inner max-w-3xl mx-auto font-sans leading-relaxed selection:bg-teal-100 selection:text-teal-900">
                {/* Header Basics */}
                <div className="text-center pb-5 border-b border-slate-200">
                  <h1 className="text-2xl font-bold tracking-tight text-slate-900 uppercase">
                    {redactPii ? '[REDACTED CANDIDATE]' : profile.basics.name}
                  </h1>
                  {profile.basics.headline && (
                    <div className="text-sm font-medium text-slate-600 mt-1">
                      {profile.basics.headline}
                    </div>
                  )}
                  <div className="flex items-center justify-center gap-3 text-xs text-slate-500 mt-2 flex-wrap">
                    {!redactPii && profile.basics.email && <span>{profile.basics.email}</span>}
                    {!redactPii && profile.basics.phone && <span>• {profile.basics.phone}</span>}
                    {profile.basics.location && <span>• {redactPii ? '[REDACTED LOCATION]' : profile.basics.location}</span>}
                    {profile.basics.links?.map((lnk, i) => (
                      <span key={i}>
                        • <span className="text-teal-700 underline">{lnk.label}</span>
                      </span>
                    ))}
                  </div>
                </div>

                {/* Professional Summary */}
                {profile.basics.summary && (
                  <div className="pt-4 pb-3 border-b border-slate-100">
                    <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-1.5 font-mono">
                      Professional Summary
                    </h2>
                    <p className="text-xs text-slate-700 leading-normal">
                      {profile.basics.summary}
                    </p>
                  </div>
                )}

                {/* Skills */}
                {profile.skills && profile.skills.length > 0 && (
                  <div className="py-4 border-b border-slate-100">
                    <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-2 font-mono">
                      Technical Skills & Competencies
                    </h2>
                    <div className="flex flex-wrap gap-1.5">
                      {profile.skills.map((sk, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-800 border border-slate-200"
                        >
                          {sk.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Experience */}
                {profile.experience && profile.experience.length > 0 && (
                  <div className="py-4 border-b border-slate-100">
                    <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-3 font-mono">
                      Professional Experience
                    </h2>
                    <div className="space-y-4">
                      {profile.experience.map((exp) => (
                        <div key={exp.id} className="text-xs space-y-1">
                          <div className="flex items-center justify-between font-bold text-slate-900">
                            <span>{exp.role}</span>
                            <span className="text-slate-500 font-normal">
                              {exp.start_date || 'Past'} — {exp.is_current ? 'Present' : exp.end_date || 'Past'}
                            </span>
                          </div>
                          <div className="text-slate-600 font-medium italic">
                            {exp.company} {exp.location && `• ${exp.location}`}
                          </div>
                          {exp.bullets && exp.bullets.length > 0 && (
                            <ul className="list-disc list-inside space-y-1 text-slate-700 pt-1">
                              {exp.bullets.map((b, bIdx) => (
                                <li key={bIdx} className="leading-snug">
                                  {b.text}
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Projects */}
                {profile.projects && profile.projects.length > 0 && (
                  <div className="py-4 border-b border-slate-100">
                    <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-3 font-mono">
                      Key Technical Projects
                    </h2>
                    <div className="space-y-3">
                      {profile.projects.map((proj) => (
                        <div key={proj.id} className="text-xs space-y-1">
                          <div className="flex items-center justify-between font-bold text-slate-900">
                            <span>{proj.name}</span>
                            {proj.role && <span className="text-slate-500 font-normal">{proj.role}</span>}
                          </div>
                          {proj.description && <p className="text-slate-600">{proj.description}</p>}
                          {proj.bullets && proj.bullets.length > 0 && (
                            <ul className="list-disc list-inside space-y-1 text-slate-700 pt-0.5">
                              {proj.bullets.map((b, bIdx) => (
                                <li key={bIdx} className="leading-snug">
                                  {b.text}
                                </li>
                              ))}
                            </ul>
                          )}
                          {proj.technologies && proj.technologies.length > 0 && (
                            <div className="text-[11px] text-slate-500 pt-0.5">
                              <span className="font-semibold">Tools:</span> {proj.technologies.join(', ')}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Education */}
                {profile.education && profile.education.length > 0 && (
                  <div className="py-4">
                    <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-2 font-mono">
                      Education & Credentials
                    </h2>
                    <div className="space-y-2">
                      {profile.education.map((edu) => (
                        <div key={edu.id} className="text-xs flex items-center justify-between">
                          <div>
                            <span className="font-bold text-slate-900">{edu.degree}</span>{' '}
                            {edu.field_of_study && <span>in {edu.field_of_study}</span>}
                            <div className="text-slate-600 italic">{edu.institution}</div>
                          </div>
                          <div className="text-slate-500">
                            {edu.end_date || edu.start_date || 'Completed'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      {selectedResumeId && (
        <>
          <WizardModal
            isOpen={isWizardOpen}
            onClose={() => setIsWizardOpen(false)}
            resumeId={selectedResumeId}
            onAnswersSubmitted={() => {
              // Trigger a reload of versions or quality
              loadVersions(selectedResumeId);
            }}
          />
          <QualityModal
            isOpen={isQualityOpen}
            onClose={() => setIsQualityOpen(false)}
            resumeId={selectedResumeId}
            onOpenWizard={() => setIsWizardOpen(true)}
          />
        </>
      )}
    </div>
  );
};
export default ResumeStudioPage;

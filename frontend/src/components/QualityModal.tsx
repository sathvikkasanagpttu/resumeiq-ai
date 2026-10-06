import React, { useState, useEffect } from 'react';
import {
  X, ShieldCheck, AlertTriangle, AlertCircle, CheckCircle2,
  Calendar, Layers, Sparkles, DownloadCloud, ArrowUpRight, Check
} from 'lucide-react';
import { api } from '../services/api';
import { ResumeQualityReport, QualityComponentScore, ExternalImportResponse } from '../types';

interface QualityModalProps {
  isOpen: boolean;
  onClose: () => void;
  resumeId: string;
  onOpenWizard?: () => void;
}

export const QualityModal: React.FC<QualityModalProps> = ({
  isOpen,
  onClose,
  resumeId,
  onOpenWizard
}) => {
  const [activeTab, setActiveTab] = useState<'components' | 'timeline' | 'representation' | 'import'>('components');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ResumeQualityReport | null>(null);

  // External Import state
  const [importPlatform, setImportPlatform] = useState<'linkedin' | 'github'>('linkedin');
  const [importText, setImportText] = useState<string>('');
  const [importing, setImporting] = useState<boolean>(false);
  const [importSuccess, setImportSuccess] = useState<string | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && resumeId) {
      loadReport();
    }
  }, [isOpen, resumeId]);

  const loadReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getQualityReport(resumeId);
      setReport(res);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch resume quality report.');
    } finally {
      setLoading(false);
    }
  };

  const handleImportSubmit = async () => {
    if (!importText.trim()) {
      setImportError('Please paste your profile or repository text to import.');
      return;
    }
    setImporting(true);
    setImportError(null);
    setImportSuccess(null);
    try {
      const res: ExternalImportResponse = await api.importExternalProfile({
        resume_id: resumeId,
        platform: importPlatform,
        raw_text: importText
      });
      setImportSuccess(res.message);
      setImportText('');
      // Reload quality report
      await loadReport();
    } catch (err: any) {
      setImportError(err.message || 'Failed to import external profile.');
    } finally {
      setImporting(false);
    }
  };

  if (!isOpen) return null;

  const getTierColor = (tier: string) => {
    if (tier === 'Job-Ready') return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
    if (tier === 'Minor Edits Needed') return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
    return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-emerald-400';
    if (score >= 65) return 'text-teal-400';
    if (score >= 50) return 'text-amber-400';
    return 'text-rose-400';
  };

  const getSeverityBadge = (severity: string) => {
    if (severity === 'critical') {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-rose-950/80 text-rose-400 border border-rose-800">
          Critical
        </span>
      );
    }
    if (severity === 'warning') {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-950/80 text-amber-400 border border-amber-800">
          Warning
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-800 text-slate-400 border border-slate-700">
        Suggestion
      </span>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="text-lg font-bold text-slate-100">Resume Quality & Gap Audit</h2>
                {report && (
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${getTierColor(report.readiness_tier)}`}>
                    {report.readiness_tier}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400">
                8-pillar quality evaluation, timeline consistency checks, and representation gap detection.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {report && (
              <div className="text-right">
                <div className={`text-2xl font-bold font-mono ${getScoreColor(report.overall_quality_score)}`}>
                  {Math.round(report.overall_quality_score)}
                  <span className="text-xs text-slate-500 font-sans">/100</span>
                </div>
                <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                  Overall Score
                </div>
              </div>
            )}
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 bg-slate-950/40 px-6 gap-2">
          <button
            onClick={() => setActiveTab('components')}
            className={`py-3 px-3.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'components'
                ? 'border-teal-500 text-teal-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            8 Quality Pillars
          </button>
          <button
            onClick={() => setActiveTab('timeline')}
            className={`py-3 px-3.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'timeline'
                ? 'border-teal-500 text-teal-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Calendar className="w-3.5 h-3.5" />
            Timeline & Dates
            {report && report.timeline_analysis.anomalies.length > 0 && (
              <span className="w-4 h-4 rounded-full bg-amber-500/20 text-amber-300 text-[10px] flex items-center justify-center font-mono">
                {report.timeline_analysis.anomalies.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('representation')}
            className={`py-3 px-3.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'representation'
                ? 'border-teal-500 text-teal-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            Representation Gaps
            {report && report.representation_gaps.length > 0 && (
              <span className="w-4 h-4 rounded-full bg-teal-500/20 text-teal-300 text-[10px] flex items-center justify-center font-mono">
                {report.representation_gaps.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('import')}
            className={`py-3 px-3.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'import'
                ? 'border-teal-500 text-teal-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <DownloadCloud className="w-3.5 h-3.5" />
            External Importer (LinkedIn/GitHub)
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-400 space-y-3">
              <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-sm">Evaluating resume quality dimensions...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div className="text-xs">{error}</div>
            </div>
          ) : !report ? null : (
            <>
              {/* Tab 1: 8 Components */}
              {activeTab === 'components' && (
                <div className="space-y-4">
                  {/* Top Recommendations */}
                  {report.top_recommendations.length > 0 && (
                    <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-teal-400 flex items-center gap-2">
                        <Sparkles className="w-3.5 h-3.5" /> Top Quality Recommendations
                      </h4>
                      <ul className="space-y-1.5 text-xs text-slate-300 list-disc list-inside">
                        {report.top_recommendations.map((rec, i) => (
                          <li key={i}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {report.components.map((c: QualityComponentScore) => (
                      <div
                        key={c.name}
                        className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition-colors space-y-3"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                              {c.name.replace(/_/g, ' ')}
                            </span>
                            <span className="ml-2 text-[10px] text-slate-500 font-mono">
                              ({Math.round(c.weight * 100)}% wt)
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-[11px] font-semibold text-slate-400">{c.grade}</span>
                            <span className={`text-base font-bold font-mono ${getScoreColor(c.score)}`}>
                              {Math.round(c.score)}%
                            </span>
                          </div>
                        </div>

                        {/* Bar */}
                        <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-300 ${
                              c.score >= 80 ? 'bg-emerald-500' : c.score >= 60 ? 'bg-teal-500' : 'bg-amber-500'
                            }`}
                            style={{ width: `${Math.min(100, Math.max(0, c.score))}%` }}
                          />
                        </div>

                        <p className="text-[11px] text-slate-400 leading-relaxed">{c.explanation}</p>

                        {/* Issues */}
                        {c.issues.length > 0 && (
                          <div className="space-y-2 pt-1 border-t border-slate-800/60">
                            {c.issues.map((iss, idx) => (
                              <div
                                key={idx}
                                className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800/80 text-[11px] space-y-1"
                              >
                                <div className="flex items-center justify-between gap-2">
                                  <span className="font-medium text-slate-200">{iss.message}</span>
                                  {getSeverityBadge(iss.severity)}
                                </div>
                                {iss.line_text && (
                                  <div className="text-slate-400 font-mono text-[10px] bg-slate-950/60 p-1.5 rounded border border-slate-800/40">
                                    "{iss.line_text}"
                                  </div>
                                )}
                                {iss.suggested_fix && (
                                  <div className="text-teal-400 text-[10px]">
                                    <span className="font-semibold">Fix:</span> {iss.suggested_fix}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 2: Timeline Analysis */}
              {activeTab === 'timeline' && (
                <div className="space-y-5">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-center">
                      <div className="text-2xl font-bold font-mono text-teal-400">
                        {report.timeline_analysis.total_career_years.toFixed(1)}
                      </div>
                      <div className="text-xs text-slate-400 uppercase font-semibold mt-1">
                        Total Career Years
                      </div>
                    </div>
                    <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-center">
                      <div className="text-2xl font-bold font-mono text-teal-400">
                        {report.timeline_analysis.total_career_months}
                      </div>
                      <div className="text-xs text-slate-400 uppercase font-semibold mt-1">
                        Total Career Months
                      </div>
                    </div>
                    <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-center">
                      <div
                        className={`text-2xl font-bold font-mono ${
                          report.timeline_analysis.has_critical_inconsistency
                            ? 'text-rose-400'
                            : 'text-emerald-400'
                        }`}
                      >
                        {report.timeline_analysis.anomalies.length}
                      </div>
                      <div className="text-xs text-slate-400 uppercase font-semibold mt-1">
                        Timeline Anomalies
                      </div>
                    </div>
                  </div>

                  {report.timeline_analysis.anomalies.length === 0 ? (
                    <div className="p-8 text-center bg-slate-950/40 rounded-xl border border-slate-800 space-y-2">
                      <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
                      <h4 className="text-sm font-semibold text-slate-200">Timeline Is Clean & Consistent</h4>
                      <p className="text-xs text-slate-400">
                        No chronologically contradictory roles, unexplained gaps, or overlapping dates detected.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                        Detected Timeline Inconsistencies
                      </h4>
                      {report.timeline_analysis.anomalies.map((ano, idx) => (
                        <div
                          key={idx}
                          className="p-4 rounded-xl bg-slate-950/80 border border-amber-900/40 text-xs space-y-2"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-slate-200 flex items-center gap-2">
                              <AlertTriangle className="w-4 h-4 text-amber-400" />
                              {ano.company_or_entity} ({ano.dates})
                            </span>
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-950 text-amber-400 border border-amber-800">
                              {ano.anomaly_type.replace(/_/g, ' ')}
                            </span>
                          </div>
                          <p className="text-slate-400">{ano.description}</p>
                          <div className="p-2 rounded bg-slate-900/80 border border-slate-800 text-teal-400 text-[11px]">
                            <span className="font-semibold text-slate-300">Remediation:</span> {ano.remediation_hint}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Tab 3: Representation Gaps */}
              {activeTab === 'representation' && (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-teal-950/20 border border-teal-800/40 text-xs text-slate-300 leading-relaxed">
                    <p>
                      <strong>What is a Representation Gap?</strong> When candidate experience or project bullets
                      clearly mention a skill (e.g. built using Docker or FastAPI), but the candidate forgot to list
                      it in their canonical Skills section.
                    </p>
                  </div>

                  {report.representation_gaps.length === 0 ? (
                    <div className="p-8 text-center bg-slate-950/40 rounded-xl border border-slate-800 space-y-2">
                      <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
                      <h4 className="text-sm font-semibold text-slate-200">All Mentioned Skills Represented!</h4>
                      <p className="text-xs text-slate-400">
                        No implied skills or unlisted abilities found in your project or experience descriptions.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                        Unlisted Skills Found In Your Experience Text
                      </h4>
                      {report.representation_gaps.map((gap, idx) => (
                        <div
                          key={idx}
                          className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2.5"
                        >
                          <div className="flex items-center justify-between">
                            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-teal-500/20 text-teal-300 border border-teal-500/30">
                              {gap.implied_skill}
                            </span>
                            <span className="text-[10px] text-slate-500 uppercase font-mono">
                              Found in: {gap.context_section}
                            </span>
                          </div>

                          <div className="text-xs text-slate-300 bg-slate-900 p-2.5 rounded-lg border border-slate-800/60 font-mono text-[11px]">
                            "{gap.trigger_text}"
                          </div>

                          <p className="text-xs text-slate-400">{gap.rationale}</p>

                          <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
                            <span className="text-[11px] text-slate-400 italic">
                              "{gap.suggested_question}"
                            </span>
                            {onOpenWizard && (
                              <button
                                onClick={() => {
                                  onClose();
                                  onOpenWizard();
                                }}
                                className="px-3 py-1 rounded-lg bg-teal-600/80 hover:bg-teal-600 text-white text-xs font-medium transition-colors flex items-center gap-1.5"
                              >
                                Add via Wizard
                                <ArrowUpRight className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Tab 4: External Importer */}
              {activeTab === 'import' && (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-300 space-y-2">
                    <h4 className="font-semibold text-slate-100 flex items-center gap-2">
                      <DownloadCloud className="w-4 h-4 text-teal-400" />
                      External Profile Ingestion
                    </h4>
                    <p className="text-slate-400 leading-relaxed">
                      Paste text from your LinkedIn profile or GitHub README. Our parser extracts verified facts
                      (projects, skills, employment dates) and records them as verified evidence in your profile.
                    </p>
                  </div>

                  {importSuccess && (
                    <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 text-xs flex items-center gap-2">
                      <Check className="w-4 h-4 flex-shrink-0" />
                      <span>{importSuccess}</span>
                    </div>
                  )}

                  {importError && (
                    <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 flex-shrink-0" />
                      <span>{importError}</span>
                    </div>
                  )}

                  <div className="space-y-3">
                    <div className="flex items-center gap-4">
                      <label className="text-xs font-medium text-slate-300">Source Platform:</label>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => setImportPlatform('linkedin')}
                          className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                            importPlatform === 'linkedin'
                              ? 'bg-blue-600/20 text-blue-400 border-blue-500/50'
                              : 'bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700'
                          }`}
                        >
                          LinkedIn
                        </button>
                        <button
                          type="button"
                          onClick={() => setImportPlatform('github')}
                          className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                            importPlatform === 'github'
                              ? 'bg-purple-600/20 text-purple-400 border-purple-500/50'
                              : 'bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700'
                          }`}
                        >
                          GitHub
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">
                        Paste Profile / Repository Text:
                      </label>
                      <textarea
                        rows={6}
                        value={importText}
                        onChange={(e) => setImportText(e.target.value)}
                        placeholder={`Paste text exported or copied from your ${importPlatform} profile...`}
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500 font-mono"
                      />
                    </div>

                    <div className="flex justify-end">
                      <button
                        type="button"
                        onClick={handleImportSubmit}
                        disabled={importing || !importText.trim()}
                        className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white font-semibold text-xs transition-colors shadow-lg shadow-teal-600/20 flex items-center gap-2"
                      >
                        {importing ? (
                          <>
                            <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            <span>Importing & Parsing...</span>
                          </>
                        ) : (
                          <>
                            <DownloadCloud className="w-4 h-4" />
                            <span>Import Profile Facts</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-800 bg-slate-900/60">
          <div className="text-xs text-slate-400">
            Powered by RESUMEIQ Evidence & Quality Analyzer
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
          >
            Close Audit
          </button>
        </div>
      </div>
    </div>
  );
};

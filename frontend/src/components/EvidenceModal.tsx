import React, { useEffect, useState } from 'react';
import { X, ShieldCheck, AlertCircle, Quote, Briefcase, FolderGit2, Sparkles, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';
import { EvidenceBadge } from './EvidenceBadge';

interface EvidenceModalProps {
  resumeId: string;
  skillName: string | null;
  onClose: () => void;
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({ resumeId, skillName, onClose }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!skillName || !resumeId) return;

    setLoading(true);
    setError(null);
    api.getSkillEvidence(resumeId, skillName)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to retrieve evidence');
        setLoading(false);
      });
  }, [resumeId, skillName]);

  if (!skillName) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto shadow-2xl flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-start justify-between bg-slate-900/80 sticky top-0 backdrop-blur z-10">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs uppercase tracking-wider font-semibold text-teal-400">Evidence Graph Inspector</span>
              <span className="text-slate-500">•</span>
              <span className="text-xs text-slate-400">Zero-Fabrication Audit</span>
            </div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              Why does ResumeIQ believe candidate has <span className="text-teal-300">"{skillName}"</span> experience?
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 flex-1">
          {loading && (
            <div className="py-12 text-center text-slate-400">
              <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              Verifying evidence graph in candidate factual record...
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <div>{error}</div>
            </div>
          )}

          {!loading && data && (
            <>
              {/* Summary Banner */}
              <div className="p-4 rounded-xl bg-slate-850 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="text-xs text-slate-400 mb-1">Audit Status & Evidence Tier</div>
                  <div className="flex items-center gap-3">
                    <EvidenceBadge strength={data.evidence_strength} size="md" />
                    <span className="text-sm font-semibold text-slate-200">
                      System Confidence: {Math.round((data.confidence || 0) * 100)}%
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-slate-400 mb-1">Status Classification</div>
                  <span className={`text-sm font-mono font-medium ${data.status === 'supported' ? 'text-emerald-400' : 'text-amber-400'}`}>
                    [{data.status.toUpperCase()}]
                  </span>
                </div>
              </div>

              {/* Core Explanation */}
              <div>
                <h3 className="text-xs uppercase tracking-wider font-semibold text-slate-400 mb-2 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-teal-400" />
                  Reasoning & Evidence Synthesis
                </h3>
                <p className="text-sm text-slate-300 bg-slate-950 p-4 rounded-xl border border-slate-800/80 leading-relaxed">
                  {data.explanation}
                </p>
              </div>

              {/* Exact Quotes / Resume Citations */}
              {data.citations && data.citations.length > 0 && (
                <div>
                  <h3 className="text-xs uppercase tracking-wider font-semibold text-slate-400 mb-2 flex items-center gap-2">
                    <Quote className="w-4 h-4 text-teal-400" />
                    Verbatim Resume Evidence Citations ({data.citations.length})
                  </h3>
                  <div className="space-y-3">
                    {data.citations.map((c: any, idx: number) => (
                      <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-sm space-y-2">
                        <div className="flex items-center justify-between text-xs text-slate-400">
                          <span className="font-mono text-teal-400">Section: [{c.section.toUpperCase()}]</span>
                          {c.metric && <span className="text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">Metric: {c.metric}</span>}
                          {c.action_verb && <span className="text-sky-400 bg-sky-950/60 px-2 py-0.5 rounded border border-sky-800">Action: "{c.action_verb}"</span>}
                        </div>
                        <p className="text-slate-200 italic font-mono text-xs border-l-2 border-teal-500 pl-3 py-1">
                          "{c.quote}"
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Associated Roles & Projects */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {data.related_experiences && data.related_experiences.length > 0 && (
                  <div className="p-4 rounded-xl bg-slate-850 border border-slate-800">
                    <h4 className="text-xs font-semibold text-slate-300 mb-2 flex items-center gap-2">
                      <Briefcase className="w-4 h-4 text-teal-400" /> Verified in Employment Roles
                    </h4>
                    <ul className="text-xs space-y-1.5 text-slate-400">
                      {data.related_experiences.map((exp: any, i: number) => (
                        <li key={i} className="flex items-center gap-2">
                          <CheckCircle2 className="w-3.5 h-3.5 text-teal-400 flex-shrink-0" />
                          <span><strong className="text-slate-200">{exp.role}</strong> @ {exp.company}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {data.related_projects && data.related_projects.length > 0 && (
                  <div className="p-4 rounded-xl bg-slate-850 border border-slate-800">
                    <h4 className="text-xs font-semibold text-slate-300 mb-2 flex items-center gap-2">
                      <FolderGit2 className="w-4 h-4 text-teal-400" /> Verified in Projects
                    </h4>
                    <ul className="text-xs space-y-1.5 text-slate-400">
                      {data.related_projects.map((proj: any, i: number) => (
                        <li key={i} className="flex items-center gap-2">
                          <CheckCircle2 className="w-3.5 h-3.5 text-teal-400 flex-shrink-0" />
                          <span className="text-slate-200 font-medium">{proj.title}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/80 flex items-center justify-between text-xs text-slate-500">
          <span>Principle: "Never optimize by inventing candidate experience."</span>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-medium transition"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};

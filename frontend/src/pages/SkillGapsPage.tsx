import React, { useState, useEffect } from 'react';
import {
  AlertTriangle, CheckCircle2, ArrowRight, ShieldAlert, Sparkles,
  RefreshCw, Info, HelpCircle, AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import { SkillGapReport, SkillGap, Match } from '../types';

interface SkillGapsPageProps {
  selectedMatchId?: string | null;
  onNavigateToRoadmap?: () => void;
}

export const SkillGapsPage: React.FC<SkillGapsPageProps> = ({
  selectedMatchId, onNavigateToRoadmap
}) => {
  const [report, setReport] = useState<SkillGapReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'all' | 'critical' | 'representation' | 'moderate' | 'transferable'>('all');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedMatchId) {
      loadGaps(selectedMatchId);
    }
  }, [selectedMatchId]);

  const loadGaps = async (matchId: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getGapReport(matchId);
      setReport(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load skill gaps');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityBadge = (sev: string) => {
    const map: Record<string, { bg: string; text: string; border: string; label: string }> = {
      critical: { bg: 'bg-rose-950/60', text: 'text-rose-400', border: 'border-rose-800', label: 'Critical Gap (Must-Have)' },
      representation: { bg: 'bg-amber-950/60', text: 'text-amber-400', border: 'border-amber-800', label: 'Representation Gap (Weak Phrasing)' },
      moderate: { bg: 'bg-sky-950/60', text: 'text-sky-400', border: 'border-sky-800', label: 'Moderate Gap (Preferred)' },
      minor: { bg: 'bg-slate-900', text: 'text-slate-400', border: 'border-slate-800', label: 'Minor Gap' },
      transferable: { bg: 'bg-teal-950/60', text: 'text-teal-400', border: 'border-teal-800', label: 'Transferable Skill' },
    };
    const c = map[sev] || map.minor;
    return (
      <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${c.bg} ${c.text} ${c.border}`}>
        {c.label}
      </span>
    );
  };

  const filteredGaps = report?.gaps.filter((g) => {
    if (activeTab === 'all') return true;
    return g.gap_severity === activeTab;
  }) || [];

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <AlertTriangle className="w-6 h-6 text-amber-400" /> Evidence-Based Skill Gap Engine
          </h1>
          <p className="text-sm text-slate-400">
            Identifies must-haves, preferred qualifications, and representation gaps where skills exist but lack quantified action evidence.
          </p>
        </div>

        {onNavigateToRoadmap && (
          <button
            onClick={onNavigateToRoadmap}
            className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-teal-600/20 transition flex items-center gap-2"
          >
            <span>View Remediation Roadmap</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Severity Counters */}
      {report && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <button
            onClick={() => setActiveTab('critical')}
            className={`p-5 rounded-2xl border text-left transition ${
              activeTab === 'critical' ? 'bg-rose-950/40 border-rose-800' : 'bg-slate-900 border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="text-xs text-rose-400 font-semibold mb-1">Critical Blockers</div>
            <div className="text-2xl font-bold font-mono text-white">{report.critical_gaps_count}</div>
            <p className="text-[11px] text-slate-400 mt-1">Must-have requirements</p>
          </button>

          <button
            onClick={() => setActiveTab('representation')}
            className={`p-5 rounded-2xl border text-left transition ${
              activeTab === 'representation' ? 'bg-amber-950/40 border-amber-800' : 'bg-slate-900 border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="text-xs text-amber-400 font-semibold mb-1">Representation Gaps</div>
            <div className="text-2xl font-bold font-mono text-white">{report.representation_gaps_count}</div>
            <p className="text-[11px] text-slate-400 mt-1">Listed but missing impact</p>
          </button>

          <button
            onClick={() => setActiveTab('moderate')}
            className={`p-5 rounded-2xl border text-left transition ${
              activeTab === 'moderate' ? 'bg-sky-950/40 border-sky-800' : 'bg-slate-900 border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="text-xs text-sky-400 font-semibold mb-1">Moderate Gaps</div>
            <div className="text-2xl font-bold font-mono text-white">{report.moderate_gaps_count}</div>
            <p className="text-[11px] text-slate-400 mt-1">Preferred qualifications</p>
          </button>

          <button
            onClick={() => setActiveTab('all')}
            className={`p-5 rounded-2xl border text-left transition ${
              activeTab === 'all' ? 'bg-slate-850 border-teal-500/50' : 'bg-slate-900 border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="text-xs text-slate-400 font-semibold mb-1">Total Gap Count</div>
            <div className="text-2xl font-bold font-mono text-teal-400">{report.total_gaps}</div>
            <p className="text-[11px] text-slate-400 mt-1">All audit items</p>
          </button>
        </div>
      )}

      {/* Representation Gap Educational Callout */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex items-start gap-4">
        <div className="p-2.5 rounded-xl bg-amber-950/60 border border-amber-800 text-amber-400 flex-shrink-0">
          <Info className="w-5 h-5" />
        </div>
        <div className="space-y-1 text-xs leading-relaxed">
          <h4 className="font-bold text-white text-sm">Understanding Representation Gaps</h4>
          <p className="text-slate-300">
            A <strong>Representation Gap</strong> occurs when a candidate possesses a skill or includes it in a skills list,
            but the resume fails to demonstrate measurable deliverables or active verbs (e.g. "Built", "Architected", "Optimized 40%").
            Closing representation gaps requires rewriting bullets truthfully to reflect actual impact rather than acquiring a new skill.
          </p>
        </div>
      </div>

      {/* Gaps List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white">
            Gap Diagnostics ({filteredGaps.length})
          </h3>
          <button
            onClick={() => setActiveTab('all')}
            className="text-xs text-slate-400 hover:text-white"
          >
            Reset Filters
          </button>
        </div>

        {filteredGaps.length === 0 ? (
          <div className="p-12 text-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 text-xs text-slate-500">
            No gaps detected in this category. All requirements are verified with strong evidence.
          </div>
        ) : (
          <div className="space-y-4">
            {filteredGaps.map((g, idx) => (
              <div
                key={idx}
                className="p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <span className="text-lg font-bold text-white">{g.skill_name}</span>
                    {getSeverityBadge(g.gap_severity)}
                  </div>
                  <span className="text-xs font-mono text-slate-500">Confidence: {Math.round(g.confidence * 100)}%</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  {/* Explanation */}
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                    <span className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">Gap Analysis</span>
                    <p className="text-slate-300 leading-relaxed">{g.explanation}</p>
                  </div>

                  {/* Recommendation */}
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                    <span className="text-teal-400 font-semibold uppercase tracking-wider text-[10px]">Actionable Remediation</span>
                    <p className="text-slate-300 leading-relaxed">{g.recommendation}</p>
                  </div>
                </div>

                {/* Candidate Evidence State */}
                <div className="text-[11px] text-slate-400 pt-1 flex items-center gap-2">
                  <span className="font-semibold text-slate-500">Candidate Evidence Found:</span>
                  <span className="italic font-mono text-slate-300">{g.candidate_evidence}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

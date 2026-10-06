import React, { useState, useEffect } from 'react';
import {
  Sparkles, CheckCircle2, AlertTriangle, ArrowRight, ShieldCheck,
  TrendingUp, Briefcase, Building2, MapPin, AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import { JobRecommendation, Resume } from '../types';

interface JobRecommendationsPageProps {
  selectedResumeId?: string | null;
  onSelectJob: (jobId: string) => void;
  onNavigateToMatch: () => void;
}

export const JobRecommendationsPage: React.FC<JobRecommendationsPageProps> = ({
  selectedResumeId, onSelectJob, onNavigateToMatch
}) => {
  const [recommendations, setRecommendations] = useState<JobRecommendation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedResumeId) {
      loadRecommendations(selectedResumeId);
    }
  }, [selectedResumeId]);

  const loadRecommendations = async (resumeId: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getJobRecommendations(resumeId);
      setRecommendations(res.recommendations);
    } catch (err: any) {
      setError(err.message || 'Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyStrategy = (jobId: string) => {
    onSelectJob(jobId);
    onNavigateToMatch();
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-teal-400" /> Ranked Job Recommendations
        </h1>
        <p className="text-sm text-slate-400">
          Ranked opportunities evaluated across 8 multi-signal dimensions with explicit risk factors and tactical strategies.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <div className="py-16 text-center text-slate-400">
          <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          Running multi-signal compatibility matching across active positions...
        </div>
      )}

      {!loading && recommendations.length === 0 && (
        <div className="p-16 text-center border-2 border-dashed border-slate-800 rounded-3xl bg-slate-900/40 text-xs text-slate-500">
          No job descriptions active to evaluate. Please ingest jobs in Job Analyzer.
        </div>
      )}

      {/* Recommendations Cards */}
      <div className="space-y-6">
        {recommendations.map((item, idx) => (
          <div
            key={item.job_id}
            className="p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition space-y-6"
          >
            {/* Top Bar */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono text-teal-400 font-bold">Rank #{idx + 1}</span>
                  <span className="text-slate-600">•</span>
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    <Building2 className="w-3.5 h-3.5" /> {item.company}
                  </span>
                  <span className="text-slate-600">•</span>
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5" /> {item.location || 'Remote'} ({item.work_model.toUpperCase()})
                  </span>
                </div>
                <h3 className="text-xl font-bold text-white">{item.title}</h3>
              </div>

              {/* Compatibility Badge */}
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <span className="text-[10px] uppercase font-bold text-slate-500">Compatibility</span>
                  <div className="text-2xl font-black font-mono text-teal-400">
                    {Math.round(item.compatibility_score)}%
                  </div>
                </div>

                <button
                  onClick={() => handleApplyStrategy(item.job_id)}
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-teal-600/20 transition flex items-center gap-1.5"
                >
                  <span>Analyze Match</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Why it matches */}
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 leading-relaxed">
              <strong className="text-teal-400">Match Rationale: </strong>
              {item.why_it_matches}
            </div>

            {/* 4 Pillars Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
              {/* Strong Matches */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="text-[10px] uppercase font-bold text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Strong Matches
                </div>
                <ul className="space-y-1 text-slate-300">
                  {item.strong_matches.map((s, i) => (
                    <li key={i} className="flex items-center gap-1.5">
                      <span className="text-emerald-400">•</span> {s}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Potential Gaps */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="text-[10px] uppercase font-bold text-amber-400 flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5" /> Potential Gaps
                </div>
                <ul className="space-y-1 text-slate-300">
                  {item.potential_gaps.map((g, i) => (
                    <li key={i} className="flex items-center gap-1.5">
                      <span className="text-amber-400">•</span> {g}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Transferable Skills */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="text-[10px] uppercase font-bold text-sky-400 flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5" /> Transferable Skills
                </div>
                <ul className="space-y-1 text-slate-300">
                  {item.transferable_skills.map((t, i) => (
                    <li key={i} className="flex items-center gap-1.5">
                      <span className="text-sky-400">•</span> {t}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Risk Factors */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="text-[10px] uppercase font-bold text-rose-400 flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5" /> Risk Factors
                </div>
                <ul className="space-y-1 text-slate-300">
                  {item.risk_factors.map((r, i) => (
                    <li key={i} className="flex items-center gap-1.5">
                      <span className="text-rose-400">•</span> {r}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Recommended Application Strategy */}
            <div className="text-xs text-slate-400 pt-1 flex items-start gap-2">
              <span className="font-bold text-teal-400 flex-shrink-0">Application Strategy:</span>
              <span className="text-slate-300">{item.recommended_strategy}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import {
  BarChart3, TrendingUp, Users, Globe, ShieldCheck,
  Sparkles, CheckCircle2, AlertCircle, PieChart
} from 'lucide-react';
import { api } from '../services/api';
import { MarketAnalytics } from '../types';

interface MarketAnalyticsPageProps {
  selectedResumeId?: string | null;
}

export const MarketAnalyticsPage: React.FC<MarketAnalyticsPageProps> = ({
  selectedResumeId
}) => {
  const [analytics, setAnalytics] = useState<MarketAnalytics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalytics();
  }, [selectedResumeId]);

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getMarketAnalytics(selectedResumeId || undefined);
      setAnalytics(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load market analytics');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-teal-400" /> Aggregate Job Market Intelligence
        </h1>
        <p className="text-sm text-slate-400">
          Synthesized demand trends across {analytics?.total_jobs_analyzed || 0} job descriptions with candidate profile market benchmarking.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Candidate Benchmark Card */}
      {analytics?.candidate_benchmark && (
        <div className="p-8 rounded-3xl bg-gradient-to-r from-teal-950/40 via-slate-900 to-slate-900 border border-teal-800/80 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <span className="text-xs uppercase font-bold text-teal-400 tracking-wider">Candidate Market Benchmark</span>
            <h2 className="text-2xl font-extrabold text-white">Competitive Market Alignment</h2>
            <p className="text-xs text-slate-300 leading-relaxed">
              {analytics.candidate_benchmark.summary}
            </p>
            <div className="flex flex-wrap gap-2 pt-2">
              <span className="text-xs text-slate-400 font-semibold mr-1 self-center">Possessed Market Skills:</span>
              {analytics.candidate_benchmark.candidate_skills_in_market.map((s, i) => (
                <span key={i} className="text-xs px-2.5 py-1 rounded-lg bg-teal-950 text-teal-300 border border-teal-800 font-mono">
                  {s}
                </span>
              ))}
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-slate-950 border border-slate-800 text-center min-w-[200px]">
            <span className="text-[10px] uppercase font-bold text-slate-500">Market Coverage</span>
            <div className="text-5xl font-black font-mono text-teal-400">
              {analytics.candidate_benchmark.candidate_percentile}%
            </div>
            <span className="text-xs text-slate-400 mt-1 block">In-Demand Skills Met</span>
          </div>
        </div>
      )}

      {analytics && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Top Skills In Demand (8 cols) */}
          <div className="lg:col-span-8 p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-teal-400" /> Most Requested Competencies
              </h3>
              <span className="text-xs text-slate-400">Required vs Preferred Ratio</span>
            </div>

            <div className="space-y-3">
              {analytics.top_skills.map((s, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-white font-mono text-sm">{s.skill_name}</span>
                    <div className="flex items-center gap-3 font-mono">
                      <span className="text-teal-400">{s.percentage}% of roles</span>
                      <span className="text-slate-500">({Math.round(s.required_ratio * 100)}% mandatory)</span>
                    </div>
                  </div>

                  {/* Frequency Bar */}
                  <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-teal-500 h-full rounded-full"
                      style={{ width: `${s.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Seniority & Domain Distributions (4 cols) */}
          <div className="lg:col-span-4 space-y-6">
            {/* Seniority Distribution */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Users className="w-4 h-4 text-sky-400" /> Seniority Tier Demand
              </h3>
              <div className="space-y-3">
                {analytics.seniority_distribution.map((sen, i) => (
                  <div key={i} className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-slate-300 font-medium">{sen.seniority}</span>
                    <div className="flex items-center gap-2 font-mono">
                      <span className="text-white font-bold">{sen.count}</span>
                      <span className="text-slate-500">({sen.percentage}%)</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Domain Distribution */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Globe className="w-4 h-4 text-purple-400" /> Domain & Tech Focus
              </h3>
              <div className="space-y-3">
                {analytics.domain_distribution.map((dom, i) => (
                  <div key={i} className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-slate-300 font-medium">{dom.domain}</span>
                    <div className="flex items-center gap-2 font-mono">
                      <span className="text-white font-bold">{dom.count}</span>
                      <span className="text-slate-500">({dom.percentage}%)</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

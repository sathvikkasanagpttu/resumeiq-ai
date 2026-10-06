import React, { useState, useEffect } from 'react';
import {
  Compass, CheckCircle2, Clock, BookOpen, Hammer,
  FileCheck2, AlertCircle, ArrowRight
} from 'lucide-react';
import { api } from '../services/api';
import { CareerRoadmap } from '../types';

interface CareerRoadmapPageProps {
  selectedMatchId?: string | null;
}

export const CareerRoadmapPage: React.FC<CareerRoadmapPageProps> = ({
  selectedMatchId
}) => {
  const [roadmap, setRoadmap] = useState<CareerRoadmap | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedMatchId) {
      loadRoadmap(selectedMatchId);
    }
  }, [selectedMatchId]);

  const loadRoadmap = async (matchId: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getCareerRoadmap(matchId);
      setRoadmap(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load career roadmap');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <Compass className="w-6 h-6 text-teal-400" /> Evidence-Driven Career Roadmap
          </h1>
          <p className="text-sm text-slate-400">
            A milestone-based upskilling plan that bridges skill gaps by completing verifiable portfolio projects.
          </p>
        </div>

        {roadmap && (
          <div className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 flex items-center gap-2">
            <Clock className="w-4 h-4 text-teal-400" />
            <span>Estimated Timeline: <strong className="text-teal-300 font-mono">{roadmap.estimated_total_weeks} Weeks</strong></span>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Strategy Overview Banner */}
      {roadmap && (
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono text-teal-400 uppercase tracking-wider">
            Target Transition: {roadmap.current_seniority_level} → {roadmap.target_seniority_level} ({roadmap.target_role})
          </div>
          <h3 className="text-lg font-bold text-white">Remediation & Evidence Acquisition Strategy</h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            {roadmap.summary_strategy}
          </p>
        </div>
      )}

      {/* Learning Paths */}
      {roadmap ? (
        <div className="space-y-8">
          {roadmap.learning_paths.map((path, idx) => (
            <div key={idx} className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
              {/* Path Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-2">
                <div>
                  <div className="flex items-center gap-2.5">
                    <span className="text-xl font-bold text-white">{path.skill_name}</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-teal-950 text-teal-400 border border-teal-800">
                      Priority: {path.priority_level.toUpperCase()}
                    </span>
                    {path.transferable_base && (
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800">
                        Transferable from {path.transferable_base}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    Market Demand: {path.job_market_demand.toUpperCase()} • Estimated Effort: {path.effort_estimate_hours} Hours
                  </div>
                </div>
              </div>

              {/* Milestones Flow */}
              <div className="space-y-4">
                {path.milestones.map((m) => (
                  <div
                    key={m.step_number}
                    className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3 relative"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-teal-400 flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-teal-950 border border-teal-800 flex items-center justify-center text-[10px]">
                          {m.step_number}
                        </span>
                        {m.title}
                      </span>
                      <span className="text-slate-500 font-mono">~{m.estimated_weeks} Weeks</span>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed">{m.description}</p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 text-xs">
                      {/* Hands-on project */}
                      <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                        <div className="text-[10px] uppercase font-bold text-sky-400 flex items-center gap-1.5">
                          <Hammer className="w-3.5 h-3.5" /> Hands-on Project Deliverable
                        </div>
                        <p className="text-slate-300 text-[11px]">{m.hands_on_project_to_prove}</p>
                      </div>

                      {/* Verifiable Resume Bullet */}
                      <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                        <div className="text-[10px] uppercase font-bold text-emerald-400 flex items-center gap-1.5">
                          <FileCheck2 className="w-3.5 h-3.5" /> Verifiable Resume Bullet
                        </div>
                        <p className="text-slate-300 text-[11px] italic font-mono">"{m.evidence_to_add_to_resume}"</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-16 text-center border-2 border-dashed border-slate-800 rounded-3xl bg-slate-900/40 text-xs text-slate-500">
          Run or select a compatibility match to generate a prioritized career roadmap.
        </div>
      )}
    </div>
  );
};

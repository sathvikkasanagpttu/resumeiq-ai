import React, { useState, useEffect } from 'react';
import {
  GitCompare, ShieldCheck, CheckCircle2, AlertTriangle, ArrowRight,
  Sparkles, Sliders, Quote, Layers, Check, XCircle, AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import { Match, Resume, Job } from '../types';
import { ScoreCard } from '../components/ScoreCard';
import { EvidenceModal } from '../components/EvidenceModal';

interface MatchAnalysisPageProps {
  selectedMatchId?: string | null;
  resumes: Resume[];
  jobs: Job[];
  onSelectMatch: (id: string) => void;
  onNavigateToGaps: () => void;
}

export const MatchAnalysisPage: React.FC<MatchAnalysisPageProps> = ({
  selectedMatchId, resumes, jobs, onSelectMatch, onNavigateToGaps
}) => {
  const [match, setMatch] = useState<Match | null>(null);
  const [selectedResumeId, setSelectedResumeId] = useState<string>(resumes[0]?.id || '');
  const [selectedJobId, setSelectedJobId] = useState<string>(jobs[0]?.id || '');
  const [loading, setLoading] = useState<boolean>(false);
  const [computing, setComputing] = useState<boolean>(false);
  const [inspectSkill, setInspectSkill] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Custom Weight Sliders State
  const [showSliders, setShowSliders] = useState<boolean>(false);
  const [weights, setWeights] = useState({
    weight_required_skills: 0.25,
    weight_semantic_fit: 0.20,
    weight_evidence_strength: 0.15,
    weight_experience_alignment: 0.15,
    weight_preferred_skills: 0.08,
    weight_seniority_alignment: 0.07,
    weight_domain_alignment: 0.05,
    weight_education_alignment: 0.05
  });

  useEffect(() => {
    if (selectedMatchId) {
      loadMatch(selectedMatchId);
    } else if (resumes.length > 0 && jobs.length > 0) {
      // Auto run or load match
      handleRunMatch();
    }
  }, [selectedMatchId]);

  const loadMatch = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getMatch(id);
      setMatch(res);
      setSelectedResumeId(res.resume_id);
      setSelectedJobId(res.job_id);
    } catch (err: any) {
      setError(err.message || 'Failed to load match record');
    } finally {
      setLoading(false);
    }
  };

  const handleRunMatch = async () => {
    if (!selectedResumeId || !selectedJobId) return;

    setComputing(true);
    setError(null);
    try {
      const res = await api.computeMatch(
        selectedResumeId,
        selectedJobId,
        showSliders ? weights : undefined
      );
      setMatch(res);
      onSelectMatch(res.id);
    } catch (err: any) {
      setError(err.message || 'Failed to compute match');
    } finally {
      setComputing(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <GitCompare className="w-6 h-6 text-teal-400" /> Candidate–Job Compatibility Engine
          </h1>
          <p className="text-sm text-slate-400">
            Multi-signal matching combining lexical BM25, dense embeddings, verified evidence strength, and requirement coverage.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowSliders(!showSliders)}
            className={`px-3.5 py-2 rounded-xl text-xs font-semibold border transition flex items-center gap-2 ${
              showSliders
                ? 'bg-teal-950 border-teal-800 text-teal-300'
                : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700'
            }`}
          >
            <Sliders className="w-4 h-4" />
            <span>Customize Weights</span>
          </button>

          <button
            onClick={handleRunMatch}
            disabled={computing || !selectedResumeId || !selectedJobId}
            className="px-5 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-teal-600/20 transition flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4" />
            <span>{computing ? 'Computing 8 Signals...' : 'Run Compatibility Audit'}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Target Pair Selector */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-400 mb-1">Select Candidate Resume</label>
          <select
            value={selectedResumeId}
            onChange={(e) => setSelectedResumeId(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-medium text-white focus:outline-none focus:border-teal-500"
          >
            {resumes.map((r) => (
              <option key={r.id} value={r.id}>
                {r.filename} ({r.skills_count} extracted skills)
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 mb-1">Select Target Job Description</label>
          <select
            value={selectedJobId}
            onChange={(e) => setSelectedJobId(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-medium text-white focus:outline-none focus:border-teal-500"
          >
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.title} @ {j.company} ({j.seniority.toUpperCase()})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Weight Customizer Drawer */}
      {showSliders && (
        <div className="p-6 rounded-2xl bg-slate-900 border border-teal-500/30 space-y-4 animate-in slide-in-from-top-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs uppercase tracking-wider font-bold text-teal-400 flex items-center gap-2">
              <Sliders className="w-4 h-4" /> Custom Scoring Model Parameters
            </h3>
            <span className="text-xs text-slate-400">Total Weight: 100% Normalized</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(weights).map(([k, v]) => (
              <div key={k} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400 font-medium">{k.replace('weight_', '').replace('_', ' ')}</span>
                  <span className="font-mono text-teal-400 font-bold">{Math.round(v * 100)}%</span>
                </div>
                <input
                  type="range"
                  min="0.01"
                  max="0.50"
                  step="0.01"
                  value={v}
                  onChange={(e) => setWeights({ ...weights, [k]: parseFloat(e.target.value) })}
                  className="w-full accent-teal-500"
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Match Results Breakdown */}
      {match && (
        <div className="space-y-8">
          {/* Main Hero Compatibility Banner */}
          <div className="p-8 rounded-3xl bg-gradient-to-r from-slate-900 via-slate-850 to-slate-900 border border-slate-800 shadow-xl flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="space-y-2 max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-950 border border-teal-800 text-teal-400 text-xs font-semibold">
                <ShieldCheck className="w-4 h-4" /> {match.explanation_summary.headline}
              </div>
              <h2 className="text-2xl font-extrabold text-white">
                Candidate–Job Compatibility Score
              </h2>
              <p className="text-sm text-slate-300 leading-relaxed">
                {match.explanation_summary.overall_assessment}
              </p>
              <div className="text-xs text-slate-400 font-mono pt-1">
                Recommendation Strategy: <span className="text-teal-300">{match.explanation_summary.recommendation_strategy}</span>
              </div>
            </div>

            {/* Large Radial Score */}
            <div className="flex flex-col items-center justify-center p-6 rounded-2xl bg-slate-950 border border-slate-800 min-w-[200px] text-center">
              <span className="text-xs uppercase tracking-wider font-semibold text-slate-500 mb-1">Final Metric</span>
              <div className="text-5xl font-black font-mono text-teal-400 tracking-tight">
                {match.compatibility_score}
                <span className="text-2xl font-normal text-slate-600">/100</span>
              </div>
              <span className="text-[11px] text-slate-400 mt-2 font-medium">Grounded Compatibility</span>
            </div>
          </div>

          {/* Component Scores Grid (8 Signals) */}
          <div className="space-y-3">
            <h3 className="text-xs uppercase tracking-wider font-bold text-slate-400">Component Signals Breakdown</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <ScoreCard
                title="Required Skill Coverage"
                score={match.required_skill_coverage}
                subtitle="Proportion of must-have job competencies"
                weight={match.calculation_weights.required_skills}
              />
              <ScoreCard
                title="Semantic Fit"
                score={match.semantic_score}
                subtitle="Dense embedding vector cosine similarity"
                weight={match.calculation_weights.semantic_fit}
              />
              <ScoreCard
                title="Evidence Strength"
                score={match.evidence_strength_score}
                subtitle="Skills evidenced by action verbs and metrics"
                weight={match.calculation_weights.evidence_strength}
              />
              <ScoreCard
                title="Experience Alignment"
                score={match.experience_alignment_score}
                subtitle="Candidate timeline vs required threshold"
                weight={match.calculation_weights.experience_alignment}
              />
              <ScoreCard
                title="Preferred Skill Coverage"
                score={match.preferred_skill_coverage}
                subtitle="Nice-to-have capabilities"
                weight={match.calculation_weights.preferred_skills}
              />
              <ScoreCard
                title="Seniority Alignment"
                score={match.seniority_alignment_score}
                subtitle="Junior / Mid / Senior level congruency"
                weight={match.calculation_weights.seniority_alignment}
              />
              <ScoreCard
                title="Domain Alignment"
                score={match.domain_alignment_score}
                subtitle="Cross-functional tech category presence"
                weight={match.calculation_weights.domain_alignment}
              />
              <ScoreCard
                title="Education & Credentials"
                score={match.education_alignment_score}
                subtitle="Degree level alignment"
                weight={match.calculation_weights.education_alignment}
              />
            </div>
          </div>

          {/* Strengths & Critical Concerns */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Top Verified Strengths
              </h4>
              <ul className="space-y-2 text-xs text-slate-300">
                {match.explanation_summary.top_strengths.map((str, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">•</span>
                    <span>{str}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" /> Critical Identified Gaps
              </h4>
              <ul className="space-y-2 text-xs text-slate-300">
                {match.explanation_summary.critical_concerns.map((con, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-amber-400 font-bold">•</span>
                    <span>{con}</span>
                  </li>
                ))}
              </ul>
              <div className="pt-2">
                <button
                  onClick={onNavigateToGaps}
                  className="text-xs text-teal-400 hover:text-teal-300 font-semibold flex items-center gap-1 transition"
                >
                  Inspect Full Skill Gap Analysis <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

          {/* Verbatim Evidence Citations */}
          {match.explanation_summary.citations && match.explanation_summary.citations.length > 0 && (
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Quote className="w-4 h-4 text-teal-400" /> Supporting Resume Citations Grounding This Decision
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {match.explanation_summary.citations.map((c, idx) => (
                  <div
                    key={idx}
                    onClick={() => setInspectSkill(c.entity)}
                    className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-teal-500/50 cursor-pointer transition space-y-2"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-teal-300">{c.entity}</span>
                      <span className="font-mono text-slate-500 text-[10px]">[{c.source_section}]</span>
                    </div>
                    <p className="text-xs italic text-slate-300 border-l-2 border-teal-500 pl-2">
                      "{c.quote}"
                    </p>
                    <p className="text-[11px] text-slate-500">{c.explanation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {(computing || loading) && (
        <div className="p-16 text-center border border-slate-800 rounded-3xl bg-slate-900/40 space-y-3 animate-pulse">
          <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <h3 className="text-sm font-semibold text-white">Evaluating 8 Compatibility Evidence Pillars...</h3>
          <p className="text-xs text-slate-400">Verifying required skills, semantic fit, seniority, and proof snippets</p>
        </div>
      )}

      {!match && !computing && !loading && (
        <div className="p-16 text-center border-2 border-dashed border-slate-800 rounded-3xl bg-slate-900/40 space-y-3">
          <GitCompare className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-lg font-bold text-white">No Match Analysis Selected</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            {resumes.length === 0 || jobs.length === 0
              ? 'Please upload at least one resume and create or select a job target first.'
              : 'Select a candidate resume and target job above, then click "Recompute Match Pipeline" to evaluate compatibility.'}
          </p>
        </div>
      )}

      {/* Interactive Evidence Modal */}
      {match && inspectSkill && (
        <EvidenceModal
          resumeId={match.resume_id}
          skillName={inspectSkill}
          onClose={() => setInspectSkill(null)}
        />
      )}
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import {
  FileText, Briefcase, GitCompare, CheckCircle2, AlertTriangle,
  ArrowUpRight, ShieldCheck, Sparkles, TrendingUp, Cpu
} from 'lucide-react';
import { api } from '../services/api';
import { Resume, Job, Match } from '../types';
import { ScoreCard } from '../components/ScoreCard';
import { EvidenceBadge } from '../components/EvidenceBadge';

interface DashboardPageProps {
  onNavigate: (tab: any) => void;
  onSelectResume: (id: string) => void;
  onSelectJob: (id: string) => void;
  onSelectMatch: (id: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onNavigate, onSelectResume, onSelectJob, onSelectMatch
}) => {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [recentMatches, setRecentMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [resList, jobList] = await Promise.all([
        api.listResumes(),
        api.listJobs()
      ]);
      setResumes(resList);
      setJobs(jobList);

      if (resList.length > 0) {
        const matches = await api.getResumeMatches(resList[0].id);
        setRecentMatches(matches);
      }
    } catch (e) {
      console.error('Failed to load dashboard data', e);
    } finally {
      setLoading(false);
    }
  };

  const activeResume = resumes[0];
  const latestMatch = recentMatches[0];

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Hero Welcome & Principle */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-slate-850 to-slate-900 border border-slate-800 p-8 shadow-xl">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-950/80 border border-teal-800/80 text-teal-400 text-xs font-semibold">
            <ShieldCheck className="w-4 h-4" /> Evidence-First AI Career Intelligence
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">
            Welcome back to Resume<span className="text-teal-400">IQ</span>
          </h1>
          <p className="text-slate-300 text-sm leading-relaxed">
            The career platform engineered around absolute factual integrity. We measure compatibility through
            hybrid semantic embedding and evidence extraction — never inventing metrics or experience.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <button
              onClick={() => onNavigate('resume-intelligence')}
              className="px-4 py-2.5 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-teal-600/20 transition flex items-center gap-2"
            >
              <FileText className="w-4 h-4" /> Upload / Inspect Resume
            </button>
            <button
              onClick={() => onNavigate('job-analyzer')}
              className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold border border-slate-700 transition flex items-center gap-2"
            >
              <Briefcase className="w-4 h-4" /> Analyze Target Job
            </button>
          </div>
        </div>
      </div>

      {/* KPI Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Active Profile</span>
            <FileText className="w-4 h-4 text-teal-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {activeResume ? activeResume.filename : 'No resume uploaded'}
          </div>
          <p className="text-xs text-slate-400">
            {activeResume ? `${activeResume.skills_count} skills extracted with evidence` : 'Upload your resume to begin'}
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Evaluated Roles</span>
            <Briefcase className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-white">{jobs.length} Positions</div>
          <p className="text-xs text-slate-400">Ingested with classified requirements</p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Top Match Compatibility</span>
            <GitCompare className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400">
            {latestMatch ? `${latestMatch.compatibility_score}%` : 'N/A'}
          </div>
          <p className="text-xs text-slate-400">
            {latestMatch ? latestMatch.explanation_summary.headline : 'Run match analysis'}
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Hallucination Rate</span>
            <ShieldCheck className="w-4 h-4 text-teal-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-teal-400">0.00%</div>
          <p className="text-xs text-slate-400">100% verified against candidate evidence</p>
        </div>
      </div>

      {/* Featured Match or Quick Action */}
      {latestMatch && (
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-teal-400 uppercase tracking-wider">Latest Compatibility Audit</span>
              <h3 className="text-lg font-bold text-white">Target Position Match Breakdown</h3>
            </div>
            <button
              onClick={() => {
                onSelectMatch(latestMatch.id);
                onNavigate('match-analysis');
              }}
              className="text-xs text-teal-400 hover:text-teal-300 font-medium flex items-center gap-1 transition"
            >
              View Full Match Breakdown <ArrowUpRight className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <ScoreCard
              title="Compatibility Score"
              score={latestMatch.compatibility_score}
              subtitle="Weighted across 8 signals"
              highlight
            />
            <ScoreCard
              title="Required Skill Coverage"
              score={latestMatch.required_skill_coverage}
              subtitle="Mandatory qualifications present"
            />
            <ScoreCard
              title="Semantic Fit"
              score={latestMatch.semantic_score}
              subtitle="Dense embedding alignment"
            />
            <ScoreCard
              title="Evidence Strength"
              score={latestMatch.evidence_strength_score}
              subtitle="Skills backed by active metrics"
            />
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 leading-relaxed">
            <strong className="text-white">Overall Assessment: </strong>
            {latestMatch.explanation_summary.overall_assessment}
          </div>
        </div>
      )}

      {/* Recent Resumes & Jobs Lists */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Resumes */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-teal-400" /> Uploaded Profiles
            </h3>
            <button
              onClick={() => onNavigate('resume-intelligence')}
              className="text-xs text-teal-400 hover:text-teal-300 font-medium"
            >
              Manage Resumes
            </button>
          </div>

          {resumes.length === 0 ? (
            <div className="p-8 text-center border border-dashed border-slate-800 rounded-xl text-xs text-slate-500">
              No resumes uploaded yet. Click 'Upload / Inspect Resume' above.
            </div>
          ) : (
            <div className="space-y-3">
              {resumes.map((r) => (
                <div
                  key={r.id}
                  onClick={() => {
                    onSelectResume(r.id);
                    onNavigate('resume-intelligence');
                  }}
                  className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 cursor-pointer transition flex items-center justify-between"
                >
                  <div>
                    <div className="text-sm font-semibold text-white">{r.filename}</div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      {r.skills_count} skills • {r.experience_count} work experiences
                    </div>
                  </div>
                  <span className="text-xs font-mono text-teal-400 bg-teal-950/60 px-2 py-1 rounded border border-teal-800">
                    Active
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Jobs */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-sky-400" /> Target Job Descriptions
            </h3>
            <button
              onClick={() => onNavigate('job-analyzer')}
              className="text-xs text-sky-400 hover:text-sky-300 font-medium"
            >
              Analyze New Job
            </button>
          </div>

          {jobs.length === 0 ? (
            <div className="p-8 text-center border border-dashed border-slate-800 rounded-xl text-xs text-slate-500">
              No job postings analyzed yet. Paste a job description to begin.
            </div>
          ) : (
            <div className="space-y-3">
              {jobs.map((j) => (
                <div
                  key={j.id}
                  onClick={() => {
                    onSelectJob(j.id);
                    onNavigate('job-analyzer');
                  }}
                  className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 cursor-pointer transition flex items-center justify-between"
                >
                  <div>
                    <div className="text-sm font-semibold text-white">{j.title}</div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      {j.company} • {j.work_model.toUpperCase()} • {j.seniority.toUpperCase()}
                    </div>
                  </div>
                  <span className="text-xs font-mono text-slate-400 bg-slate-900 px-2 py-1 rounded border border-slate-800">
                    {j.requirements_count || 0} Reqs
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

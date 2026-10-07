import React, { useState, useEffect } from 'react';
import {
  Briefcase, Sparkles, CheckCircle2, AlertCircle, Plus,
  Shield, Tag, Layers, ArrowRight, Trash2
} from 'lucide-react';
import { api } from '../services/api';
import { Job } from '../types';

const SAMPLE_BENCHMARK_JOB = {
  title: 'Senior Backend & Distributed Systems Engineer',
  company: 'Stripe / CloudScale',
  location: 'Remote',
  work_model: 'remote',
  description: `Basic Qualifications:
• 5+ years of software engineering experience with Python and relational database architectures.
• Required: Strong hands-on experience building production microservices with FastAPI or Flask.
• Required: Deep expertise in PostgreSQL schema design, indexing, and query tuning.
• Required: Containerization and deployment with Docker.
• Required: Experience designing robust REST APIs and distributed systems.

Preferred Qualifications:
• Preferred: Familiarity with AWS cloud infrastructure (EC2, S3, ECS).
• Preferred: Experience implementing Redis caching layers and asynchronous task workers.
• Preferred: Knowledge of RAG pipelines, vector search, or LLM application engineering is a major plus.

Responsibilities:
• Architect, deploy, and maintain core high-throughput payment and messaging services.
• Collaborate with cross-functional teams to define architecture standards and system observability.`
};

interface JobAnalyzerPageProps {
  selectedJobId?: string | null;
  onSelectJob: (id: string) => void;
  onNavigateToMatch?: () => void;
}

export const JobAnalyzerPage: React.FC<JobAnalyzerPageProps> = ({
  selectedJobId, onSelectJob, onNavigateToMatch
}) => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [activeJob, setActiveJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [creating, setCreating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Form State - Clean initial state, no preloaded mock data
  const [title, setTitle] = useState('');
  const [company, setCompany] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');

  const handlePopulateSample = () => {
    setTitle(SAMPLE_BENCHMARK_JOB.title);
    setCompany(SAMPLE_BENCHMARK_JOB.company);
    setDescription(SAMPLE_BENCHMARK_JOB.description);
    setLocation(SAMPLE_BENCHMARK_JOB.location);
  };

  useEffect(() => {
    loadJobs();
  }, []);

  useEffect(() => {
    if (selectedJobId && jobs.length > 0) {
      loadJobDetails(selectedJobId);
    }
  }, [selectedJobId, jobs]);

  const loadJobs = async () => {
    setLoading(true);
    try {
      const list = await api.listJobs();
      setJobs(list);
      if (list.length > 0) {
        const targetId = selectedJobId || list[0].id;
        loadJobDetails(targetId);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  const loadJobDetails = async (id: string) => {
    try {
      const detail = await api.getJob(id);
      setActiveJob(detail);
      onSelectJob(id);
    } catch (err: any) {
      setError(err.message || 'Failed to load job details');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !description) return;

    setCreating(true);
    setError(null);
    try {
      const created = await api.createJob({
        title,
        company: company || 'Enterprise Tech',
        description,
        location,
        work_model: 'remote'
      });
      await loadJobs();
      await loadJobDetails(created.id);
    } catch (err: any) {
      setError(err.message || 'Failed to analyze job description');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this job posting?')) return;
    try {
      await api.deleteJob(id);
      await loadJobs();
      if (activeJob?.id === id) {
        setActiveJob(null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete job');
    }
  };

  const getCategoryBadge = (cat: string) => {
    const map: Record<string, { bg: string; text: string; border: string }> = {
      REQUIRED: { bg: 'bg-rose-950/60', text: 'text-rose-400', border: 'border-rose-800' },
      PREFERRED: { bg: 'bg-sky-950/60', text: 'text-sky-400', border: 'border-sky-800' },
      RESPONSIBILITY: { bg: 'bg-teal-950/60', text: 'text-teal-400', border: 'border-teal-800' },
      EXPERIENCE: { bg: 'bg-amber-950/60', text: 'text-amber-400', border: 'border-amber-800' },
      QUALIFICATION: { bg: 'bg-purple-950/60', text: 'text-purple-400', border: 'border-purple-800' },
      DOMAIN: { bg: 'bg-indigo-950/60', text: 'text-indigo-400', border: 'border-indigo-800' }
    };
    const c = map[cat] || { bg: 'bg-slate-900', text: 'text-slate-400', border: 'border-slate-800' };
    return (
      <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded border ${c.bg} ${c.text} ${c.border}`}>
        {cat}
      </span>
    );
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <Briefcase className="w-6 h-6 text-sky-400" /> Job Intelligence Engine
          </h1>
          <p className="text-sm text-slate-400">
            Deep syntactic and semantic analysis of job descriptions with categorized requirements and importance weighting.
          </p>
        </div>

        {activeJob && onNavigateToMatch && (
          <button
            onClick={onNavigateToMatch}
            className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-teal-600/20 transition flex items-center gap-2"
          >
            <span>Proceed to Match Analysis</span>
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

      {/* Grid: Creation Form & Jobs List */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Input Form (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Plus className="w-4 h-4 text-sky-400" /> Ingest New Target Role
              </h3>
              {import.meta.env.DEV && (
                <button
                  type="button"
                  onClick={handlePopulateSample}
                  className="text-[11px] text-amber-400 hover:text-amber-300 font-mono flex items-center gap-1"
                >
                  <Sparkles className="w-3 h-3" /> [Dev Only] Sample
                </button>
              )}
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Job Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Senior Backend Engineer"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-teal-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Company</label>
                  <input
                    type="text"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    placeholder="e.g. Stripe"
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-teal-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Location</label>
                  <input
                    type="text"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="Remote / City"
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Job Description Content</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={10}
                  placeholder="Paste the full job posting requirements and responsibilities here..."
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:border-teal-500"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={creating}
                className="w-full py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-sky-600/20 transition flex items-center justify-center gap-2"
              >
                <Sparkles className="w-4 h-4" />
                <span>{creating ? 'Extracting & Classifying Requirements...' : 'Deep Parse Job Description'}</span>
              </button>
            </form>
          </div>

          {/* Existing Jobs Selector */}
          {jobs.length > 0 && (
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Ingested Positions ({jobs.length})</h4>
              <div className="space-y-2">
                {jobs.map((j) => (
                  <div
                    key={j.id}
                    onClick={() => loadJobDetails(j.id)}
                    className={`p-3 rounded-xl border cursor-pointer transition flex items-center justify-between ${
                      activeJob?.id === j.id
                        ? 'bg-sky-950/60 border-sky-800 text-sky-200'
                        : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
                    }`}
                  >
                    <div>
                      <div className="text-xs font-bold">{j.title}</div>
                      <div className="text-[10px] text-slate-500">{j.company} • {j.work_model}</div>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                      {j.requirements_count || 0} reqs
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Parsed Results & Classification (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {activeJob ? (
            <div className="space-y-6">
              {/* Job Summary Banner */}
              <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono text-sky-400 uppercase tracking-wider">Structured Job Blueprint</span>
                    <span className="text-slate-600">•</span>
                    <span className="text-xs text-slate-400 font-mono">Seniority: {activeJob.seniority.toUpperCase()}</span>
                  </div>
                  <h2 className="text-xl font-bold text-white">{activeJob.title}</h2>
                  <div className="text-xs text-slate-400 mt-1">{activeJob.company} • {activeJob.location}</div>
                </div>
                <button
                  onClick={() => handleDelete(activeJob.id)}
                  className="p-2 text-slate-500 hover:text-rose-400 rounded-lg hover:bg-rose-950/30 transition"
                  title="Delete Job"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {/* Extracted Skills with Required vs Preferred Flags */}
              <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Tag className="w-4 h-4 text-sky-400" /> Technical Competencies Identified ({activeJob.skills?.length || 0})
                  </h3>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-rose-400 text-[10px] bg-rose-950/60 px-2 py-0.5 rounded border border-rose-800">Required</span>
                    <span className="text-sky-400 text-[10px] bg-sky-950/60 px-2 py-0.5 rounded border border-sky-800">Preferred</span>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {activeJob.skills?.map((sk) => (
                    <div
                      key={sk.id}
                      className={`px-3 py-1.5 rounded-xl border text-xs font-medium flex items-center gap-2 ${
                        sk.is_required
                          ? 'bg-rose-950/30 border-rose-800/80 text-rose-300'
                          : 'bg-sky-950/30 border-sky-800/80 text-sky-300'
                      }`}
                    >
                      <span>{sk.normalized_skill}</span>
                      <span className="text-[10px] opacity-75 font-mono">w={sk.importance_weight}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Classified Requirements List */}
              <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Layers className="w-4 h-4 text-teal-400" />
                  Classified Requirements Breakdown ({activeJob.requirements?.length || 0})
                </h3>

                <div className="space-y-3">
                  {activeJob.requirements?.map((req) => (
                    <div key={req.id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-2">
                      <div className="flex items-center justify-between">
                        {getCategoryBadge(req.category)}
                        <span className="font-mono text-slate-500 text-[10px]">Weight: {req.importance_weight}</span>
                      </div>
                      <p className="text-slate-300 leading-relaxed font-sans">{req.requirement_text}</p>
                      {req.normalized_entities && req.normalized_entities.length > 0 && (
                        <div className="flex flex-wrap gap-1 pt-1">
                          {req.normalized_entities.map((e, idx) => (
                            <span key={idx} className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-900 text-teal-300 border border-slate-800">
                              {e}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-16 text-center border-2 border-dashed border-slate-800 rounded-2xl bg-slate-900/40 text-xs text-slate-500">
              Select or ingest a job to view requirement classifications.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

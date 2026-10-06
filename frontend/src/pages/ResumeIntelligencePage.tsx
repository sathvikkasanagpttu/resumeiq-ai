import React, { useState, useEffect } from 'react';
import {
  Upload, FileText, CheckCircle2, AlertCircle, Quote, Briefcase,
  FolderGit2, GraduationCap, Award, ShieldCheck, Sparkles, Trash2
} from 'lucide-react';
import { api } from '../services/api';
import { Resume } from '../types';
import { EvidenceBadge } from '../components/EvidenceBadge';
import { EvidenceModal } from '../components/EvidenceModal';

const SAMPLE_RESUME_TEXT = `Sarah Chen
Email: sarah.chen@example.com | San Francisco, CA | github.com/sarahchen

PROFESSIONAL SUMMARY
Senior Backend & AI Systems Engineer with 6+ years of experience building resilient microservices, distributed data pipelines, and production RAG systems.

WORK EXPERIENCE
Senior Software Engineer - CloudScale AI (2021 - Present)
• Architected high-throughput REST APIs and asynchronous workers using FastAPI, Python, and PostgreSQL, handling 40,000 requests/sec with sub-25ms p99 latency.
• Orchestrated containerized microservices deployments with Docker and AWS ECS, achieving 99.99% system availability.
• Integrated Redis caching and distributed task queues, reducing database read load by 60% and saving $18,000 monthly in cloud infrastructure costs.
• Spearheaded production RAG pipeline with hybrid retrieval (dense embeddings + BM25) and reciprocal rank fusion, improving context relevance by 35%.

Software Engineer - NextGen Analytics (2018 - 2021)
• Engineered scalable ETL data pipelines using Python, SQL, and PostgreSQL for enterprise data warehouse integration.
• Developed CI/CD automated test workflows using GitHub Actions and Docker, reducing deployment cycle times by 3x.
• Built full-stack monitoring dashboards using React and TypeScript for real-time telemetry.

EDUCATION
B.S. in Computer Science - University of California, Berkeley (2018)
GPA: 3.85 / 4.0

TECHNICAL SKILLS
Languages: Python, SQL, TypeScript, JavaScript
Backend & Frameworks: FastAPI, Flask, SQLAlchemy, REST API
Databases & Cache: PostgreSQL, Redis, MySQL
Cloud & DevOps: AWS, Docker, GitHub Actions, Linux
AI & Data: RAG, Embeddings, LLMs, Pandas, Scikit-learn`;

interface ResumeIntelligencePageProps {
  selectedResumeId?: string | null;
  onSelectResume: (id: string) => void;
}

export const ResumeIntelligencePage: React.FC<ResumeIntelligencePageProps> = ({
  selectedResumeId, onSelectResume
}) => {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [activeResume, setActiveResume] = useState<Resume | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [uploading, setUploading] = useState<boolean>(false);
  const [inspectSkill, setInspectSkill] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadResumes();
  }, []);

  useEffect(() => {
    if (selectedResumeId && resumes.length > 0) {
      loadResumeDetails(selectedResumeId);
    }
  }, [selectedResumeId, resumes]);

  const loadResumes = async () => {
    setLoading(true);
    try {
      const list = await api.listResumes();
      setResumes(list);
      if (list.length > 0) {
        const targetId = selectedResumeId || list[0].id;
        loadResumeDetails(targetId);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load resumes');
    } finally {
      setLoading(false);
    }
  };

  const loadResumeDetails = async (id: string) => {
    try {
      const detail = await api.getResume(id);
      setActiveResume(detail);
      onSelectResume(id);
    } catch (err: any) {
      setError(err.message || 'Failed to load resume details');
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    try {
      const uploaded = await api.uploadResume(file);
      await loadResumes();
      await loadResumeDetails(uploaded.id);
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleLoadSample = async () => {
    setUploading(true);
    setError(null);
    try {
      const blob = new Blob([SAMPLE_RESUME_TEXT], { type: 'text/plain' });
      const file = new File([blob], 'Sarah_Chen_Senior_Engineer_Resume.txt', { type: 'text/plain' });
      const uploaded = await api.uploadResume(file);
      await loadResumes();
      await loadResumeDetails(uploaded.id);
    } catch (err: any) {
      setError(err.message || 'Failed to load sample resume');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this resume?')) return;
    try {
      await api.deleteResume(id);
      await loadResumes();
      if (activeResume?.id === id) {
        setActiveResume(null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete resume');
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <FileText className="w-6 h-6 text-teal-400" /> Resume Intelligence Engine
          </h1>
          <p className="text-sm text-slate-400">
            Multi-stage extraction pipeline with section segmentation, entity recognition, and evidence-strength scoring.
          </p>
        </div>

        {/* Upload Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleLoadSample}
            disabled={uploading}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold border border-slate-700 transition flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4 text-teal-400" /> Load Benchmark Profile
          </button>

          <label className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-teal-600/20 cursor-pointer transition flex items-center gap-2">
            <Upload className="w-4 h-4" />
            <span>{uploading ? 'Processing Document...' : 'Upload PDF / DOCX / TXT'}</span>
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Resume Selector Bar */}
      {resumes.length > 1 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-800">
          <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider mr-2">Available:</span>
          {resumes.map((r) => (
            <button
              key={r.id}
              onClick={() => loadResumeDetails(r.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-2 ${
                activeResume?.id === r.id
                  ? 'bg-teal-950 text-teal-300 border border-teal-800'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>{r.filename}</span>
            </button>
          ))}
        </div>
      )}

      {!activeResume && !loading && (
        <div className="p-16 text-center border-2 border-dashed border-slate-800 rounded-3xl bg-slate-900/40 space-y-4">
          <Upload className="w-12 h-12 text-slate-600 mx-auto" />
          <div>
            <h3 className="text-lg font-bold text-white">No Resume Active</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Upload your resume in PDF, DOCX, or TXT format or click 'Load Benchmark Profile' to test the extraction engine.
            </p>
          </div>
          <button
            onClick={handleLoadSample}
            className="px-5 py-2.5 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-teal-600/20 transition inline-flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4" /> Load Sarah Chen Benchmark
          </button>
        </div>
      )}

      {activeResume && (
        <div className="space-y-8">
          {/* Resume Overview Header */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono text-teal-400 uppercase tracking-wider">Active Parsed Document</span>
                <span className="text-slate-600">•</span>
                <span className="text-xs text-slate-400 font-mono">Format: {activeResume.file_type.toUpperCase()}</span>
                <span className="text-slate-600">•</span>
                <span className="text-xs text-slate-400 font-mono">{Math.round(activeResume.file_size / 1024)} KB</span>
              </div>
              <h2 className="text-xl font-bold text-white">{activeResume.filename}</h2>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-xs text-slate-500">Skills Identified</div>
                <div className="text-lg font-mono font-bold text-teal-400">{activeResume.skills?.length || 0}</div>
              </div>
              <div className="text-right pl-4 border-l border-slate-800">
                <div className="text-xs text-slate-500">Work History</div>
                <div className="text-lg font-mono font-bold text-sky-400">{activeResume.experiences?.length || 0} Roles</div>
              </div>
              <button
                onClick={() => handleDelete(activeResume.id)}
                className="p-2 text-slate-500 hover:text-rose-400 hover:bg-rose-950/40 rounded-lg transition"
                title="Delete Resume"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Extracted Skills Section with Evidence Inspector */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-teal-400" />
                  Extracted Skills & Verified Evidence Graph
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Click any skill below to inspect its exact verbatim citation, action verb, metric, and confidence score.
                </p>
              </div>
              <div className="hidden sm:flex items-center gap-3 text-xs">
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" /> Verified (Action + Metric)
                </span>
                <span className="flex items-center gap-1.5 text-amber-400">
                  <span className="w-2 h-2 rounded-full bg-amber-400" /> Weak (Listed Only)
                </span>
              </div>
            </div>

            <div className="flex flex-wrap gap-2.5 pt-2">
              {activeResume.skills?.map((sk) => (
                <button
                  key={sk.id}
                  onClick={() => setInspectSkill(sk.normalized_skill)}
                  className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 hover:border-teal-500/60 hover:bg-slate-850 transition text-left flex items-center gap-2.5 group"
                >
                  <span className="text-xs font-semibold text-slate-200 group-hover:text-teal-300 transition">
                    {sk.normalized_skill}
                  </span>
                  <EvidenceBadge strength={sk.evidence_strength} size="sm" />
                </button>
              ))}
            </div>
          </div>

          {/* Work Experience */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-teal-400" /> Verified Work Experience ({activeResume.experiences?.length || 0})
            </h3>
            <div className="space-y-4">
              {activeResume.experiences?.map((exp) => (
                <div key={exp.id} className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                    <div>
                      <h4 className="text-base font-bold text-white">{exp.role}</h4>
                      <div className="text-xs font-semibold text-teal-400">{exp.company} • {exp.location || 'Remote'}</div>
                    </div>
                    <span className="text-xs font-mono text-slate-400 bg-slate-900 px-2.5 py-1 rounded border border-slate-800 w-fit">
                      {exp.start_date || 'Past'} — {exp.end_date || 'Present'}
                    </span>
                  </div>

                  {/* Bullet Points */}
                  <ul className="space-y-2 text-xs text-slate-300 leading-relaxed">
                    {exp.bullet_points.map((b, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-teal-400 font-bold mt-0.5">•</span>
                        <span>{b}</span>
                      </li>
                    ))}
                  </ul>

                  {/* Technologies */}
                  {exp.technologies && exp.technologies.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-2 border-t border-slate-900">
                      <span className="text-[10px] text-slate-500 uppercase font-mono mr-1 self-center">Used:</span>
                      {exp.technologies.map((t, idx) => (
                        <span key={idx} className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Raw Text Inspector Accordion */}
          <details className="p-6 rounded-2xl bg-slate-900 border border-slate-800 group">
            <summary className="text-sm font-semibold text-slate-300 cursor-pointer hover:text-white flex items-center justify-between">
              <span>View Raw Extracted Text Document</span>
              <span className="text-xs text-teal-400 group-open:rotate-180 transition">▼</span>
            </summary>
            <pre className="mt-4 p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-400 whitespace-pre-wrap max-h-96 overflow-y-auto leading-relaxed">
              {activeResume.raw_text}
            </pre>
          </details>
        </div>
      )}

      {/* Interactive Evidence Modal */}
      {activeResume && inspectSkill && (
        <EvidenceModal
          resumeId={activeResume.id}
          skillName={inspectSkill}
          onClose={() => setInspectSkill(null)}
        />
      )}
    </div>
  );
};

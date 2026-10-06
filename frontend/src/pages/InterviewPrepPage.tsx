import React, { useState } from 'react';
import {
  MessageSquare, Sparkles, CheckCircle2, AlertCircle, RefreshCw,
  Layers, ChevronDown, ChevronUp, BookOpen, ShieldCheck, Quote
} from 'lucide-react';
import { api } from '../services/api';
import { Resume, InterviewPrepQuestion, InterviewPrepResponse } from '../types';

interface InterviewPrepPageProps {
  selectedResumeId: string | null;
  resumes: Resume[];
  onSelectResume: (id: string) => void;
}

export const InterviewPrepPage: React.FC<InterviewPrepPageProps> = ({
  selectedResumeId,
  resumes,
  onSelectResume
}) => {
  const [targetRole, setTargetRole] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [prepData, setPrepData] = useState<InterviewPrepResponse | null>(null);
  const [expandedQuestionId, setExpandedQuestionId] = useState<string | null>(null);
  const [rehearsalNotes, setRehearsalNotes] = useState<Record<string, string>>({});

  const handleGenerate = async () => {
    if (!selectedResumeId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.generateInterviewPrep({
        resume_id: selectedResumeId,
        target_role: targetRole.trim() || undefined
      });
      setPrepData(res);
      if (res.questions.length > 0) {
        setExpandedQuestionId(res.questions[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate interview prep session.');
    } finally {
      setLoading(false);
    }
  };

  const getCategoryColor = (cat: string) => {
    const c = cat.toLowerCase();
    if (c.includes('behavioral')) return 'bg-purple-950/80 text-purple-300 border-purple-800';
    if (c.includes('architect') || c.includes('technical')) return 'bg-blue-950/80 text-blue-300 border-blue-800';
    return 'bg-emerald-950/80 text-emerald-300 border-emerald-800';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400">
              <MessageSquare className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
                Interview Prep STAR Engine
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-teal-500/20 text-teal-300 font-mono">
                  Grounded
                </span>
              </h1>
              <p className="text-xs text-slate-400">
                Generate behavioral and technical interview questions strictly grounded in your verified resume evidence.
              </p>
            </div>
          </div>
        </div>

        {/* Verification Guarantee badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400">
          <ShieldCheck className="w-4 h-4 text-teal-400" />
          <span>Zero-Fabrication STAR Skeletons</span>
        </div>
      </div>

      {/* Configuration Bar */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Select Candidate Resume
            </label>
            <select
              value={selectedResumeId || ''}
              onChange={(e) => onSelectResume(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-teal-500"
            >
              {resumes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.filename}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Target Role (Optional)
            </label>
            <input
              type="text"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              placeholder="e.g. Senior Backend Engineer"
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500"
            />
          </div>

          <div>
            <button
              onClick={handleGenerate}
              disabled={loading || !selectedResumeId}
              className="w-full px-4 py-2 bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-400 hover:to-emerald-500 disabled:opacity-50 text-white font-semibold text-xs rounded-xl shadow-lg shadow-teal-500/20 transition-all flex items-center justify-center gap-2 h-[38px]"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Synthesizing Questions...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Generate STAR Prep</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 flex items-center gap-2 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Prep Questions Display */}
      {!prepData ? (
        <div className="py-20 text-center bg-slate-900/40 rounded-2xl border border-slate-800 text-xs text-slate-400 space-y-2">
          <BookOpen className="w-10 h-10 text-teal-500/50 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-300">No Interview Prep Generated Yet</h3>
          <p>Select your resume and click "Generate STAR Prep" to formulate targeted practice questions.</p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <span>
              Targeting: <strong className="text-slate-200">{prepData.target_role}</strong>
            </span>
            <span className="font-mono">{prepData.total_questions} Questions Formulated</span>
          </div>

          <div className="space-y-4">
            {prepData.questions.map((q: InterviewPrepQuestion, idx) => {
              const isExpanded = expandedQuestionId === q.id;
              const notes = rehearsalNotes[q.id] || '';

              return (
                <div
                  key={q.id}
                  className="rounded-2xl border border-slate-800 bg-slate-900 overflow-hidden transition-all shadow-sm"
                >
                  {/* Question Header Accordion */}
                  <div
                    onClick={() => setExpandedQuestionId(isExpanded ? null : q.id)}
                    className="p-5 flex items-start justify-between gap-4 cursor-pointer hover:bg-slate-800/50 transition-colors"
                  >
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                          Q{idx + 1}
                        </span>
                        <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${getCategoryColor(q.category)}`}>
                          {q.category}
                        </span>
                      </div>
                      <h3 className="text-sm font-bold text-slate-100 leading-snug">{q.question}</h3>
                    </div>

                    <button className="text-slate-400 hover:text-slate-200 p-1">
                      {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                    </button>
                  </div>

                  {/* Expanded Body */}
                  {isExpanded && (
                    <div className="px-5 pb-5 pt-2 border-t border-slate-800/80 space-y-4 text-xs animate-in fade-in duration-150">
                      {/* Cited Evidence Callout */}
                      <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-1">
                        <div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase text-teal-400">
                          <Quote className="w-3.5 h-3.5" />
                          <span>Cited Resume Evidence Context</span>
                        </div>
                        <p className="text-slate-300 italic font-serif text-[11px] leading-relaxed">
                          "{q.context_evidence}"
                        </p>
                      </div>

                      {/* Structured STAR Skeleton Breakdown */}
                      <div className="space-y-2.5">
                        <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                          Recommended STAR Skeleton Framework
                        </h4>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {q.star_skeleton.situation && (
                            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                              <span className="text-[10px] font-bold uppercase text-purple-400 font-mono">
                                [S] Situation
                              </span>
                              <p className="text-slate-300 leading-relaxed text-[11px]">
                                {q.star_skeleton.situation}
                              </p>
                            </div>
                          )}

                          {q.star_skeleton.task && (
                            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                              <span className="text-[10px] font-bold uppercase text-blue-400 font-mono">
                                [T] Task
                              </span>
                              <p className="text-slate-300 leading-relaxed text-[11px]">
                                {q.star_skeleton.task}
                              </p>
                            </div>
                          )}

                          {q.star_skeleton.action && (
                            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                              <span className="text-[10px] font-bold uppercase text-teal-400 font-mono">
                                [A] Action
                              </span>
                              <p className="text-slate-300 leading-relaxed text-[11px]">
                                {q.star_skeleton.action}
                              </p>
                            </div>
                          )}

                          {q.star_skeleton.result && (
                            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                              <span className="text-[10px] font-bold uppercase text-emerald-400 font-mono">
                                [R] Result
                              </span>
                              <p className="text-slate-300 leading-relaxed text-[11px]">
                                {q.star_skeleton.result}
                              </p>
                            </div>
                          )}

                          {q.star_skeleton.architecture && (
                            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                              <span className="text-[10px] font-bold uppercase text-sky-400 font-mono">
                                Architecture Decisions
                              </span>
                              <p className="text-slate-300 leading-relaxed text-[11px]">
                                {q.star_skeleton.architecture}
                              </p>
                            </div>
                          )}

                          {q.star_skeleton.trade_offs && (
                            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                              <span className="text-[10px] font-bold uppercase text-amber-400 font-mono">
                                Technical Trade-offs
                              </span>
                              <p className="text-slate-300 leading-relaxed text-[11px]">
                                {q.star_skeleton.trade_offs}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Rehearsal Notes Draft Area */}
                      <div className="pt-2">
                        <label className="block text-[11px] font-medium text-slate-400 mb-1">
                          Candidate Rehearsal Notes / Talking Points:
                        </label>
                        <textarea
                          rows={2}
                          value={notes}
                          onChange={(e) =>
                            setRehearsalNotes({ ...rehearsalNotes, [q.id]: e.target.value })
                          }
                          placeholder="Jot down notes or practice delivery for this question..."
                          className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500"
                        />
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
export default InterviewPrepPage;

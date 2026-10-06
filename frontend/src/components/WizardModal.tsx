import React, { useState, useEffect } from 'react';
import { X, HelpCircle, CheckCircle2, Sparkles, AlertCircle, ArrowRight, Save } from 'lucide-react';
import { api } from '../services/api';
import { WizardQuestion, WizardAnswer } from '../types';

interface WizardModalProps {
  isOpen: boolean;
  onClose: () => void;
  resumeId: string;
  onAnswersSubmitted?: () => void;
}

export const WizardModal: React.FC<WizardModalProps> = ({
  isOpen,
  onClose,
  resumeId,
  onAnswersSubmitted
}) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [questions, setQuestions] = useState<WizardQuestion[]>([]);
  const [summaryMessage, setSummaryMessage] = useState<string>('');
  const [answers, setAnswers] = useState<Record<string, { answer_text: string; metric?: string; techs?: string }>>({});
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && resumeId) {
      loadQuestions();
    }
  }, [isOpen, resumeId]);

  const loadQuestions = async () => {
    setLoading(true);
    setError(null);
    setSubmitSuccess(null);
    try {
      const res = await api.getWizardQuestions(resumeId);
      setQuestions(res.questions || []);
      setSummaryMessage(res.summary_message || 'Review identified gaps to strengthen resume evidence.');
      // Initialize answer map
      const initial: Record<string, { answer_text: string; metric?: string; techs?: string }> = {};
      res.questions.forEach((q) => {
        initial[q.id] = { answer_text: '', metric: '', techs: '' };
      });
      setAnswers(initial);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch wizard questions.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const handleTextChange = (qId: string, val: string) => {
    setAnswers((prev) => ({
      ...prev,
      [qId]: { ...prev[qId], answer_text: val }
    }));
  };

  const handleMetricChange = (qId: string, val: string) => {
    setAnswers((prev) => ({
      ...prev,
      [qId]: { ...prev[qId], metric: val }
    }));
  };

  const handleTechsChange = (qId: string, val: string) => {
    setAnswers((prev) => ({
      ...prev,
      [qId]: { ...prev[qId], techs: val }
    }));
  };

  const handleApplyExample = (qId: string, ex: string) => {
    handleTextChange(qId, ex);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const payload: WizardAnswer[] = Object.entries(answers)
        .filter(([_, ans]) => ans.answer_text.trim().length > 0)
        .map(([qId, ans]) => ({
          question_id: qId,
          answer_text: ans.answer_text.trim(),
          confirmed_metric: ans.metric?.trim() || undefined,
          confirmed_technologies: ans.techs
            ? ans.techs.split(',').map((t) => t.trim()).filter((t) => t.length > 0)
            : []
        }));

      if (payload.length === 0) {
        setError('Please answer at least one question before submitting.');
        setSubmitting(false);
        return;
      }

      const res = await api.submitWizardAnswers(resumeId, payload);
      setSubmitSuccess(res.message);
      if (onAnswersSubmitted) {
        onAnswersSubmitted();
      }
    } catch (err: any) {
      setError(err.message || 'Failed to submit answers.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                Missing-Info Wizard
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-teal-500/20 text-teal-300 font-mono">
                  {questions.length} Detected Gaps
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Ground your resume with verified user-confirmed facts. Never invent metrics.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-400 space-y-3">
              <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-sm">Analyzing resume representation gaps & missing evidence...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div className="text-xs">{error}</div>
            </div>
          ) : submitSuccess ? (
            <div className="py-12 px-6 text-center space-y-4">
              <div className="w-14 h-14 bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold text-slate-100">Evidence Confirmed & Saved!</h3>
              <p className="text-sm text-slate-300 max-w-md mx-auto">{submitSuccess}</p>
              <div className="pt-4 flex justify-center gap-3">
                <button
                  onClick={onClose}
                  className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-semibold text-xs transition-colors shadow-lg shadow-teal-600/20 flex items-center gap-2"
                >
                  Return to Resume Studio
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : questions.length === 0 ? (
            <div className="text-center py-12 space-y-2 text-slate-400">
              <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
              <h3 className="text-base font-semibold text-slate-200">No Critical Gaps Detected!</h3>
              <p className="text-xs">Your resume has strong evidence coverage across summary, metrics, and experience.</p>
            </div>
          ) : (
            <>
              {/* Summary message */}
              <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-xs text-slate-300 flex items-center gap-2.5">
                <HelpCircle className="w-4 h-4 text-teal-400 flex-shrink-0" />
                <span>{summaryMessage}</span>
              </div>

              {/* Questions List */}
              <div className="space-y-6">
                {questions.map((q, idx) => {
                  const currentAns = answers[q.id] || { answer_text: '', metric: '', techs: '' };
                  const isAnswered = currentAns.answer_text.trim().length > 0;

                  return (
                    <div
                      key={q.id}
                      className={`p-5 rounded-xl border transition-all ${
                        isAnswered
                          ? 'bg-slate-900/90 border-teal-500/40 shadow-sm'
                          : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-4 mb-3">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                            #{idx + 1}
                          </span>
                          <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold uppercase tracking-wider bg-teal-950/80 text-teal-400 border border-teal-800/60">
                            {q.category}
                          </span>
                          <span className="text-xs px-2 py-0.5 rounded bg-slate-800/70 text-slate-400">
                            Section: {q.target_section}
                          </span>
                        </div>
                        {isAnswered && (
                          <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-400">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Answered
                          </span>
                        )}
                      </div>

                      <h4 className="text-sm font-semibold text-slate-100 mb-1">{q.prompt_text}</h4>
                      <p className="text-xs text-slate-400 mb-3">{q.context_hint}</p>

                      {/* Example Inspiration Tags */}
                      {q.example_answers && q.example_answers.length > 0 && (
                        <div className="mb-3 flex items-center gap-1.5 flex-wrap">
                          <span className="text-[10px] text-slate-500 uppercase font-semibold">Examples:</span>
                          {q.example_answers.map((ex, i) => (
                            <button
                              key={i}
                              type="button"
                              onClick={() => handleApplyExample(q.id, ex)}
                              className="text-[11px] px-2 py-0.5 rounded-md bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700/60 transition-colors text-left"
                            >
                              "{ex}"
                            </button>
                          ))}
                        </div>
                      )}

                      {/* Main Answer Area */}
                      <div className="space-y-3">
                        <div>
                          <label className="block text-[11px] font-medium text-slate-300 mb-1">
                            Your Verifiable Answer:
                          </label>
                          <textarea
                            rows={2}
                            value={currentAns.answer_text}
                            onChange={(e) => handleTextChange(q.id, e.target.value)}
                            placeholder="Provide concrete details from your actual experience..."
                            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500"
                          />
                        </div>

                        {/* Optional Metric & Tech Fields */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          <div>
                            <label className="block text-[11px] font-medium text-slate-400 mb-1">
                              Confirmed Metric (Optional, e.g. "35%", "$120k", "50k daily active users"):
                            </label>
                            <input
                              type="text"
                              value={currentAns.metric || ''}
                              onChange={(e) => handleMetricChange(q.id, e.target.value)}
                              placeholder="e.g. 40% latency reduction"
                              className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500"
                            />
                          </div>

                          <div>
                            <label className="block text-[11px] font-medium text-slate-400 mb-1">
                              Technologies Used (Comma-separated, e.g. "Python, Redis, Docker"):
                            </label>
                            <input
                              type="text"
                              value={currentAns.techs || ''}
                              onChange={(e) => handleTechsChange(q.id, e.target.value)}
                              placeholder="e.g. PostgreSQL, Celery, FastAPI"
                              className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        {!submitSuccess && questions.length > 0 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-slate-800 bg-slate-900/60">
            <div className="text-xs text-slate-400">
              {Object.values(answers).filter((a) => a.answer_text.trim().length > 0).length} of{' '}
              {questions.length} questions completed
            </div>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={submitting}
                className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white font-semibold text-xs transition-colors shadow-lg shadow-teal-600/20 flex items-center gap-2"
              >
                {submitting ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Saving Facts...</span>
                  </>
                ) : (
                  <>
                    <Save className="w-3.5 h-3.5" />
                    <span>Confirm Evidence & Save</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

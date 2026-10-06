import React, { useState, useEffect } from 'react';
import {
  Wand2, ShieldCheck, CheckCircle2, ArrowRight, Sparkles,
  AlertCircle, Copy, Check, ArrowLeftRight, Layers
} from 'lucide-react';
import { api } from '../services/api';
import { ResumeOptimization } from '../types';

interface ResumeOptimizerPageProps {
  selectedMatchId?: string | null;
  onNavigateToApplications?: () => void;
}

export const ResumeOptimizerPage: React.FC<ResumeOptimizerPageProps> = ({
  selectedMatchId, onNavigateToApplications
}) => {
  const [optimization, setOptimization] = useState<ResumeOptimization | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedMatchId) {
      loadOptimization(selectedMatchId);
    }
  }, [selectedMatchId]);

  const loadOptimization = async (matchId: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getResumeOptimization(matchId);
      setOptimization(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load optimization');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <Wand2 className="w-6 h-6 text-teal-400" /> Evidence-Grounded Resume Optimizer
          </h1>
          <p className="text-sm text-slate-400">
            Transforms passive phrases into active Google XYZ outcome statements while strictly prohibiting hallucination or invented metrics.
          </p>
        </div>

        {onNavigateToApplications && (
          <button
            onClick={onNavigateToApplications}
            className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-teal-600/20 transition flex items-center gap-2"
          >
            <span>Proceed to Cover Letter Generation</span>
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

      {/* Truthfulness Guarantee Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-teal-950/40 via-slate-900 to-slate-900 border border-teal-800/80 shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-xs font-bold text-teal-400 uppercase tracking-wider">
            <ShieldCheck className="w-4 h-4" /> Strict Grounding Contract
          </div>
          <h3 className="text-lg font-bold text-white">Zero Invention Guarantee</h3>
          <p className="text-xs text-slate-300 leading-relaxed max-w-2xl">
            {optimization?.truthfulness_guarantee ||
              'Every suggested revision is mathematically bounded by the candidate’s verifiable experience. No phantom metrics, unearned titles, or fabricated technologies are ever introduced.'}
          </p>
        </div>

        {optimization && (
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center min-w-[160px]">
            <span className="text-[10px] uppercase font-bold text-slate-500">Projected Gain</span>
            <div className="text-2xl font-black font-mono text-teal-400">
              +{optimization.estimated_compatibility_gain}%
            </div>
            <span className="text-[10px] text-slate-400">Compatibility Boost</span>
          </div>
        )}
      </div>

      {/* Before / After Modifications */}
      {optimization ? (
        <div className="space-y-6">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <ArrowLeftRight className="w-4 h-4 text-teal-400" />
            Before & After Bullet Point Transformations ({optimization.modifications.length})
          </h3>

          <div className="space-y-6">
            {optimization.modifications.map((mod, idx) => (
              <div
                key={idx}
                className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 hover:border-slate-700 transition"
              >
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="font-semibold text-teal-400 font-mono">[{mod.section}]</span>
                  <span className="font-mono text-slate-500">Confidence: {Math.round(mod.confidence * 100)}%</span>
                </div>

                {/* Diff Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Before */}
                  <div className="p-4 rounded-xl bg-slate-950 border border-rose-950/60 space-y-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-rose-400 font-mono">
                      Original / As Extracted
                    </span>
                    <p className="text-xs font-mono text-slate-300 leading-relaxed">
                      "{mod.original_text}"
                    </p>
                  </div>

                  {/* After */}
                  <div className="p-4 rounded-xl bg-teal-950/20 border border-teal-800/80 space-y-2 relative group">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-teal-400 font-mono flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" /> Optimized (Active & Truthful)
                      </span>
                      <button
                        onClick={() => copyToClipboard(mod.optimized_text, idx)}
                        className="text-xs text-teal-400 hover:text-teal-300 flex items-center gap-1 bg-slate-900 px-2 py-0.5 rounded border border-slate-800"
                      >
                        {copiedIdx === idx ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                        <span>{copiedIdx === idx ? 'Copied' : 'Copy'}</span>
                      </button>
                    </div>
                    <p className="text-xs font-mono text-slate-100 font-medium leading-relaxed">
                      "{mod.optimized_text}"
                    </p>
                  </div>
                </div>

                {/* Rationale & Grounded Evidence */}
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 text-xs space-y-1.5">
                  <div className="text-[10px] uppercase font-bold text-slate-400">Engineering Rationale</div>
                  <p className="text-slate-300 leading-relaxed">{mod.rationale}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Formatting & Representation Tips */}
          {optimization.formatting_recommendations.length > 0 && (
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Structural & Formatting Recommendations
              </h4>
              <ul className="space-y-2 text-xs text-slate-300">
                {optimization.formatting_recommendations.map((tip, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-teal-400 font-bold">•</span>
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <div className="p-16 text-center border-2 border-dashed border-slate-800 rounded-3xl bg-slate-900/40 text-xs text-slate-500">
          Run or select a compatibility match to generate tailored resume optimizations.
        </div>
      )}
    </div>
  );
};

import React from 'react';

interface ScoreCardProps {
  title: string;
  score: number;
  subtitle?: string;
  weight?: number;
  highlight?: boolean;
}

export const ScoreCard: React.FC<ScoreCardProps> = ({ title, score, subtitle, weight, highlight = false }) => {
  const getScoreColor = (val: number) => {
    if (val >= 80) return 'text-emerald-400 border-emerald-500/40 bg-emerald-950/20';
    if (val >= 65) return 'text-teal-400 border-teal-500/40 bg-teal-950/20';
    if (val >= 50) return 'text-amber-400 border-amber-500/40 bg-amber-950/20';
    return 'text-rose-400 border-rose-500/40 bg-rose-950/20';
  };

  const getProgressColor = (val: number) => {
    if (val >= 80) return 'bg-emerald-500';
    if (val >= 65) return 'bg-teal-500';
    if (val >= 50) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  return (
    <div className={`p-5 rounded-2xl border transition-all ${highlight ? 'bg-slate-900 border-teal-500/50 shadow-lg shadow-teal-500/5' : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'}`}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">{title}</span>
          {weight !== undefined && (
            <span className="ml-2 text-xs font-mono text-slate-500">Weight: {Math.round(weight * 100)}%</span>
          )}
        </div>
        <div className={`text-2xl font-bold font-mono px-2.5 py-0.5 rounded-lg border ${getScoreColor(score)}`}>
          {Math.round(score)}%
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-800 rounded-full h-2 mb-2 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${getProgressColor(score)}`}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </div>

      {subtitle && <p className="text-xs text-slate-400 leading-relaxed mt-2">{subtitle}</p>}
    </div>
  );
};

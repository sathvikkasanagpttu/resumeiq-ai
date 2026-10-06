import React from 'react';

interface EvidenceBadgeProps {
  strength: 'verified' | 'weak' | 'inferred' | 'missing' | 'uncertain' | string;
  size?: 'sm' | 'md';
}

export const EvidenceBadge: React.FC<EvidenceBadgeProps> = ({ strength, size = 'md' }) => {
  const norm = strength.toLowerCase();

  const styles: Record<string, { bg: string; text: string; label: string; border: string }> = {
    verified: {
      bg: 'bg-emerald-950/60',
      text: 'text-emerald-400',
      border: 'border-emerald-800/60',
      label: 'Verified Evidence'
    },
    weak: {
      bg: 'bg-amber-950/60',
      text: 'text-amber-400',
      border: 'border-amber-800/60',
      label: 'Weak / Listed Only'
    },
    inferred: {
      bg: 'bg-sky-950/60',
      text: 'text-sky-400',
      border: 'border-sky-800/60',
      label: 'Inferred / Transferable'
    },
    missing: {
      bg: 'bg-rose-950/60',
      text: 'text-rose-400',
      border: 'border-rose-800/60',
      label: 'Missing Evidence'
    },
    uncertain: {
      bg: 'bg-slate-900',
      text: 'text-slate-400',
      border: 'border-slate-800',
      label: 'Uncertain'
    }
  };

  const current = styles[norm] || styles.uncertain;
  const padding = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center gap-1.5 font-medium rounded-full border ${current.bg} ${current.text} ${current.border} ${padding}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${norm === 'verified' ? 'bg-emerald-400' : (norm === 'weak' ? 'bg-amber-400' : (norm === 'missing' ? 'bg-rose-400' : 'bg-sky-400'))}`} />
      {current.label}
    </span>
  );
};

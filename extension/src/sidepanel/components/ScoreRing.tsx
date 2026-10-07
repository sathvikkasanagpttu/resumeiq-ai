import React from "react";

interface ScoreRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
}

export const ScoreRing: React.FC<ScoreRingProps> = ({
  score,
  size = 90,
  strokeWidth = 8,
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clampedScore = Math.min(100, Math.max(0, score));
  const offset = circumference - (clampedScore / 100) * circumference;

  const getColor = (s: number) => {
    if (s >= 80) return "#10b981"; // emerald-500
    if (s >= 65) return "#6366f1"; // indigo-500
    if (s >= 45) return "#f59e0b"; // amber-500
    return "#f43f5e";             // rose-500
  };

  const color = getColor(clampedScore);

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#f1f5f9"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          fill="transparent"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center text-center">
        <span className="text-xl font-extrabold text-slate-900 tracking-tight leading-none">
          {Math.round(clampedScore)}
          <span className="text-xs font-semibold text-slate-400">%</span>
        </span>
        <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider mt-0.5">
          Match
        </span>
      </div>
    </div>
  );
};

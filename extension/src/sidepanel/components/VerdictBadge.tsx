import React from "react";
import { CheckCircle2, TrendingUp, AlertTriangle, XCircle } from "lucide-react";
import { MatchVerdict } from "../../common/types";

interface VerdictBadgeProps {
  verdict: MatchVerdict;
}

export const VerdictBadge: React.FC<VerdictBadgeProps> = ({ verdict }) => {
  const getStyle = () => {
    switch (verdict) {
      case "Strong Match":
        return {
          bg: "bg-emerald-50 border-emerald-200 text-emerald-800",
          icon: <CheckCircle2 className="w-4 h-4 text-emerald-600" />,
        };
      case "Good Match":
        return {
          bg: "bg-indigo-50 border-indigo-200 text-indigo-800",
          icon: <TrendingUp className="w-4 h-4 text-indigo-600" />,
        };
      case "Partial Match":
        return {
          bg: "bg-amber-50 border-amber-200 text-amber-800",
          icon: <AlertTriangle className="w-4 h-4 text-amber-600" />,
        };
      case "Weak Match":
      default:
        return {
          bg: "bg-rose-50 border-rose-200 text-rose-800",
          icon: <XCircle className="w-4 h-4 text-rose-600" />,
        };
    }
  };

  const style = getStyle();

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border shadow-2xs ${style.bg}`}
    >
      {style.icon}
      <span>{verdict}</span>
    </div>
  );
};

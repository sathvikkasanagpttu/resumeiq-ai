import React from 'react';
import {
  LayoutDashboard, FileText, Briefcase, GitCompare, AlertTriangle,
  Wand2, Send, Compass, Sparkles, BarChart3, Settings, ShieldCheck
} from 'lucide-react';

export type NavTab =
  | 'dashboard'
  | 'resume-intelligence'
  | 'job-analyzer'
  | 'match-analysis'
  | 'skill-gaps'
  | 'resume-optimizer'
  | 'application-generator'
  | 'career-roadmap'
  | 'job-recommendations'
  | 'market-analytics'
  | 'settings';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'resume-intelligence', label: 'Resume Intelligence', icon: FileText },
    { id: 'job-analyzer', label: 'Job Analyzer', icon: Briefcase },
    { id: 'match-analysis', label: 'Match Analysis', icon: GitCompare },
    { id: 'skill-gaps', label: 'Skill Gaps', icon: AlertTriangle },
    { id: 'resume-optimizer', label: 'Resume Optimizer', icon: Wand2 },
    { id: 'application-generator', label: 'Application Generator', icon: Send },
    { id: 'career-roadmap', label: 'Career Roadmap', icon: Compass },
    { id: 'job-recommendations', label: 'Job Recommendations', icon: Sparkles },
    { id: 'market-analytics', label: 'Market Analytics', icon: BarChart3 },
    { id: 'settings', label: 'Verification & Config', icon: Settings },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950 flex flex-col justify-between p-4 flex-shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="space-y-1">
        <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500 px-3 py-2">
          Career Intelligence Suite
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id as NavTab)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all ${
                isActive
                  ? 'bg-teal-500/10 text-teal-400 border border-teal-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-teal-400' : 'text-slate-500'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* Core Principle Badge */}
      <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800/80 text-[11px] text-slate-400 space-y-1.5">
        <div className="flex items-center gap-1.5 font-semibold text-teal-400 text-xs">
          <ShieldCheck className="w-4 h-4" />
          <span>Core Principle</span>
        </div>
        <p className="leading-snug text-slate-400 italic">
          "Never optimize by inventing candidate experience."
        </p>
      </div>
    </aside>
  );
};

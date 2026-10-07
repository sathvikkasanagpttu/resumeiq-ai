import React, { useEffect, useState } from 'react';
import { ShieldCheck, Activity, User, Bell, Sparkles, Database, LogOut } from 'lucide-react';
import { api, setAuthToken } from '../services/api';

export const Navbar: React.FC = () => {
  const [health, setHealth] = useState<any>(null);
  const [user, setUser] = useState<any>(null);

  const loadUser = () => {
    api.getMe().then(setUser).catch(() => setUser(null));
  };

  useEffect(() => {
    api.getHealth().then(setHealth).catch(() => setHealth({ status: 'offline' }));
    loadUser();

    const handleLogoutEvent = () => {
      setUser(null);
    };
    window.addEventListener('resumeiq:logout', handleLogoutEvent);
    return () => window.removeEventListener('resumeiq:logout', handleLogoutEvent);
  }, []);

  const handleLogout = () => {
    setAuthToken(null);
    setUser(null);
    window.dispatchEvent(new CustomEvent('resumeiq:logout'));
  };

  const getInitials = (name?: string) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map((part) => part[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Brand & Tagline */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-teal-600 to-emerald-400 flex items-center justify-center shadow-lg shadow-teal-500/20 text-white font-black text-lg">
            RQ
          </div>
          <div>
            <div className="font-extrabold text-base tracking-tight text-white flex items-center gap-2">
              RESUME<span className="text-teal-400">IQ</span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-teal-950 text-teal-400 border border-teal-800">
                Evidence-First Engine
              </span>
            </div>
            <div className="text-[10px] text-slate-400 tracking-wide">
              Zero Fabrication • Grounded Career Intelligence
            </div>
          </div>
        </div>
      </div>

      {/* Engine Status & Account */}
      <div className="flex items-center gap-4">
        {/* System Health Badge */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs text-slate-300">
          <span className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
          <span className="font-medium font-mono text-[11px]">
            {health?.status === 'healthy' ? 'AI Verification Engine Online' : 'Connecting to Core...'}
          </span>
        </div>

        {/* User Profile */}
        <div className="flex items-center gap-3 pl-3 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-teal-300 font-semibold text-xs">
            {getInitials(user?.full_name)}
          </div>
          <div className="hidden md:block text-left">
            <div className="text-xs font-semibold text-white">
              {user?.full_name || 'Authenticated User'}
            </div>
            <div className="text-[10px] text-slate-400 font-mono">
              {user?.email || 'Logged In'}
            </div>
          </div>
          {user && (
            <button
              onClick={handleLogout}
              className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition"
              title="Sign Out"
              aria-label="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </header>
  );
};

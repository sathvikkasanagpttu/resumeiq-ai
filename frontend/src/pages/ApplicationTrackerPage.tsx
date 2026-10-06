import React, { useState, useEffect } from 'react';
import {
  Briefcase, Plus, Trash2, Edit3, CheckCircle2, Clock, Check, X,
  AlertCircle, ArrowRight, ExternalLink, Calendar, Filter
} from 'lucide-react';
import { api } from '../services/api';
import { TrackerItem, TrackerStage, TrackerItemCreate } from '../types';

export const ApplicationTrackerPage: React.FC = () => {
  const [items, setItems] = useState<TrackerItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // New Item Modal
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false);
  const [newTitle, setNewTitle] = useState<string>('');
  const [newCompany, setNewCompany] = useState<string>('');
  const [newStage, setNewStage] = useState<TrackerStage>('saved');
  const [newNotes, setNewNotes] = useState<string>('');
  const [creating, setCreating] = useState<boolean>(false);

  useEffect(() => {
    loadItems();
  }, []);

  const loadItems = async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await api.listTrackerItems();
      setItems(list);
    } catch (err: any) {
      setError(err.message || 'Failed to load application tracker items.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newCompany.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const payload: TrackerItemCreate = {
        job_title: newTitle.trim(),
        company_name: newCompany.trim(),
        stage: newStage,
        notes: newNotes.trim() || undefined
      };
      const created = await api.createTrackerItem(payload);
      setItems((prev) => [created, ...prev]);
      setIsCreateOpen(false);
      setNewTitle('');
      setNewCompany('');
      setNewStage('saved');
      setNewNotes('');
    } catch (err: any) {
      setError(err.message || 'Failed to create application item.');
    } finally {
      setCreating(false);
    }
  };

  const handleStageChange = async (itemId: string, newStg: TrackerStage) => {
    try {
      const updated = await api.updateTrackerItem(itemId, { stage: newStg });
      setItems((prev) => prev.map((it) => (it.id === itemId ? updated : it)));
    } catch (err: any) {
      setError(err.message || 'Failed to update stage.');
    }
  };

  const handleDelete = async (itemId: string) => {
    try {
      await api.deleteTrackerItem(itemId);
      setItems((prev) => prev.filter((it) => it.id !== itemId));
    } catch (err: any) {
      setError(err.message || 'Failed to delete item.');
    }
  };

  const stages: { id: TrackerStage; label: string; color: string; badge: string }[] = [
    { id: 'saved', label: 'Saved / Target', color: 'border-slate-700 bg-slate-900/40', badge: 'bg-slate-800 text-slate-300' },
    { id: 'applied', label: 'Applied', color: 'border-blue-900/50 bg-blue-950/20', badge: 'bg-blue-950 text-blue-300 border border-blue-800' },
    { id: 'interviewing', label: 'Interviewing', color: 'border-amber-900/50 bg-amber-950/20', badge: 'bg-amber-950 text-amber-300 border border-amber-800' },
    { id: 'offer', label: 'Offer Received', color: 'border-emerald-900/50 bg-emerald-950/20', badge: 'bg-emerald-950 text-emerald-300 border border-emerald-800' },
    { id: 'rejected', label: 'Archived', color: 'border-rose-900/30 bg-rose-950/10', badge: 'bg-rose-950/60 text-rose-400 border border-rose-900' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400">
              <Briefcase className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
                Application Tracker
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-teal-500/20 text-teal-300 font-mono">
                  {items.length} Active
                </span>
              </h1>
              <p className="text-xs text-slate-400">
                Track your job application stages, interview rounds, and tailored resume versions.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={() => setIsCreateOpen(true)}
          className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-semibold text-xs transition-colors shadow-lg shadow-teal-600/20 flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          <span>New Application</span>
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-400 hover:text-rose-200">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Kanban Board Grid */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400 space-y-3">
          <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm">Loading applications...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-start">
          {stages.map((stg) => {
            const colItems = items.filter((it) => it.stage === stg.id);
            return (
              <div
                key={stg.id}
                className={`p-4 rounded-2xl border ${stg.color} min-h-[450px] flex flex-col space-y-3`}
              >
                {/* Column Header */}
                <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                  <span className="text-xs font-bold text-slate-200">{stg.label}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full font-mono font-bold bg-slate-800 text-slate-400">
                    {colItems.length}
                  </span>
                </div>

                {/* Cards */}
                <div className="flex-1 space-y-3 overflow-y-auto">
                  {colItems.length === 0 ? (
                    <div className="py-8 text-center text-[11px] text-slate-500 italic">
                      No applications
                    </div>
                  ) : (
                    colItems.map((item) => (
                      <div
                        key={item.id}
                        className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all text-xs space-y-2 shadow-sm"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <h4 className="font-bold text-slate-100 leading-snug">{item.job_title}</h4>
                          <button
                            onClick={() => handleDelete(item.id)}
                            className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                            title="Delete application"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>

                        <div className="text-slate-400 font-medium text-[11px]">{item.company_name}</div>

                        {item.notes && (
                          <p className="text-[11px] text-slate-400 italic bg-slate-950/60 p-2 rounded border border-slate-800/60">
                            {item.notes}
                          </p>
                        )}

                        {/* Stage Selector */}
                        <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between">
                          <select
                            value={item.stage}
                            onChange={(e) => handleStageChange(item.id, e.target.value as TrackerStage)}
                            className="text-[10px] bg-slate-950 border border-slate-700 rounded px-1.5 py-0.5 text-slate-300 focus:outline-none focus:border-teal-500"
                          >
                            <option value="saved">Saved</option>
                            <option value="applied">Applied</option>
                            <option value="interviewing">Interviewing</option>
                            <option value="offer">Offer</option>
                            <option value="rejected">Archived</option>
                          </select>

                          {item.created_at && (
                            <span className="text-[10px] text-slate-500 font-mono">
                              {new Date(item.created_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="relative w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-teal-400" />
                Add New Job Application
              </h3>
              <button
                onClick={() => setIsCreateOpen(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Job Title *</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Senior Machine Learning Engineer"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-slate-200 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Company Name *</label>
                <input
                  type="text"
                  required
                  value={newCompany}
                  onChange={(e) => setNewCompany(e.target.value)}
                  placeholder="e.g. Stripe, OpenAI, Google"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-slate-200 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Current Stage</label>
                <select
                  value={newStage}
                  onChange={(e) => setNewStage(e.target.value as TrackerStage)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-slate-200 focus:outline-none focus:border-teal-500"
                >
                  <option value="saved">Saved / Target</option>
                  <option value="applied">Applied</option>
                  <option value="interviewing">Interviewing</option>
                  <option value="offer">Offer Received</option>
                  <option value="rejected">Archived</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Notes / Referral / Links</label>
                <textarea
                  rows={3}
                  value={newNotes}
                  onChange={(e) => setNewNotes(e.target.value)}
                  placeholder="Add interview dates, recruiter contact, or notes..."
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-slate-200 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-semibold transition-colors disabled:opacity-50"
                >
                  {creating ? 'Saving...' : 'Add Application'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default ApplicationTrackerPage;

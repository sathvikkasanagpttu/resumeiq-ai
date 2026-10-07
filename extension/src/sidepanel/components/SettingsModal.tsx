import React, { useState } from "react";
import { Settings, X, Check, RotateCcw } from "lucide-react";
import { ExtSettings } from "../../common/types";
import { DEFAULT_SETTINGS } from "../../common/constants";

interface SettingsModalProps {
  settings: ExtSettings;
  onSave: (settings: Partial<ExtSettings>) => Promise<void>;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  settings,
  onSave,
  onClose,
}) => {
  const [form, setForm] = useState<ExtSettings>({ ...settings });
  const [savedToast, setSavedToast] = useState(false);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSave(form);
    setSavedToast(true);
    setTimeout(() => {
      setSavedToast(false);
      onClose();
    }, 800);
  };

  const handleReset = () => {
    setForm({ ...DEFAULT_SETTINGS });
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-3 animate-in fade-in">
      <div className="bg-white rounded-2xl shadow-xl w-full max-h-[85vh] flex flex-col border border-slate-200 overflow-hidden">
        <div className="p-3.5 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2">
            <Settings className="w-4 h-4 text-indigo-600" />
            <h3 className="font-bold text-xs text-slate-900">
              Extension Settings & Thresholds
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-700 rounded-md"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSave} className="p-4 space-y-4 overflow-y-auto flex-1">
          {/* Backend URL */}
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700">
              Backend API Base URL
            </label>
            <input
              type="text"
              value={form.api_base_url}
              onChange={(e) => setForm({ ...form, api_base_url: e.target.value })}
              className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono text-slate-800"
            />
          </div>

          {/* Thresholds */}
          <div className="space-y-3 pt-2 border-t border-slate-100">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
              Match Verdict Thresholds (%)
            </span>

            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-700 font-medium">Strong Match (Emerald)</span>
                <span className="font-bold text-slate-900 font-mono">≥ {form.threshold_strong}%</span>
              </div>
              <input
                type="range"
                min={70}
                max={95}
                value={form.threshold_strong}
                onChange={(e) => setForm({ ...form, threshold_strong: Number(e.target.value) })}
                className="w-full accent-emerald-600"
              />
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-700 font-medium">Good Match (Indigo)</span>
                <span className="font-bold text-slate-900 font-mono">≥ {form.threshold_good}%</span>
              </div>
              <input
                type="range"
                min={50}
                max={79}
                value={form.threshold_good}
                onChange={(e) => setForm({ ...form, threshold_good: Number(e.target.value) })}
                className="w-full accent-indigo-600"
              />
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-700 font-medium">Partial Match (Amber)</span>
                <span className="font-bold text-slate-900 font-mono">≥ {form.threshold_partial}%</span>
              </div>
              <input
                type="range"
                min={30}
                max={55}
                value={form.threshold_partial}
                onChange={(e) => setForm({ ...form, threshold_partial: Number(e.target.value) })}
                className="w-full accent-amber-600"
              />
            </div>
            <p className="text-[10px] text-slate-400">
              Scores below {form.threshold_partial}% will be labeled as "Weak Match" (Rose).
            </p>
          </div>

          {/* Feature Toggles */}
          <div className="space-y-2 pt-2 border-t border-slate-100">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={form.auto_match_on_open}
                onChange={(e) => setForm({ ...form, auto_match_on_open: e.target.checked })}
                className="rounded text-indigo-600 accent-indigo-600"
              />
              <span className="text-xs text-slate-700 font-medium">
                Auto-compute match when opening Side Panel
              </span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={form.floating_button_enabled}
                onChange={(e) => setForm({ ...form, floating_button_enabled: e.target.checked })}
                className="rounded text-indigo-600 accent-indigo-600"
              />
              <span className="text-xs text-slate-700 font-medium">
                Show floating "⚡ Match" button on detected job posts
              </span>
            </label>
          </div>

          {/* Footer buttons */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
            <button
              type="button"
              onClick={handleReset}
              className="text-xs text-slate-500 hover:text-slate-800 flex items-center gap-1"
            >
              <RotateCcw className="w-3 h-3" />
              Reset Defaults
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs rounded-lg shadow-2xs flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              {savedToast ? (
                <>
                  <Check className="w-3.5 h-3.5" />
                  Saved!
                </>
              ) : (
                "Save Preferences"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

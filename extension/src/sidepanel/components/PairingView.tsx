import React, { useState } from "react";
import { KeyRound, ShieldCheck, ArrowRight, Server, AlertCircle, Loader2 } from "lucide-react";
import { apiClient } from "../../common/api-client";
import { DEFAULT_API_BASE_URL } from "../../common/constants";
import { ExtStoredAuth } from "../../common/types";

interface PairingViewProps {
  onPaired: (auth: ExtStoredAuth) => void;
  defaultServerUrl?: string;
}

export const PairingView: React.FC<PairingViewProps> = ({
  onPaired,
  defaultServerUrl = DEFAULT_API_BASE_URL,
}) => {
  const [code, setCode] = useState("");
  const [serverUrl, setServerUrl] = useState(defaultServerUrl);
  const [showServerConfig, setShowServerConfig] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePair = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim()) {
      setError("Please enter the 6-character pairing code.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const auth = await apiClient.pair(code, serverUrl);
      onPaired(auth);
    } catch (err: any) {
      setError(err.message || "Failed to pair with ResumeIQ. Check the code and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-md mx-auto space-y-6">
      <div className="text-center space-y-2">
        <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 text-indigo-600 mx-auto flex items-center justify-center shadow-xs">
          <KeyRound className="w-6 h-6" />
        </div>
        <h2 className="text-lg font-bold text-slate-900 tracking-tight">
          Pair with ResumeIQ
        </h2>
        <p className="text-xs text-slate-600 leading-relaxed">
          Connect this browser extension to your ResumeIQ account to enable one-click resume matching directly on job posts.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 flex items-start gap-2 animate-in fade-in">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <p className="leading-snug">{error}</p>
        </div>
      )}

      <form onSubmit={handlePair} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5 uppercase tracking-wider">
            Pairing Code
          </label>
          <div className="relative">
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              placeholder="e.g. 849201"
              maxLength={12}
              className="w-full px-4 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 font-mono text-center text-lg tracking-widest uppercase focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 shadow-2xs placeholder:text-slate-300"
            />
          </div>
          <p className="mt-1.5 text-[11px] text-slate-500">
            Find your pairing code in <span className="font-medium text-slate-700">ResumeIQ Web App → Settings → Integrations</span>.
          </p>
        </div>

        <div>
          <button
            type="button"
            onClick={() => setShowServerConfig(!showServerConfig)}
            className="text-[11px] font-medium text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
          >
            <Server className="w-3 h-3" />
            {showServerConfig ? "Hide Backend URL Config" : "Configure Backend Server URL"}
          </button>

          {showServerConfig && (
            <div className="mt-2 p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1.5 animate-in fade-in">
              <label className="block text-[11px] font-medium text-slate-600">
                API Base Endpoint
              </label>
              <input
                type="text"
                value={serverUrl}
                onChange={(e) => setServerUrl(e.target.value)}
                placeholder="http://localhost:8000/api/v1"
                className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded font-mono text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={loading || !code.trim()}
          className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 disabled:bg-slate-300 text-white font-medium text-sm rounded-lg shadow-sm flex items-center justify-center gap-2 transition-colors cursor-pointer disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Pairing Device...
            </>
          ) : (
            <>
              Pair Extension
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </form>

      <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Zero Password Storage</span>
        </div>
        <p className="text-[11px] text-slate-600 leading-relaxed">
          The extension securely uses a scoped, revocable access token. No passwords or sensitive profile credentials are ever stored in the browser.
        </p>
      </div>
    </div>
  );
};

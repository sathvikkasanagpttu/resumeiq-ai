import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon, ShieldCheck, Database, Key,
  Sliders, Search, Sparkles, CheckCircle2, AlertCircle, Cpu,
  KeyRound, Copy, Check, Laptop, Trash2, RefreshCw
} from 'lucide-react';
import { api } from '../services/api';

export const SettingsPage: React.FC = () => {
  const [health, setHealth] = useState<any>(null);
  const [user, setUser] = useState<any>(null);
  const [ragQuery, setRagQuery] = useState('Google XYZ formula resume bullets');
  const [ragResults, setRagResults] = useState<any[]>([]);
  const [searchingRag, setSearchingRag] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [savedKey, setSavedKey] = useState(false);
  
  // Extension pairing & device management state
  const [pairingCode, setPairingCode] = useState<string | null>(null);
  const [codeCountdown, setCodeCountdown] = useState<number>(0);
  const [generatingCode, setGeneratingCode] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);
  const [devices, setDevices] = useState<any[]>([]);
  const [loadingDevices, setLoadingDevices] = useState(false);
  const [deviceActionMsg, setDeviceActionMsg] = useState<string | null>(null);

  const fetchDevices = () => {
    setLoadingDevices(true);
    api.listExtensionDevices()
      .then(setDevices)
      .catch(() => setDevices([]))
      .finally(() => setLoadingDevices(false));
  };

  useEffect(() => {
    api.getHealth().then(setHealth).catch(() => setHealth({ status: 'offline' }));
    api.getMe().then(setUser).catch(() => setUser(null));
    fetchDevices();
  }, []);

  // Countdown timer for pairing code
  useEffect(() => {
    if (codeCountdown <= 0) {
      if (pairingCode) setPairingCode(null);
      return;
    }
    const timer = setInterval(() => {
      setCodeCountdown((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [codeCountdown, pairingCode]);

  const handleGeneratePairingCode = async () => {
    setGeneratingCode(true);
    setDeviceActionMsg(null);
    try {
      const res = await api.generatePairingCode();
      setPairingCode(res.pairing_code);
      setCodeCountdown(res.expires_in_seconds || 300);
    } catch (err: any) {
      setDeviceActionMsg(`Failed to generate code: ${err.message || 'Error'}`);
    } finally {
      setGeneratingCode(false);
    }
  };

  const handleRevokeDevice = async (deviceId: string) => {
    try {
      await api.revokeExtensionDevice(deviceId);
      setDeviceActionMsg(`Device ${deviceId} successfully revoked.`);
      fetchDevices();
    } catch (err: any) {
      setDeviceActionMsg(`Failed to revoke device: ${err.message || 'Error'}`);
    }
  };

  const handleSearchRAG = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ragQuery) return;
    setSearchingRag(true);
    try {
      const res = await fetch(`/api/v1/rag/search?q=${encodeURIComponent(ragQuery)}&top_k=3`);
      const data = await res.json();
      setRagResults(data.results || []);
    } catch (err) {
      console.error(err);
    } finally {
      setSearchingRag(false);
    }
  };

  const handleSaveKey = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedKey(true);
    setTimeout(() => setSavedKey(false), 2000);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-teal-400" /> Verification, RAG & Engine Config
        </h1>
        <p className="text-sm text-slate-400">
          Inspect core AI verification telemetry, test hybrid RAG knowledge retrieval, and manage paired browser devices.
        </p>
      </div>

      {/* Core Integrity Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Database Connection</span>
            <Database className="w-4 h-4 text-teal-400" />
          </div>
          <div className="text-xl font-bold text-white flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${health?.database_connected ? 'bg-emerald-400' : 'bg-red-400'}`} />
            {health?.database_connected ? 'Connected' : 'Disconnected'}
          </div>
          <p className="text-xs text-slate-500">PostgreSQL / SQLite Storage Engine</p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>RAG Knowledge Base</span>
            <Cpu className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-xl font-bold text-white flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
            6 Chunks Synced
          </div>
          <p className="text-xs text-slate-500">Dense vectors + BM25 Lexical Inverted Index</p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Active Account</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-white truncate">
            {user?.full_name || 'Authenticated User'}
          </div>
          <p className="text-xs text-slate-500 truncate font-mono">{user?.email || 'Logged In'}</p>
        </div>
      </div>

      {/* Hybrid RAG Tester */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Search className="w-5 h-5 text-teal-400" /> Hybrid RAG Retriever Test Bench
        </h3>
        <p className="text-xs text-slate-400">
          Query the in-memory knowledge store combining dense semantic embeddings and sparse BM25 scoring with Reciprocal Rank Fusion (RRF).
        </p>

        <form onSubmit={handleSearchRAG} className="flex gap-3">
          <input
            type="text"
            value={ragQuery}
            onChange={(e) => setRagQuery(e.target.value)}
            placeholder="Search resume knowledge..."
            className="flex-1 px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
          />
          <button
            type="submit"
            disabled={searchingRag}
            className="px-5 py-2.5 bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold flex items-center gap-2 transition"
          >
            {searchingRag ? 'Searching...' : 'Execute Hybrid Search'}
          </button>
        </form>

        {ragResults.length > 0 && (
          <div className="space-y-3 pt-2">
            {ragResults.map((r, i) => (
              <div key={i} className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-teal-300">{r.title}</span>
                  <span className="font-mono text-slate-500 text-[10px]">RRF Score: {r.score}</span>
                </div>
                <p className="text-slate-300 leading-relaxed font-mono text-[11px] whitespace-pre-wrap">{r.content}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Model & API Credentials */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Key className="w-5 h-5 text-sky-400" /> AI Provider & Credentials
        </h3>
        <p className="text-xs text-slate-400">
          ResumeIQ functions with deterministic semantic embeddings and feature projection.
          Optionally provide a Gemini API Key to enable live cloud models.
        </p>

        <form onSubmit={handleSaveKey} className="flex flex-col sm:flex-row gap-3 max-w-xl">
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Enter GEMINI_API_KEY (optional)..."
            className="flex-1 px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-white placeholder-slate-600 focus:outline-none focus:border-teal-500"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold border border-slate-700 transition"
          >
            {savedKey ? 'Saved' : 'Save Key'}
          </button>
        </form>
      </div>

      {/* Chrome Extension Pairing & Device Management */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-indigo-400" /> Chrome Extension Pairing & Device Management
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Securely pair browser extension sessions using single-use 5-minute pairing codes with refresh rotation.
            </p>
          </div>
          <span className="px-2.5 py-1 text-[11px] font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            Active: {user?.full_name || 'Authenticated User'}
          </span>
        </div>

        {deviceActionMsg && (
          <div className="p-3 rounded-xl bg-indigo-950/60 border border-indigo-800/60 text-xs text-indigo-200">
            {deviceActionMsg}
          </div>
        )}

        {/* Generate One-Time Pairing Code Card */}
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
          <div className="space-y-2">
            <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block">
              One-Time Single-Use Pairing Code
            </span>
            {pairingCode ? (
              <div className="flex items-center gap-3">
                <span className="font-mono text-3xl font-extrabold tracking-widest text-indigo-400 bg-indigo-950/60 px-4 py-1.5 rounded-xl border border-indigo-700/50 shadow-inner">
                  {pairingCode}
                </span>
                <button
                  type="button"
                  onClick={() => {
                    navigator.clipboard.writeText(pairingCode);
                    setCopiedCode(true);
                    setTimeout(() => setCopiedCode(false), 2500);
                  }}
                  className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 transition shadow-md shadow-indigo-600/20 cursor-pointer"
                >
                  {copiedCode ? <Check className="w-4 h-4 text-emerald-300" /> : <Copy className="w-4 h-4" />}
                  {copiedCode ? "Copied!" : "Copy Code"}
                </button>
              </div>
            ) : (
              <button
                type="button"
                disabled={generatingCode}
                onClick={handleGeneratePairingCode}
                className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold flex items-center gap-2 transition cursor-pointer shadow-md shadow-indigo-600/20"
              >
                {generatingCode ? 'Generating...' : 'Generate New 5-Minute Pairing Code'}
              </button>
            )}

            {pairingCode && (
              <p className="text-[11px] text-amber-400 font-mono">
                Expires in {Math.floor(codeCountdown / 60)}m {codeCountdown % 60}s • Single-use only
              </p>
            )}
          </div>

          <div className="text-xs text-slate-400 bg-slate-900/80 p-3.5 rounded-xl border border-slate-800/80 max-w-sm space-y-1.5">
            <p className="text-slate-200 font-semibold flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" /> Pairing Instructions:
            </p>
            <ol className="list-decimal list-inside space-y-1 text-[11px] text-slate-400 leading-relaxed">
              <li>Open the ResumeIQ side panel in your browser.</li>
              <li>Paste the code generated above into the <strong>PAIRING CODE</strong> box.</li>
              <li>Click <strong>Pair Extension →</strong> to connect securely.</li>
            </ol>
          </div>
        </div>

        {/* Paired Extension Devices Table */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <Laptop className="w-4 h-4 text-slate-400" /> Paired Extension Devices ({devices.length})
            </h4>
            <button
              onClick={fetchDevices}
              disabled={loadingDevices}
              className="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingDevices ? 'animate-spin' : ''}`} /> Refresh
            </button>
          </div>

          {devices.length === 0 ? (
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center text-xs text-slate-500">
              No paired extension devices found. Generate a pairing code above to pair your first device.
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
                  <tr>
                    <th className="p-3">Device Name</th>
                    <th className="p-3">Device ID</th>
                    <th className="p-3">Last Active</th>
                    <th className="p-3">Status</th>
                    <th className="p-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 bg-slate-900/60 text-slate-300">
                  {devices.map((dev) => (
                    <tr key={dev.id} className="hover:bg-slate-800/40 transition">
                      <td className="p-3 font-semibold text-white">{dev.device_name || 'Chrome Extension'}</td>
                      <td className="p-3 font-mono text-slate-400">{dev.device_id.substring(0, 16)}...</td>
                      <td className="p-3 font-mono text-slate-400">
                        {dev.last_used_at ? new Date(dev.last_used_at).toLocaleDateString() : 'Never'}
                      </td>
                      <td className="p-3">
                        {dev.is_revoked ? (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
                            Revoked
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            Active
                          </span>
                        )}
                      </td>
                      <td className="p-3 text-right">
                        {!dev.is_revoked && (
                          <button
                            onClick={() => handleRevokeDevice(dev.device_id)}
                            className="px-2.5 py-1 rounded-lg bg-red-950/40 hover:bg-red-900/60 text-red-300 text-[11px] font-semibold border border-red-800/60 transition cursor-pointer"
                          >
                            Revoke Device
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import {
  Send, FileText, MessageSquare, HelpCircle, ShieldCheck,
  Sparkles, Copy, Check, Quote, AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import { GeneratedMaterial } from '../types';

interface ApplicationGeneratorPageProps {
  selectedMatchId?: string | null;
}

export const ApplicationGeneratorPage: React.FC<ApplicationGeneratorPageProps> = ({
  selectedMatchId
}) => {
  const [docType, setDocType] = useState<'cover_letter' | 'recruiter_message' | 'interview_qa'>('cover_letter');
  const [material, setMaterial] = useState<GeneratedMaterial | null>(null);
  const [generating, setGenerating] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!selectedMatchId) return;

    setGenerating(true);
    setError(null);
    try {
      const res = await api.generateMaterial(selectedMatchId, docType);
      setMaterial(res);
    } catch (err: any) {
      setError(err.message || 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const copyToClipboard = () => {
    if (!material) return;
    navigator.clipboard.writeText(material.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <Send className="w-6 h-6 text-teal-400" /> Evidence-Grounded Application Generator
          </h1>
          <p className="text-sm text-slate-400">
            Generate bespoke cover letters, recruiter outreach messages, and interview answers with cited resume evidence.
          </p>
        </div>

        <button
          onClick={handleGenerate}
          disabled={generating || !selectedMatchId}
          className="px-5 py-2.5 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-teal-600/20 transition flex items-center gap-2"
        >
          <Sparkles className="w-4 h-4" />
          <span>{generating ? 'Verifying Evidence & Generating...' : 'Generate Grounded Document'}</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Document Type Selector Tabs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <button
          onClick={() => setDocType('cover_letter')}
          className={`p-5 rounded-2xl border text-left transition flex items-start gap-4 ${
            docType === 'cover_letter'
              ? 'bg-teal-950/40 border-teal-800 shadow-md'
              : 'bg-slate-900 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="p-2.5 rounded-xl bg-slate-950 text-teal-400 border border-slate-800">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-bold text-white">Cover Letter</div>
            <p className="text-xs text-slate-400 mt-0.5">Under 350 words, citing verified accomplishments</p>
          </div>
        </button>

        <button
          onClick={() => setDocType('recruiter_message')}
          className={`p-5 rounded-2xl border text-left transition flex items-start gap-4 ${
            docType === 'recruiter_message'
              ? 'bg-teal-950/40 border-teal-800 shadow-md'
              : 'bg-slate-900 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="p-2.5 rounded-xl bg-slate-950 text-sky-400 border border-slate-800">
            <MessageSquare className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-bold text-white">Recruiter Outreach</div>
            <p className="text-xs text-slate-400 mt-0.5">High-conversion message under 150 words</p>
          </div>
        </button>

        <button
          onClick={() => setDocType('interview_qa')}
          className={`p-5 rounded-2xl border text-left transition flex items-start gap-4 ${
            docType === 'interview_qa'
              ? 'bg-teal-950/40 border-teal-800 shadow-md'
              : 'bg-slate-900 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="p-2.5 rounded-xl bg-slate-950 text-purple-400 border border-slate-800">
            <HelpCircle className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-bold text-white">Interview Q&A</div>
            <p className="text-xs text-slate-400 mt-0.5">Role-specific behavioral & technical questions</p>
          </div>
        </button>
      </div>

      {/* Generated Content Output */}
      {material ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Main Document Content (8 cols) */}
          <div className="lg:col-span-8 space-y-4">
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div>
                  <span className="text-xs uppercase font-mono text-teal-400 tracking-wider">Generated Document</span>
                  <h3 className="text-base font-bold text-white">{material.title}</h3>
                </div>
                <button
                  onClick={copyToClipboard}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 transition flex items-center gap-1.5"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Copied' : 'Copy Text'}</span>
                </button>
              </div>

              <pre className="p-6 rounded-xl bg-slate-950 border border-slate-800/90 text-xs font-mono text-slate-200 whitespace-pre-wrap leading-relaxed">
                {material.content}
              </pre>
            </div>
          </div>

          {/* Evidence Citations Panel (4 cols) */}
          <div className="lg:col-span-4 space-y-4">
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <div className="flex items-center gap-2 text-xs font-bold text-teal-400 uppercase tracking-wider">
                <ShieldCheck className="w-4 h-4" /> Supporting Evidence Audit
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                <div className="text-slate-400 mb-1">Verification Status</div>
                <div className="font-mono text-emerald-400 font-bold">[{material.verification_status.toUpperCase()}]</div>
                <div className="text-[10px] text-slate-500 mt-1">Confidence: {Math.round(material.confidence_score * 100)}%</div>
              </div>

              <div className="space-y-3">
                <span className="text-xs font-bold text-slate-300">Grounded Resume Citations:</span>
                {material.grounded_citations.map((c, i) => (
                  <div key={i} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                    <div className="text-[10px] font-semibold text-teal-400">{c.paragraph_or_claim}</div>
                    <div className="text-slate-300 italic font-mono text-[11px] border-l-2 border-teal-500 pl-2">
                      "{c.cited_resume_evidence}"
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="p-16 text-center border-2 border-dashed border-slate-800 rounded-3xl bg-slate-900/40 text-xs text-slate-500 space-y-3">
          <Sparkles className="w-8 h-8 text-teal-500 mx-auto" />
          <p>Click 'Generate Grounded Document' above to produce evidence-backed application text.</p>
        </div>
      )}
    </div>
  );
};

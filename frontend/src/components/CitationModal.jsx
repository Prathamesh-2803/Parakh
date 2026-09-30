import React from 'react';
import { ExternalLink, X, ShieldCheck, FileText, Building2 } from 'lucide-react';

export function CitationModal({ show, onClose, citation }) {
  if (!show || !citation) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
      <div
        className="relative w-full max-w-lg bg-white rounded-lg shadow-xl border border-slate-300 overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-labelledby="citation-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 bg-slate-50 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-slate-200 text-slate-800 rounded">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h3 id="citation-title" className="text-sm font-semibold text-slate-900">
                Official Document Citation
              </h3>
              <p className="text-xs text-slate-500">Bureau of Indian Standards Reference</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-700 rounded hover:bg-slate-200 transition cursor-pointer"
            aria-label="Close modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Standard / Publication
            </span>
            <div className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>{citation.source || "Bureau of Indian Standards"}</span>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                <ShieldCheck className="w-3.5 h-3.5 mr-1" />
                Verified Context
              </span>
            </div>
          </div>

          {citation.section && (
            <div className="space-y-1">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Clause / Section
              </span>
              <div className="text-xs font-medium text-slate-800 bg-slate-100 p-2.5 rounded border border-slate-200 font-mono">
                {citation.section}
              </div>
            </div>
          )}

          {citation.text && (
            <div className="space-y-1">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Extracted Grounding Excerpt
              </span>
              <blockquote className="text-xs text-slate-700 bg-slate-50 border-l-3 border-slate-400 p-3 rounded-r leading-relaxed">
                "{citation.text}"
              </blockquote>
            </div>
          )}

          <div className="pt-2">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-600 bg-slate-50 p-3 rounded border border-slate-200">
              <div className="flex items-start gap-2">
                <Building2 className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-slate-800 block">Cross-reference at BIS Official Portal</span>
                  <span className="text-slate-500">View complete standard gazette and certification rules.</span>
                </div>
              </div>
              <a
                href={citation.url || "https://www.bis.gov.in/"}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium rounded transition shrink-0"
              >
                <span>Visit Official Source</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 bg-slate-50 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-3 py-1.5 bg-white hover:bg-slate-100 text-slate-700 text-xs font-medium border border-slate-300 rounded transition cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

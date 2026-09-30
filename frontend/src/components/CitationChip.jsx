import React from 'react';
import { FileText, ExternalLink } from 'lucide-react';

export function CitationChip({ citation, onClick }) {
  if (!citation || !citation.source) return null;

  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium bg-slate-100 hover:bg-slate-200/90 text-slate-800 border border-slate-300 rounded-md transition shadow-xs group cursor-pointer"
      title={`View authoritative reference for ${citation.source}`}
    >
      <FileText className="w-3.5 h-3.5 text-slate-600" />
      <span className="font-semibold text-slate-900">{citation.source}</span>
      {citation.section && (
        <span className="text-slate-600 font-normal truncate max-w-[140px]">
          ({citation.section})
        </span>
      )}
      <ExternalLink className="w-3 h-3 text-slate-400 group-hover:text-slate-700 transition-colors" />
    </button>
  );
}

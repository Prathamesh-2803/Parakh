import React from 'react';
import { ArrowRight } from 'lucide-react';

export function FollowUpChip({ suggestion, onClick }) {
  if (!suggestion) return null;

  return (
    <button
      type="button"
      onClick={() => onClick(suggestion)}
      className="inline-flex items-center justify-between gap-2 px-3 py-1.5 text-xs text-slate-700 bg-white hover:bg-slate-50 hover:text-slate-900 border border-slate-300 hover:border-slate-400 rounded-md transition text-left group shadow-xs cursor-pointer w-full sm:w-auto"
    >
      <span className="font-medium line-clamp-1">{suggestion}</span>
      <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-700 transition-colors shrink-0" />
    </button>
  );
}

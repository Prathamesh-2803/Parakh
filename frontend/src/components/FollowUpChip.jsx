import React from 'react';
import { ArrowRight, CornerDownRight } from 'lucide-react';

export function FollowUpChip({ suggestion, onClick }) {
  if (!suggestion) return null;

  return (
    <button
      type="button"
      onClick={(e) => {
        e.preventDefault();
        onClick(suggestion);
      }}
      className="w-full text-left px-3 py-2 sm:py-2.5 rounded-lg bg-blue-50/80 hover:bg-blue-100/90 active:bg-blue-200/90 border border-blue-200/80 hover:border-blue-300 transition-all flex items-start sm:items-center justify-between gap-2.5 group cursor-pointer shadow-2xs touch-manipulation"
    >
      <div className="flex items-start gap-2 min-w-0">
        <CornerDownRight className="w-3.5 h-3.5 text-blue-600 shrink-0 mt-0.5" />
        <span className="text-xs text-blue-950 font-medium leading-snug">
          {suggestion}
        </span>
      </div>
      <ArrowRight className="w-3.5 h-3.5 text-blue-400 group-hover:text-blue-700 group-hover:translate-x-0.5 transition-all shrink-0 mt-0.5 sm:mt-0" />
    </button>
  );
}

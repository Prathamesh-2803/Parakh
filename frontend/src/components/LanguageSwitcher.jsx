import React from 'react';
import { Globe } from 'lucide-react';
import { SUPPORTED_LANGUAGES } from '../languages';

export function LanguageSwitcher({ value = 'en', onChange, className = '' }) {
  return (
    <div className={`inline-flex items-center gap-1.5 ${className}`}>
      <Globe className="w-3.5 h-3.5 text-slate-500" />
      <div className="inline-flex rounded-md border border-slate-300 bg-white p-0.5 shadow-xs">
        {SUPPORTED_LANGUAGES.map((lang) => {
          const isActive = value === lang.code;
          return (
            <button
              key={lang.code}
              type="button"
              onClick={() => onChange(lang.code)}
              className={`px-1.5 sm:px-2.5 py-0.5 sm:py-1 text-[10px] sm:text-xs font-medium rounded transition-colors cursor-pointer shrink-0 ${
                isActive
                  ? 'bg-slate-900 text-white font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
              title={`Switch language to ${lang.label} (${lang.native})`}
            >
              {lang.native}
            </button>
          );
        })}
      </div>
    </div>
  );
}

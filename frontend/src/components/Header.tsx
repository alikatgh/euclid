import React from 'react';
import type { Theme } from '../hooks/useTheme';

interface HeaderProps {
  applicationName: string;
  title: string;
  subtitle: string;
  withE0: boolean;
  onToggleE0: (withE0: boolean) => void;
  theme: Theme;
  onToggleTheme: () => void;
  fontScale: number;
  onIncreaseFontSize: () => void;
  onDecreaseFontSize: () => void;
  onResetFontSize: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  applicationName,
  title,
  subtitle,
  withE0,
  onToggleE0,
  theme,
  onToggleTheme,
  fontScale,
  onIncreaseFontSize,
  onDecreaseFontSize,
  onResetFontSize,
}) => {
  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3">
      <div>
        <div className="flex flex-wrap items-baseline gap-x-3">
          <h1 className="text-2xl font-serif font-bold tracking-normal text-main">{applicationName}</h1>
          <p className="text-sm font-serif text-muted">{title}</p>
        </div>
        <p className="text-xs font-serif italic text-muted mt-0.5">{subtitle}</p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-dim">Algorithm:</span>
          <div className="flex bg-surface border border-border overflow-hidden" role="group">
            <button
              onClick={() => onToggleE0(false)}
              className={`px-3 py-1 text-xs font-medium transition-colors ${
                !withE0 ? 'bg-border text-main font-semibold' : 'text-muted hover:text-main'
              }`}
            >
              Standard (Without E0)
            </button>
            <button
              onClick={() => onToggleE0(true)}
              className={`px-3 py-1 text-xs font-medium transition-colors ${
                withE0 ? 'bg-border text-main font-semibold' : 'text-muted hover:text-main'
              }`}
            >
              With Step E0 (Optimized)
            </button>
          </div>
        </div>

        {/* Font Size / Readability Controller */}
        <div className="flex items-center gap-1 bg-surface border border-border px-1 py-0.5" title="Text Readability Scaling">
          <button
            onClick={onDecreaseFontSize}
            disabled={fontScale <= 0.85}
            className="px-2 py-0.5 text-xs font-bold text-muted hover:text-main hover:bg-border disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            title="Decrease font size"
            aria-label="Decrease font size"
          >
            A−
          </button>
          <button
            onClick={onResetFontSize}
            className="text-[11px] font-mono text-dim px-1 min-w-[36px] text-center hover:text-main transition-colors select-none"
            title="Click to reset font size to 100%"
          >
            {Math.round(fontScale * 100)}%
          </button>
          <button
            onClick={onIncreaseFontSize}
            disabled={fontScale >= 1.35}
            className="px-2 py-0.5 text-xs font-bold text-muted hover:text-main hover:bg-border disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            title="Increase font size"
            aria-label="Increase font size"
          >
            A+
          </button>
        </div>

        <button
          onClick={onToggleTheme}
          className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium bg-surface border border-border text-main hover:border-muted transition-colors"
          aria-label="Toggle theme"
        >
          <span>{theme === 'light' ? '☾' : '☼'}</span>
          <span>{theme === 'light' ? 'Dark Mode' : 'Light Mode'}</span>
        </button>
      </div>
    </header>
  );
};

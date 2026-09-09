import { useState, useRef, useEffect } from 'react';
import { TICKERS, TICKER_META } from '../lib/constants';

export default function Header({ activeTicker, onSelect, usingCache }) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);

  const filtered = query.trim()
    ? TICKERS.filter(t => t.includes(query.toUpperCase()))
    : TICKERS;

  function pick(ticker) {
    setQuery('');
    setOpen(false);
    onSelect(ticker);
  }

  // close on outside click
  useEffect(() => {
    function handler(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // ⌘K / Ctrl+K shortcut
  useEffect(() => {
    function handler(e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        containerRef.current?.querySelector('select')?.focus();
      }
    }
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, []);

  return (
    <header className="fixed top-0 w-full z-50 bg-surface-container-lowest/95 backdrop-blur-md border-b border-outline-variant/30">
      <div className="h-16 w-full px-gutter-desktop mx-auto flex items-center justify-between gap-space-md">

        {/* Brand */}
        <div className="flex items-center gap-space-md shrink-0">
          <div className="flex items-center gap-space-sm">
            <div className="w-7 h-7 rounded bg-primary/20 border border-primary/30 flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-primary text-[16px]">query_stats</span>
            </div>
            <div className="flex flex-col">
              <span className="font-headline-sm text-headline-sm text-on-surface tracking-tight font-semibold leading-tight">
                Market Sentiment Dashboard
              </span>
              <span className="font-label-mono text-label-mono text-outline">BNP Paribas Hackathon</span>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-space-xs px-space-sm py-space-2xs bg-surface-container rounded border border-outline-variant/40">
            <span className="w-1.5 h-1.5 rounded-full bg-tertiary animate-pulse" />
            <span className="font-label-mono text-label-mono text-tertiary uppercase tracking-wider">Model v2.4-Quant</span>
          </div>
        </div>

        {/* Right controls */}
        <div className="flex items-center gap-space-sm shrink-0" ref={containerRef}>

          {/* Ticker select */}
          <div className="relative flex items-center bg-surface-container-low rounded border border-outline-variant/50 hover:border-outline px-space-sm py-space-2xs transition-colors">
            <span className="material-symbols-outlined text-outline text-[16px] mr-space-xs pointer-events-none">
              candlestick_chart
            </span>
            <select
              className="bg-transparent text-on-surface font-code-sm text-code-sm outline-none cursor-pointer pr-space-md border-none appearance-none focus:ring-0"
              value={activeTicker ?? ''}
              onChange={e => e.target.value && onSelect(e.target.value)}
            >
              <option value="" disabled className="bg-surface-container text-outline">
                Select ticker...
              </option>
              {TICKERS.map(t => (
                <option key={t} value={t} className="bg-surface-container text-on-surface">
                  {t}
                </option>
              ))}
            </select>
            <span className="material-symbols-outlined text-outline text-[16px] pointer-events-none ml-space-2xs">
              unfold_more
            </span>
          </div>

          {/* Cache badge */}
          <div className="flex items-center gap-space-xs px-space-sm py-space-2xs bg-surface-container rounded border border-outline-variant/40">
            <span className={`w-1.5 h-1.5 rounded-full ${usingCache ? 'bg-secondary' : 'bg-tertiary'}`} />
            <span className="font-code-sm text-code-sm text-on-surface-variant hidden sm:inline">
              {usingCache ? 'Using cached data' : 'Live data stream'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}

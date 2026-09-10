/**
 * Top status strip shown on prediction & fallback screens.
 * Matches the "SYSTEM LIVE / ENG / INFERENCE" bar in screen 3.
 */
export default function StatusStrip({ ticker, usingCache, onRefresh, isRefreshing }) {
  return (
    <div className="flex items-center justify-between gap-space-sm bg-surface-container-low px-space-md py-space-xs rounded border border-outline-variant/30 text-on-surface-variant">
      <div className="flex items-center gap-space-sm font-label-mono text-label-mono">
        <span className="inline-flex items-center gap-1.5 px-space-xs py-0.5 rounded bg-tertiary-container/10 border border-tertiary/30 text-tertiary">
          <span className="w-1.5 h-1.5 rounded-full bg-tertiary animate-ping" />
          <span>SYSTEM LIVE</span>
        </span>
        <span className="hidden sm:inline text-outline">•</span>
        <span className="hidden sm:inline">ENG: XGBOOST + FINBERT</span>
        <span className="hidden md:inline text-outline">•</span>
        <span className="hidden md:inline">XAI: TREESHAP</span>
      </div>
      <div className="flex items-center gap-space-sm">
        <div className="inline-flex items-center gap-1.5 px-space-sm py-0.5 rounded bg-surface-container border border-outline-variant/50 font-label-mono text-label-mono text-tertiary">
          <span className="w-1.5 h-1.5 rounded-full bg-tertiary" />
          <span>{usingCache ? '⚠ Using cached data' : '● Live data stream'}</span>
        </div>
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Re-fetch live feeds"
          className="w-7 h-7 flex items-center justify-center rounded bg-surface-container hover:bg-surface-container-high border border-outline-variant/40 hover:border-primary/50 text-on-surface hover:text-primary transition-all active:scale-95"
        >
          <span className={`material-symbols-outlined text-[15px] transition-transform duration-500 ${isRefreshing ? 'animate-spin' : ''}`}>
            refresh
          </span>
        </button>
      </div>
    </div>
  );
}

import { TICKERS } from '../lib/constants';

/**
 * Horizontal scrollable ticker strip — matches the watchlist row in screen 3.
 * Active ticker gets cyan border + glow. Others are plain cards.
 */
export default function WatchlistStrip({ activeTicker, onSelect }) {
  return (
    <div className="bg-surface-container-low rounded p-space-md border border-outline-variant/30 flex flex-col gap-space-xs">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-space-xs">
          <span className="material-symbols-outlined text-outline text-[16px]">view_carousel</span>
          <span className="font-label-caps text-label-caps text-outline uppercase tracking-wider">
            Multi-Asset Watchlist (15 Coverage Nodes)
          </span>
        </div>
        <span className="font-label-mono text-label-mono text-outline hidden sm:inline">
          Click to load
        </span>
      </div>

      <div className="overflow-x-auto pb-space-xs pt-space-xs flex items-center gap-space-xs scrollbar-none">
        {TICKERS.map(ticker => {
          const isActive = ticker === activeTicker;
          return (
            <button
              key={ticker}
              onClick={() => onSelect(ticker)}
              className={`shrink-0 flex items-center gap-2 px-space-sm py-1.5 rounded border cursor-pointer transition-all
                ${isActive
                  ? 'bg-surface-container-highest border-primary text-primary shadow-[0_0_8px_rgba(76,215,246,0.25)]'
                  : 'bg-surface-container hover:bg-surface-container-high border-outline-variant/30 text-on-surface'
                }`}
            >
              {isActive && (
                <span className="material-symbols-outlined text-[14px]">check_circle</span>
              )}
              <span className={`font-code-md text-code-md font-${isActive ? 'bold' : 'semibold'}`}>
                {ticker}
              </span>
              <span className="w-2 h-2 rounded-full bg-[#10b981]" />
            </button>
          );
        })}
      </div>
    </div>
  );
}

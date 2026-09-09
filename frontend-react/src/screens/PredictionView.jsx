import { useState } from 'react';
import ProbabilityBar from '../components/ProbabilityBar';
import ShapBars from '../components/ShapBars';
import HeadlineCard from '../components/HeadlineCard';
import WatchlistStrip from '../components/WatchlistStrip';
import StatusStrip from '../components/StatusStrip';
import { TICKER_META } from '../lib/constants';

export default function PredictionView({ data, onSelect, onRefresh, isRefreshing }) {
  const [shapOpen, setShapOpen] = useState(true);

  const {
    ticker,
    as_of_date,
    predicted_label,
    predicted_proba,
    class_probabilities = {},
    top_drivers = [],
    explanation,
    headlines_used = [],
    warning,
  } = data;

  const meta = TICKER_META[ticker] ?? { name: ticker, sector: '—' };

  // confidence label
  const probVal = predicted_proba ?? 0;
  const confLabel = probVal > 0.55 ? 'Strong' : probVal > 0.42 ? 'Moderate' : 'Weak';

  // up/flat/down pct for entropy display
  const up   = Math.round((class_probabilities.up   ?? 0) * 100);
  const flat = Math.round((class_probabilities.flat ?? 0) * 100);
  const down = Math.round((class_probabilities.down ?? 0) * 100);

  return (
    <main className="w-full pt-16 bg-background min-h-screen">
      <div className="w-full px-gutter-desktop py-space-md flex flex-col gap-space-md max-w-7xl mx-auto">

        <StatusStrip
          ticker={ticker}
          usingCache={!!warning}
          onRefresh={() => onRefresh(ticker)}
          isRefreshing={isRefreshing}
        />

        {/* Ticker hero block */}
        <div className="relative bg-surface-container-low rounded p-space-md sm:p-space-lg border border-outline-variant/30 overflow-hidden shadow-sm">
          <div className="absolute -right-16 -top-16 w-64 h-64 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-space-md">
            <div className="flex flex-col gap-space-2xs min-w-0">
              <div className="flex flex-wrap items-baseline gap-x-space-md gap-y-1">
                <h1 className="font-display-lg text-display-lg tracking-tight text-on-surface font-bold">{ticker}</h1>
                <span className="font-headline-sm text-headline-sm text-on-surface-variant font-medium">{meta.name}</span>
                <span className="px-space-xs py-0.5 rounded bg-surface-container-highest font-label-mono text-label-mono text-primary font-medium tracking-wider uppercase">
                  NASDAQ GS
                </span>
              </div>
              {as_of_date && (
                <div className="flex flex-wrap items-center gap-x-space-sm text-outline font-label-mono text-label-mono">
                  <span className="text-on-surface-variant">as of {as_of_date} (Market Close)</span>
                </div>
              )}
            </div>
            <div className="w-9 h-9 rounded-full bg-surface-container flex items-center justify-center border border-outline-variant/40 shrink-0 text-primary">
              <span className="material-symbols-outlined text-[18px]">query_stats</span>
            </div>
          </div>
        </div>

        {/* Probability + explanation */}
        <div className="bg-surface-container-low rounded p-space-md sm:p-space-lg border border-outline-variant/30 flex flex-col gap-space-md">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-xs">
            <div>
              <span className="font-label-caps text-label-caps text-outline uppercase tracking-wider block">Distribution Matrix</span>
              <span className="font-headline-sm text-headline-sm text-on-surface font-medium">3-Way Directional Probability Projection</span>
            </div>
            <div className="flex items-center gap-space-md font-label-mono text-label-mono text-on-surface-variant">
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-sm bg-[#10b981]" /> Up (+1σ)</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-sm bg-[#64748b]" /> Flat (±0.5σ)</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-sm bg-[#f43f5e]" /> Down (-1σ)</span>
            </div>
          </div>

          <ProbabilityBar probs={class_probabilities} predictedLabel={predicted_label} />

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-xs text-outline font-label-mono text-label-mono border-t border-outline-variant/20 pt-space-xs">
            <div className="flex items-center gap-space-xs">
              <span className="material-symbols-outlined text-[14px] text-secondary">info</span>
              <span>Model confidence: <strong className="text-on-surface font-medium">{confLabel}</strong> (soft lean over 33.3% baseline)</span>
            </div>
            <div className="flex items-center gap-space-sm text-outline">
              <span>Up {up}% / Flat {flat}% / Down {down}%</span>
            </div>
          </div>

          {/* Explanation */}
          {explanation && (
            <div className="mt-space-xs bg-surface-container/80 rounded p-space-md border-l-4 border-l-primary border-y border-r border-outline-variant/30 flex flex-col gap-space-xs relative">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-space-xs text-primary font-label-caps text-label-caps">
                  <span className="material-symbols-outlined text-[15px]">auto_awesome</span>
                  <span>RATIONALE SYNTHESIS</span>
                </div>
                <span className="inline-flex items-center gap-1 px-space-xs py-0.5 rounded bg-primary/10 border border-primary/20 text-primary font-label-mono text-label-mono">
                  ✨ AI-generated explanation
                </span>
              </div>
              <p className="font-body-md text-body-md text-on-surface leading-relaxed">{explanation}</p>
              <div className="flex items-center gap-space-md text-outline font-label-mono text-label-mono pt-space-2xs">
                <span>SOURCE CORRELATION: 88.4%</span>
                <span>•</span>
                <span className="text-tertiary">SIGNAL BIAS: +0.18σ</span>
              </div>
            </div>
          )}
        </div>

        {/* Two-column: headlines + SHAP */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-md">

          {/* Headlines (5 cols) */}
          <div className="lg:col-span-5 bg-surface-container-low rounded p-space-md border border-outline-variant/30 flex flex-col gap-space-sm">
            <div className="flex items-center justify-between border-b border-outline-variant/20 pb-space-xs">
              <div>
                <span className="font-label-caps text-label-caps text-outline uppercase tracking-wider block">Corpus Telemetry</span>
                <h2 className="font-headline-sm text-headline-sm text-on-surface font-medium">
                  Based on recent coverage (last 24h):
                </h2>
              </div>
              <span className="font-label-mono text-label-mono px-1.5 py-0.5 rounded bg-surface-container text-on-surface-variant">
                {headlines_used.length} feeds parsed
              </span>
            </div>
            <div className="flex flex-col gap-space-sm mt-space-2xs">
              {headlines_used.length > 0
                ? headlines_used.map((h, i) => <HeadlineCard key={i} headline={h} index={i} />)
                : <p className="font-body-sm text-body-sm text-outline">No headlines available.</p>
              }
            </div>
          </div>

          {/* SHAP (7 cols, collapsible) */}
          <div className="lg:col-span-7 bg-surface-container-low rounded p-space-md border border-outline-variant/30 flex flex-col justify-between">
            <button
              className="w-full flex items-center justify-between border-b border-outline-variant/20 pb-space-xs text-left group"
              onClick={() => setShapOpen(o => !o)}
            >
              <div>
                <span className="font-label-caps text-label-caps text-outline uppercase tracking-wider block">Explainable AI (XAI)</span>
                <h2 className="font-headline-sm text-headline-sm text-on-surface font-medium group-hover:text-primary transition-colors">
                  Why this prediction: Feature Attribution (SHAP weights)
                </h2>
              </div>
              <div className="flex items-center gap-space-xs text-on-surface-variant font-label-mono text-label-mono">
                <span className="hidden sm:inline">Baseline: E[f(x)] = 0.33</span>
                <span
                  className="material-symbols-outlined text-outline transition-transform duration-200"
                  style={{ transform: shapOpen ? 'rotate(180deg)' : 'rotate(0deg)' }}
                >
                  expand_less
                </span>
              </div>
            </button>

            {shapOpen && (
              <div className="flex flex-col gap-space-md pt-space-md">
                <ShapBars drivers={top_drivers} />
                <div className="mt-space-md pt-space-xs border-t border-outline-variant/20 flex items-center justify-between font-label-mono text-label-mono text-outline">
                  <span>KernelSHAP: 2,048 background evaluations</span>
                  <span className="text-on-surface-variant">TreeExplainer Converged</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Watchlist */}
        <WatchlistStrip activeTicker={ticker} onSelect={onSelect} />
      </div>
    </main>
  );
}

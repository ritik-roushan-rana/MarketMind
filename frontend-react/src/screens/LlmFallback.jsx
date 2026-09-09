import { useState } from 'react';
import ProbabilityBar from '../components/ProbabilityBar';
import ShapBars from '../components/ShapBars';
import HeadlineCard from '../components/HeadlineCard';
import WatchlistStrip from '../components/WatchlistStrip';
import { TICKER_META } from '../lib/constants';

export default function LlmFallback({ data, onSelect, onRefresh, isRefreshing }) {
  const {
    ticker,
    as_of_date,
    predicted_label,
    class_probabilities = {},
    top_drivers = [],
    headlines_used = [],
    warning,
  } = data;

  const meta = TICKER_META[ticker] ?? { name: ticker, sector: '—' };

  return (
    <main className="w-full pt-16 bg-background min-h-screen">

      {/* Status strip */}
      <div className="w-full bg-surface-container-lowest px-gutter-desktop py-space-xs flex flex-wrap items-center justify-between gap-space-sm">
        <div className="flex items-center gap-space-sm">
          <div className="flex items-center gap-space-xs px-space-sm py-space-2xs bg-surface-container rounded">
            <span className="w-2 h-2 rounded-full bg-secondary-container animate-pulse" />
            <span className="font-label-mono text-label-mono text-secondary-container tracking-wider uppercase font-semibold">● Live data (Partial)</span>
          </div>
          <span className="font-label-mono text-label-mono px-space-xs py-space-2xs bg-surface-container-high text-on-surface-variant rounded">NLP_TIMEOUT (408)</span>
        </div>
        <div className="flex items-center gap-space-md font-label-mono text-label-mono text-outline">
          <span className="flex items-center gap-space-2xs">
            <span className="material-symbols-outlined text-[14px] text-tertiary">check_circle</span> FEATURE_VECTORS: SYNCED
          </span>
          <span className="flex items-center gap-space-2xs">
            <span className="material-symbols-outlined text-[14px] text-error">error</span> SYNTHESIS_SERVICE: RETRY_PENDING
          </span>
        </div>
      </div>

      <div className="w-full px-gutter-desktop py-space-base space-y-space-base">

        {/* Ticker header + probability */}
        <section className="bg-surface-container rounded-xl p-space-md shadow-sm relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-primary/5 via-transparent to-transparent pointer-events-none" />
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-space-md pb-space-md">
            <div className="flex items-start sm:items-center gap-space-md">
              <div className="w-12 h-12 rounded bg-surface-container-high flex items-center justify-center shrink-0">
                <span className="font-headline-lg text-headline-lg font-bold text-primary tracking-tight">
                  {ticker.slice(0, 2)}
                </span>
              </div>
              <div className="flex flex-col min-w-0">
                <div className="flex flex-wrap items-center gap-space-sm">
                  <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight font-bold">{ticker}</h1>
                  <span className="font-body-md text-body-md text-on-surface-variant font-medium">{meta.name} • NASDAQ</span>
                </div>
                {as_of_date && (
                  <div className="flex items-center gap-space-xs font-code-sm text-code-sm text-outline mt-space-2xs">
                    <span className="material-symbols-outlined text-[14px]">schedule</span>
                    <span>as of {as_of_date}</span>
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-space-sm shrink-0">
              <button
                onClick={() => onRefresh(ticker)}
                disabled={isRefreshing}
                className="flex items-center gap-space-xs px-space-sm py-space-xs bg-surface-container-high hover:bg-surface-bright text-on-surface rounded font-body-sm text-body-sm transition-colors active:scale-95"
              >
                <span className={`material-symbols-outlined text-[16px] text-primary ${isRefreshing ? 'animate-spin' : ''}`}>refresh</span>
                <span>Refresh Model</span>
              </button>
            </div>
          </div>

          {/* Probability bar */}
          <div className="mt-space-sm bg-surface-container-lowest rounded-lg p-space-md space-y-space-sm">
            <div className="flex flex-wrap items-center justify-between gap-space-xs">
              <div className="flex items-center gap-space-sm">
                <span className="font-label-caps text-label-caps uppercase text-outline tracking-wider">3-Way Distribution Forecast</span>
                <span className="px-space-xs py-space-2xs rounded bg-surface-container-high font-label-mono text-label-mono text-on-surface-variant">Horizon: T+1 Close</span>
              </div>
            </div>
            <ProbabilityBar probs={class_probabilities} predictedLabel={predicted_label} />
            <div className="flex justify-between font-label-mono text-label-mono text-outline px-space-2xs pt-space-2xs">
              <span className="flex items-center gap-space-2xs"><span className="w-1.5 h-1.5 rounded-full bg-tertiary" /> Bullish Bias &gt; +0.75%</span>
              <span className="flex items-center gap-space-2xs"><span className="w-1.5 h-1.5 rounded-full bg-secondary" /> Variance Range [-0.75%, +0.75%]</span>
              <span className="flex items-center gap-space-2xs"><span className="w-1.5 h-1.5 rounded-full bg-error" /> Bearish Bias &lt; -0.75%</span>
            </div>
          </div>
        </section>

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-base items-start">

          {/* Left: fallback callout + SHAP (7 cols) */}
          <div className="lg:col-span-7 space-y-space-base">

            {/* Fallback error block */}
            <div className="bg-surface-container rounded-xl p-space-md shadow-md relative overflow-hidden">
              <div className="flex items-start gap-space-md">
                <div className="w-9 h-9 rounded bg-surface-container-high text-secondary flex items-center justify-center shrink-0 mt-0.5">
                  <span className="material-symbols-outlined text-[20px]">warning</span>
                </div>
                <div className="flex-1 space-y-space-xs">
                  <div className="flex flex-wrap items-center justify-between gap-space-xs">
                    <h3 className="font-headline-sm text-headline-sm font-semibold text-on-surface tracking-tight">
                      Explanation temporarily unavailable — showing model output only.
                    </h3>
                    <span className="font-label-mono text-label-mono px-space-xs py-space-2xs rounded bg-surface-container-lowest text-outline">
                      NLP_TIMEOUT
                    </span>
                  </div>
                  <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                    The quantitative direction model calculated the distribution normally, but the plain-English NLP
                    synthesis service timed out. You can still inspect the SHAP feature weights below or retry.
                  </p>
                  <div className="pt-space-xs flex flex-wrap items-center gap-space-sm">
                    <button
                      onClick={() => onRefresh(ticker)}
                      className="flex items-center gap-space-xs px-space-md py-space-xs bg-primary-container hover:bg-primary text-on-primary-container font-headline-sm text-[13px] font-semibold rounded shadow-sm transition-all active:scale-95"
                    >
                      <span className="material-symbols-outlined text-[16px]">sync</span>
                      <span>Retry Explanation</span>
                    </button>
                    <span className="font-label-mono text-label-mono text-outline">Attempt 1 of 3</span>
                  </div>
                </div>
              </div>
              {/* Telemetry trace */}
              <div className="mt-space-md p-space-sm bg-surface-container-lowest rounded flex flex-col gap-space-2xs">
                <div className="flex items-center justify-between font-label-mono text-label-mono text-outline">
                  <span>PIPELINE TELEMETRY:</span>
                  <span className="text-secondary">NLP_WORKER_TIMEOUT_EXCEEDED (15000ms)</span>
                </div>
                <div className="font-code-sm text-code-sm text-on-surface-variant/80 truncate">
                  Worker: <span className="text-on-surface">pod-nlp-gen-09b</span> • Status: <span className="text-error">ABORTED</span>
                </div>
              </div>
            </div>

            {/* SHAP */}
            <div className="bg-surface-container rounded-xl p-space-md shadow-sm space-y-space-md">
              <div className="flex items-center justify-between pb-space-xs">
                <div className="flex items-center gap-space-sm">
                  <span className="material-symbols-outlined text-primary text-[20px]">equalizer</span>
                  <h2 className="font-headline-sm text-headline-sm text-on-surface font-semibold tracking-tight">
                    Why this prediction (SHAP Feature Weights)
                  </h2>
                </div>
                <span className="font-label-mono text-label-mono text-outline">BASELINE E(y) = 0.33</span>
              </div>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Quantitative feature attribution decomposed across global technicals and order books.
              </p>
              <ShapBars drivers={top_drivers} />
            </div>
          </div>

          {/* Right: headlines (5 cols) */}
          <div className="lg:col-span-5 bg-surface-container-low rounded p-space-md border border-outline-variant/30 flex flex-col gap-space-sm">
            <div className="flex items-center justify-between border-b border-outline-variant/20 pb-space-xs">
              <div>
                <span className="font-label-caps text-label-caps text-outline uppercase tracking-wider block">Corpus Telemetry</span>
                <h2 className="font-headline-sm text-headline-sm text-on-surface font-medium">Based on recent coverage:</h2>
              </div>
              <span className="font-label-mono text-label-mono px-1.5 py-0.5 rounded bg-surface-container text-on-surface-variant">
                {headlines_used.length} feeds
              </span>
            </div>
            <div className="flex flex-col gap-space-sm mt-space-2xs">
              {headlines_used.length > 0
                ? headlines_used.map((h, i) => <HeadlineCard key={i} headline={h} index={i} />)
                : <p className="font-body-sm text-body-sm text-outline">No headlines available.</p>
              }
            </div>
          </div>
        </div>

        {/* Watchlist */}
        <WatchlistStrip activeTicker={ticker} onSelect={onSelect} />
      </div>
    </main>
  );
}

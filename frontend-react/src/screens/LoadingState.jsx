import { useEffect, useState } from 'react';
import { TICKERS, LOADING_STAGES } from '../lib/constants';

function SkeletonBlock({ className = '' }) {
  return (
    <div className={`bg-surface-container-highest rounded animate-pulse relative overflow-hidden ${className}`}>
      <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-surface-bright/20 to-transparent pointer-events-none" />
    </div>
  );
}

export default function LoadingState({ ticker }) {
  const [stageIdx, setStageIdx] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setStageIdx(i => (i + 1) % LOADING_STAGES.length), 1800);
    return () => clearInterval(id);
  }, []);

  return (
    <main className="w-full pt-16 bg-background min-h-screen">

      {/* Loading status bar */}
      <div className="w-full bg-surface-container-lowest px-gutter-desktop py-space-sm shadow-sm">
        <div className="max-w-[1720px] mx-auto flex flex-wrap items-center justify-between gap-space-sm">
          <div className="flex items-center gap-space-md min-w-0">
            <div className="flex items-center gap-space-xs bg-surface-container-high px-space-sm py-space-2xs rounded-lg shadow-sm">
              <span className="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider">Target</span>
              <div className="flex items-center gap-space-xs">
                <span className="font-code-lg text-code-lg text-primary font-semibold tracking-tight">{ticker}</span>
                <span className="inline-block w-2 h-2 rounded-full bg-primary animate-ping" />
              </div>
            </div>
            <div className="flex items-center gap-space-sm bg-surface-container px-space-md py-space-2xs rounded-lg shadow-sm">
              <span className="material-symbols-outlined text-primary text-[18px] animate-spin">progress_activity</span>
              <span className="font-code-sm text-code-sm text-on-surface font-medium truncate">
                {LOADING_STAGES[stageIdx]}
              </span>
              <span className="hidden sm:inline-block font-label-mono text-label-mono text-primary px-space-xs py-space-2xs bg-surface-container-high rounded text-[10px]">
                EST. 4–10s
              </span>
            </div>
          </div>
          <div className="flex items-center gap-space-xs px-space-sm py-space-2xs bg-surface-container-high rounded-lg shadow-sm">
            <span className="w-2 h-2 rounded-full bg-tertiary animate-pulse" />
            <span className="font-label-mono text-label-mono text-on-surface-variant">Connecting to inference node...</span>
          </div>
        </div>
      </div>

      <div className="w-full px-gutter-desktop py-space-lg max-w-[1720px] mx-auto flex flex-col gap-space-lg">
        <div className="w-full grid grid-cols-1 xl:grid-cols-12 gap-space-base items-start">

          {/* Left skeletons (8 cols) */}
          <div className="xl:col-span-8 flex flex-col gap-space-base">
            {/* Header card */}
            <div className="relative overflow-hidden bg-surface-container p-space-lg rounded-xl shadow-md">
              <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-surface-bright/20 to-transparent pointer-events-none" />
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-md pb-space-md">
                <div className="flex items-center gap-space-md">
                  <SkeletonBlock className="h-10 w-28" />
                  <SkeletonBlock className="h-6 w-44" />
                  <SkeletonBlock className="h-6 w-20 hidden md:block" />
                </div>
                <div className="flex items-center gap-space-sm">
                  <SkeletonBlock className="h-8 w-24" />
                  <SkeletonBlock className="h-8 w-8 rounded-full" />
                </div>
              </div>
              {/* Probability bar skeleton */}
              <div className="pt-space-md flex flex-col gap-space-sm">
                <div className="flex items-center justify-between">
                  <SkeletonBlock className="h-4 w-36" />
                  <SkeletonBlock className="h-3 w-16 hidden sm:block" />
                </div>
                <div className="w-full h-8 bg-surface-container-lowest rounded-lg p-1 flex gap-1 items-center">
                  <SkeletonBlock className="h-full w-7/12 rounded-l" />
                  <SkeletonBlock className="h-full w-3/12" />
                  <SkeletonBlock className="h-full w-2/12 rounded-r" />
                </div>
                <SkeletonBlock className="h-4 w-28" />
              </div>
            </div>

            {/* Explanation card */}
            <div className="relative overflow-hidden bg-surface-container p-space-lg rounded-xl shadow-md flex flex-col gap-space-md">
              <div className="absolute inset-0 -translate-x-full animate-shimmer-slow bg-gradient-to-r from-transparent via-surface-bright/20 to-transparent pointer-events-none" />
              <div className="flex items-center justify-between pb-space-2xs">
                <div className="flex items-center gap-space-sm">
                  <div className="w-2.5 h-6 bg-primary-container rounded-sm animate-pulse" />
                  <SkeletonBlock className="h-6 w-52" />
                </div>
                <div className="flex items-center gap-space-xs bg-surface-container-high px-space-sm py-space-2xs rounded-full">
                  <span className="material-symbols-outlined text-primary text-[14px] animate-spin">smart_toy</span>
                  <SkeletonBlock className="h-3.5 w-36" />
                </div>
              </div>
              <div className="bg-surface-container-low p-space-md rounded-lg flex flex-col gap-space-sm shadow-inner">
                <SkeletonBlock className="h-4 w-11/12" />
                <SkeletonBlock className="h-4 w-full" />
                <SkeletonBlock className="h-4 w-4/5" />
                <SkeletonBlock className="h-4 w-9/12" />
              </div>
            </div>

            {/* SHAP collapsed skeleton */}
            <div className="relative overflow-hidden bg-surface-container p-space-md rounded-xl shadow-md">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-space-sm">
                  <SkeletonBlock className="w-5 h-5 rounded-full" />
                  <SkeletonBlock className="h-5 w-48" />
                </div>
                <span className="material-symbols-outlined text-outline-variant text-[20px]">expand_more</span>
              </div>
            </div>
          </div>

          {/* Right skeletons (4 cols) */}
          <div className="xl:col-span-4 flex flex-col gap-space-base">
            <div className="relative overflow-hidden bg-surface-container p-space-lg rounded-xl shadow-md flex flex-col gap-space-md">
              <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-surface-bright/20 to-transparent pointer-events-none" />
              <div className="flex items-center justify-between">
                <SkeletonBlock className="h-5 w-36" />
                <SkeletonBlock className="h-4 w-20" />
              </div>
              {[0, 1, 2].map(i => (
                <div key={i} className="bg-surface-container-low p-space-md rounded-lg flex flex-col gap-space-xs shadow-sm">
                  <div className="flex items-center justify-between gap-space-xs">
                    <SkeletonBlock className="h-4 w-20" />
                    <SkeletonBlock className="h-3 w-16" />
                  </div>
                  <SkeletonBlock className="h-4 w-full mt-1" />
                  <SkeletonBlock className="h-4 w-5/6" />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Watchlist skeleton */}
        <div className="w-full flex flex-col gap-space-sm">
          <div className="flex items-center justify-between px-space-xs">
            <div className="flex items-center gap-space-sm">
              <span className="font-label-caps text-label-caps text-on-surface uppercase tracking-wider">Watchlist Peer Matrix</span>
              <span className="font-code-sm text-code-sm text-outline px-space-xs py-space-2xs bg-surface-container-high rounded">
                15 Tickers Monitored
              </span>
            </div>
            <div className="flex items-center gap-space-xs text-outline">
              <span className="material-symbols-outlined text-[14px]">sync</span>
              <span className="font-label-mono text-label-mono">STREAMING WEIGHTS</span>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-8 xl:grid-cols-15 gap-space-xs">
            {TICKERS.map(t => (
              <div key={t} className="bg-surface-container p-space-sm rounded-lg flex flex-col gap-space-xs shadow-sm relative overflow-hidden">
                <div className="flex items-center justify-between">
                  <span className={`font-code-sm text-code-sm font-semibold ${t === ticker ? 'text-primary' : 'text-on-surface'}`}>{t}</span>
                  <div className={`w-2 h-2 rounded-full ${t === ticker ? 'bg-primary animate-ping' : 'bg-surface-container-highest animate-pulse'}`} />
                </div>
                <SkeletonBlock className="h-4 w-12" />
                <div className="h-2 w-full bg-surface-container-lowest rounded overflow-hidden">
                  <div className={`h-full ${t === ticker ? 'bg-primary/40 w-11/12' : 'bg-surface-container-high w-2/3'} animate-pulse`} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}

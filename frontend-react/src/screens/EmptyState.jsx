import { TICKERS, TICKER_META } from '../lib/constants';

export default function EmptyState({ onSelect }) {
  return (
    <main className="w-full pt-16 bg-background min-h-screen">
      <div className="flex flex-col w-full px-gutter-desktop max-w-[1440px] mx-auto pb-space-2xl relative">

        {/* Guidance callout */}
        <div className="w-full flex justify-end pt-space-md pr-space-lg mb-space-md">
          <div className="flex items-center gap-space-sm bg-surface-container-high/80 backdrop-blur px-space-md py-space-xs rounded-xl shadow-lg animate-bounce">
            <span className="material-symbols-outlined text-primary text-[18px]">arrow_upward</span>
            <span className="font-code-sm text-code-sm text-primary font-medium tracking-wide">
              Select a stock to see today's prediction
            </span>
          </div>
        </div>

        {/* Ambient glow */}
        <div className="absolute top-12 left-1/2 -translate-x-1/2 w-3/4 max-w-4xl h-72 bg-gradient-to-b from-primary/10 via-secondary-container/5 to-transparent blur-3xl pointer-events-none -z-10" />

        {/* Hero + methodology grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-lg items-stretch mt-space-sm">

          {/* Left: status console (7 cols) */}
          <div className="lg:col-span-7 flex flex-col justify-between bg-surface-container-low rounded-xl p-space-xl shadow-xl relative overflow-hidden">
            <div className="absolute -right-16 -top-16 w-64 h-64 bg-primary/5 rounded-full blur-2xl pointer-events-none" />
            <div className="space-y-space-md relative z-10">
              <div className="flex flex-wrap items-center gap-space-sm">
                <div className="inline-flex items-center gap-space-xs bg-surface-container px-space-sm py-space-2xs rounded-full">
                  <span className="w-2 h-2 rounded-full bg-tertiary animate-ping" />
                  <span className="font-label-mono text-label-mono text-tertiary uppercase">Inference Engine Idling</span>
                </div>
                <span className="font-label-mono text-label-mono text-outline">LATENCY: ~12ms</span>
                <span className="font-label-mono text-label-mono text-outline">•</span>
                <span className="font-label-mono text-label-mono text-outline">WEIGHTS: v2.4-STABLE</span>
              </div>
              <div className="space-y-space-xs">
                <h2 className="font-display-lg text-display-lg text-on-surface tracking-tight">
                  Ready for Inference
                </h2>
                <p className="font-body-lg text-body-lg text-on-surface-variant max-w-xl">
                  Select an institutional asset to aggregate multi-source sentiment, real-time technicals, and generative directional attribution.
                </p>
              </div>

              {/* Pipeline spec */}
              <div className="p-space-md bg-surface-container rounded-lg space-y-space-sm mt-space-md">
                <div className="flex items-center justify-between">
                  <span className="font-label-caps text-label-caps text-outline uppercase tracking-wider">Quant Telemetry Pipeline</span>
                  <span className="font-code-sm text-code-sm text-primary">15 / 15 Streams Armed</span>
                </div>
                <div className="grid grid-cols-3 gap-space-sm pt-space-xs">
                  {[
                    { label: 'FEED 01', name: 'Sec-EDGAR 8-K',    sub: 'Real-time Stream', subColor: 'text-tertiary' },
                    { label: 'FEED 02', name: 'Institutional NLP', sub: 'BERT-Finance v3',  subColor: 'text-tertiary' },
                    { label: 'FEED 03', name: 'L2 Order Flow',     sub: 'Tick Variance 0.04%', subColor: 'text-secondary' },
                  ].map(f => (
                    <div key={f.label} className="flex flex-col gap-space-2xs bg-surface-container-high/60 p-space-sm rounded">
                      <span className="font-label-mono text-label-mono text-outline">{f.label}</span>
                      <span className="font-code-md text-code-md text-on-surface font-medium">{f.name}</span>
                      <span className={`font-label-mono text-label-mono ${f.subColor}`}>{f.sub}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-space-lg flex flex-wrap items-center justify-between gap-space-md relative z-10">
              <div className="flex items-center gap-space-xs text-on-surface-variant font-code-sm text-code-sm">
                <span className="material-symbols-outlined text-primary text-[18px]">touch_app</span>
                <span>Click any universe ticker below to instantly run pipeline</span>
              </div>
              <div className="flex items-center gap-space-xs">
                <span className="font-label-mono text-label-mono text-outline">BATCH ID:</span>
                <span className="font-label-mono text-label-mono text-on-surface bg-surface-container px-space-xs py-space-2xs rounded">
                  BNP-QNT-092284
                </span>
              </div>
            </div>
          </div>

          {/* Right: methodology (5 cols) */}
          <div className="lg:col-span-5 flex flex-col justify-between bg-surface-container rounded-xl p-space-lg shadow-xl relative">
            <div className="space-y-space-md">
              <div className="flex items-center justify-between pb-space-sm">
                <div className="flex items-center gap-space-xs">
                  <span className="material-symbols-outlined text-primary text-[20px]">hub</span>
                  <span className="font-label-caps text-label-caps text-on-surface uppercase tracking-wider">Model Architecture</span>
                </div>
                <span className="bg-primary/10 text-primary font-label-mono text-label-mono px-space-sm py-space-2xs rounded-full">
                  TRANSFORMER-XL
                </span>
              </div>
              <h3 className="font-headline-md text-headline-md text-on-surface font-semibold">How it works</h3>
              <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                Combining next-day price technicals with real-time NLP sentiment analysis to calculate directional lean
                probabilities with AI plain-English attribution.
              </p>
              <div className="space-y-space-xs bg-surface-container-lowest p-space-md rounded-lg">
                {[
                  { label: 'Technical Vector',   pct: 40, color: 'bg-tertiary',   textColor: 'text-tertiary' },
                  { label: 'NLP Sentiment Mass', pct: 45, color: 'bg-primary',    textColor: 'text-primary' },
                  { label: 'Macro Factor Offset',pct: 15, color: 'bg-secondary',  textColor: 'text-secondary' },
                ].map(item => (
                  <div key={item.label}>
                    <div className="flex justify-between items-center text-on-surface">
                      <span className="font-code-sm text-code-sm">{item.label}</span>
                      <span className={`font-code-sm text-code-sm ${item.textColor}`}>{item.pct}% Weight</span>
                    </div>
                    <div className="w-full bg-surface-container-high h-1.5 rounded-full overflow-hidden mt-1">
                      <div className={`${item.color} h-full rounded-full`} style={{ width: `${item.pct}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="mt-space-md pt-space-md flex items-center justify-between text-outline font-label-mono text-label-mono">
              <span>DAILY INFERENCE RUNS: 48,200</span>
              <span className="text-tertiary">RMSE: 0.0142</span>
            </div>
          </div>
        </div>

        {/* Ticker grid */}
        <div className="mt-space-xl space-y-space-md">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-xs">
            <div>
              <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold">Universe Fast Select</h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                15 supported equities across Mega-Cap Tech, Financials, Energy, and Consumer Staples.
              </p>
            </div>
            <div className="flex items-center gap-space-xs">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              <span className="font-label-mono text-label-mono text-on-surface-variant uppercase">Click to trigger execution</span>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-space-sm">
            {TICKERS.map(ticker => {
              const meta = TICKER_META[ticker];
              return (
                <button
                  key={ticker}
                  onClick={() => onSelect(ticker)}
                  className="group text-left p-space-md bg-surface-container hover:bg-surface-container-high transition-all duration-150 rounded-xl shadow hover:shadow-cyan-500/10 cursor-pointer flex flex-col justify-between h-28"
                >
                  <div className="flex items-start justify-between w-full">
                    <div>
                      <span className="font-code-lg text-code-lg text-primary font-bold group-hover:text-primary-fixed transition-colors block">
                        {ticker}
                      </span>
                      <span className="block font-body-sm text-body-sm text-on-surface-variant truncate max-w-[90px]">
                        {meta.name}
                      </span>
                    </div>
                    <span className="w-2 h-2 rounded-full bg-tertiary mt-1" />
                  </div>
                  <div className="flex items-center justify-between w-full font-label-mono text-label-mono text-outline">
                    <span>{meta.sector}</span>
                    <span className="text-tertiary group-hover:translate-x-0.5 transition-transform">→</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </main>
  );
}

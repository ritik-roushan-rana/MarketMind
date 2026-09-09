import { useState } from 'react';
import { TICKERS } from '../lib/constants';

/* ─────────────────────────────────────────────────────────────────
   ErrorTicker  — 400 / unsupported asset
───────────────────────────────────────────────────────────────── */
export function ErrorTicker({ ticker, onSelect }) {
  return (
    <main className="w-full pt-16 bg-background min-h-screen">
      <div className="w-full px-gutter-desktop mx-auto max-w-[1600px] py-space-md flex flex-col gap-space-md">

        {/* Diagnostic bar */}
        <div className="w-full bg-surface-container-low rounded p-space-sm flex flex-wrap items-center justify-between gap-space-sm">
          <div className="flex items-center gap-space-md">
            <div className="flex items-center gap-space-xs">
              <span className="w-2 h-2 rounded-full bg-error animate-ping" />
              <span className="w-2 h-2 rounded-full bg-error -ml-3" />
              <span className="font-label-caps text-label-caps text-error tracking-wider uppercase">Pipeline Exception Intercepted</span>
            </div>
            <span className="text-outline-variant font-label-mono text-label-mono">|</span>
            <div className="flex items-center gap-space-xs">
              <span className="font-label-mono text-label-mono text-outline">TRACE ID:</span>
              <span className="font-code-sm text-code-sm text-on-surface-variant">0x7F9A_ERR_SEC_INGEST</span>
            </div>
          </div>
          <span className="font-label-mono text-label-mono px-space-xs py-space-2xs rounded bg-error-container text-on-error-container">
            1. Invalid Ticker (400/Bad Request)
          </span>
        </div>

        {/* Error card */}
        <div className="w-full min-h-[480px] flex flex-col justify-center items-center relative rounded overflow-hidden bg-surface-container-low">
          {/* Radar backdrop */}
          <div className="absolute inset-0 pointer-events-none opacity-20 flex items-center justify-center overflow-hidden">
            <svg className="w-[600px] h-[600px] text-outline-variant" fill="none" viewBox="0 0 800 800">
              <circle cx="400" cy="400" r="100" stroke="currentColor" strokeDasharray="3 3" />
              <circle cx="400" cy="400" r="220" stroke="currentColor" strokeDasharray="4 4" />
              <circle cx="400" cy="400" r="340" stroke="currentColor" strokeDasharray="6 6" />
              <line stroke="currentColor" strokeDasharray="2 4" x1="0" x2="800" y1="400" y2="400" />
              <line stroke="currentColor" strokeDasharray="2 4" x1="400" x2="400" y1="0" y2="800" />
            </svg>
          </div>

          <div className="w-full max-w-4xl px-space-lg py-space-xl z-10 flex flex-col items-center text-center">
            <div className="inline-flex items-center gap-space-xs px-space-md py-space-xs rounded bg-surface-container-highest/60 text-outline mb-space-lg">
              <span className="material-symbols-outlined text-error text-[18px]">emergency</span>
              <span className="font-code-md text-code-md text-on-surface font-medium">
                QUERY TOKEN: <span className="text-error underline decoration-dotted underline-offset-4">{ticker ?? '???'}</span>
              </span>
              <span className="font-label-mono text-label-mono bg-error-container text-on-error-container px-space-xs py-space-2xs rounded ml-space-xs">
                UNSUPPORTED_ASSET
              </span>
            </div>

            <div className="w-16 h-16 rounded-full bg-surface-container-high flex items-center justify-center mb-space-base shadow-lg">
              <span className="material-symbols-outlined text-primary text-[32px]">warning</span>
            </div>

            <h1 className="font-display-lg text-display-lg text-on-surface mb-space-xs tracking-tight">
              This ticker isn't supported. Try one from the list.
            </h1>
            <p className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl mx-auto mb-space-xl">
              The BNP Paribas hackathon sentiment model currently covers 15 designated high-liquidity large caps with
              curated historical 10-K, 10-Q, and live algorithmic news stream feeds.
            </p>

            {/* Recovery grid */}
            <div className="w-full bg-surface-container p-space-lg rounded shadow-xl max-w-3xl flex flex-col items-center">
              <div className="flex items-center justify-between w-full mb-space-md pb-space-xs bg-surface-container-high/40 px-space-md py-space-2xs rounded">
                <span className="font-label-caps text-label-caps text-secondary uppercase tracking-widest flex items-center gap-space-2xs">
                  <span className="material-symbols-outlined text-[14px]">bolt</span> Select Verified Benchmark Symbol
                </span>
                <span className="font-label-mono text-label-mono text-outline">15 / 15 AVAILABLE</span>
              </div>
              <div className="flex flex-wrap justify-center gap-space-xs w-full">
                {TICKERS.map(t => (
                  <button
                    key={t}
                    onClick={() => onSelect(t)}
                    className="group px-space-md py-space-xs bg-surface-container-high hover:bg-primary hover:text-on-primary rounded text-on-surface font-code-md text-code-md transition-all flex items-center gap-space-2xs active:scale-95 shadow-sm"
                  >
                    <span className="font-semibold">{t}</span>
                  </button>
                ))}
              </div>
              <p className="mt-space-md font-body-sm text-body-sm text-outline text-center">
                Clicking any ticker updates the live execution pipeline immediately.
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

/* ─────────────────────────────────────────────────────────────────
   ErrorServer  — 5xx / network / timeout
───────────────────────────────────────────────────────────────── */
export function ErrorServer({ ticker, status, detail, onRetry, onSelect }) {
  const [retrying, setRetrying] = useState(false);

  async function handleRetry() {
    setRetrying(true);
    await onRetry(ticker);
    setRetrying(false);
  }

  return (
    <main className="w-full pt-16 bg-background min-h-screen">
      <div className="w-full px-gutter-desktop mx-auto max-w-[1600px] py-space-md flex flex-col gap-space-md">

        {/* Diagnostic bar */}
        <div className="w-full bg-surface-container-low rounded p-space-sm flex flex-wrap items-center justify-between gap-space-sm">
          <div className="flex items-center gap-space-md">
            <div className="flex items-center gap-space-xs">
              <span className="w-2 h-2 rounded-full bg-error animate-ping" />
              <span className="w-2 h-2 rounded-full bg-error -ml-3" />
              <span className="font-label-caps text-label-caps text-error tracking-wider uppercase">Pipeline Exception Intercepted</span>
            </div>
            <span className="text-outline-variant font-label-mono text-label-mono">|</span>
            <span className="font-code-sm text-code-sm text-on-surface-variant font-label-mono">
              TRACE ID: 0x7F9A_ERR_INFERENCE
            </span>
          </div>
          <span className="font-label-mono text-label-mono px-space-xs py-space-2xs rounded bg-error-container text-on-error-container">
            2. Inference Timeout ({status ?? 'ERR'})
          </span>
        </div>

        {/* Error card */}
        <div className="w-full min-h-[480px] flex flex-col justify-center items-center relative rounded overflow-hidden bg-surface-container-low">
          <div className="absolute inset-0 pointer-events-none opacity-20 flex items-center justify-center overflow-hidden">
            <svg className="w-[600px] h-[600px] text-outline-variant" fill="none" viewBox="0 0 800 800">
              <circle cx="400" cy="400" r="100" stroke="currentColor" strokeDasharray="3 3" />
              <circle cx="400" cy="400" r="220" stroke="currentColor" strokeDasharray="4 4" />
              <circle cx="400" cy="400" r="340" stroke="currentColor" strokeDasharray="6 6" />
              <line stroke="currentColor" strokeDasharray="2 4" x1="0" x2="800" y1="400" y2="400" />
              <line stroke="currentColor" strokeDasharray="2 4" x1="400" x2="400" y1="0" y2="800" />
            </svg>
          </div>

          <div className="w-full max-w-4xl px-space-lg py-space-xl z-10 flex flex-col items-center text-center">
            <div className="inline-flex items-center gap-space-xs px-space-md py-space-xs rounded bg-error-container text-on-error-container mb-space-lg shadow-md">
              <span className="material-symbols-outlined text-[18px]">cloud_off</span>
              <span className="font-label-caps text-label-caps uppercase tracking-wider">CRITICAL BACKEND FAULT</span>
              <span className="font-label-mono text-label-mono bg-on-error-container/20 px-space-xs py-space-2xs rounded ml-space-xs">
                HTTP {status ?? 'ERR'}
              </span>
            </div>

            <div className="w-16 h-16 rounded-full bg-surface-container-high flex items-center justify-center mb-space-base shadow-[0_0_24px_rgba(255,180,171,0.2)]">
              <span className="material-symbols-outlined text-error text-[32px]">report_problem</span>
            </div>

            <h2 className="font-display-lg text-display-lg text-on-surface mb-space-xs tracking-tight">
              Something went wrong generating this prediction.
            </h2>
            <p className="font-body-lg text-body-lg text-on-surface-variant max-w-xl mx-auto mb-space-lg">
              {detail ?? 'The inference endpoint returned an unexpected error. Please try again.'}
            </p>

            {/* Stack trace card */}
            <div className="w-full max-w-2xl bg-surface-container-lowest p-space-md rounded text-left mb-space-xl font-code-sm text-code-sm shadow-inner">
              <div className="flex items-center justify-between border-b pb-space-2xs mb-space-xs border-outline-variant/30 text-outline">
                <span className="font-label-mono text-label-mono uppercase tracking-wider">Stack Trace Digest</span>
                <span className="font-label-mono text-label-mono text-error">STATUS: UNREACHABLE</span>
              </div>
              <div className="text-error font-medium mb-space-2xs flex items-center gap-space-xs">
                <span className="material-symbols-outlined text-[16px]">terminal</span>
                <span>ERR_INFERENCE ({status}) on ticker {ticker}</span>
              </div>
              <div className="text-outline-variant text-[11px] font-mono leading-relaxed space-y-0.5">
                <div>&gt; [QuantEngine.Runner] Dispatched batch job: SENTIMENT-EMBED</div>
                <div>&gt; [Gateway-Proxy] {detail ?? 'Read timed out after 30000ms threshold'}</div>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-space-md">
              <button
                onClick={handleRetry}
                disabled={retrying}
                className="h-10 px-space-lg bg-primary hover:bg-primary-fixed text-on-primary font-headline-sm text-headline-sm rounded font-semibold transition-all flex items-center gap-space-xs shadow-[0_0_16px_rgba(76,215,246,0.3)] active:scale-95"
              >
                <span className={`material-symbols-outlined text-[20px] ${retrying ? 'animate-spin' : ''}`}>refresh</span>
                <span>{retrying ? 'Retrying...' : 'Retry Request'}</span>
              </button>
              <button
                onClick={() => onSelect(null)}
                className="h-10 px-space-md bg-surface-container-high hover:bg-surface-bright text-on-surface font-headline-sm text-headline-sm rounded transition-all flex items-center gap-space-xs"
              >
                <span className="material-symbols-outlined text-[18px] text-outline">arrow_back</span>
                <span>Back to Universe</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

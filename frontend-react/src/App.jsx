import { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import EmptyState from './screens/EmptyState';
import LoadingState from './screens/LoadingState';
import PredictionView from './screens/PredictionView';
import LlmFallback from './screens/LlmFallback';
import { ErrorTicker, ErrorServer } from './screens/ErrorStates';
import { fetchPrediction, fetchTickers } from './lib/api';

/*
  App state machine
  ──────────────────
  screen: 'empty' | 'loading' | 'prediction' | 'llm-fallback' | 'error-ticker' | 'error-server'
*/

export default function App() {
  const [screen, setScreen]         = useState('empty');
  const [activeTicker, setActiveTicker] = useState(null);
  const [predData, setPredData]     = useState(null);
  const [errorMeta, setErrorMeta]   = useState({ status: null, detail: null });
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [usingCache, setUsingCache] = useState(false);

  // Pre-warm: fetch tickers list on mount (silent, just to verify backend is up)
  useEffect(() => {
    fetchTickers(); // fire-and-forget
  }, []);

  const runPrediction = useCallback(async (ticker) => {
    if (!ticker) { setScreen('empty'); setActiveTicker(null); return; }

    const t = ticker.toUpperCase().trim();
    setActiveTicker(t);
    setScreen('loading');
    setPredData(null);

    const { ok, status, data, errorDetail } = await fetchPrediction(t);

    if (ok) {
      setPredData(data);
      setUsingCache(!!data.warning);
      // screen 4 = LLM fallback when explanation is missing/empty
      const hasExplanation = data.explanation && data.explanation.trim().length > 10;
      setScreen(hasExplanation ? 'prediction' : 'llm-fallback');
    } else if (status === 400) {
      setErrorMeta({ status: 400, detail: errorDetail });
      setScreen('error-ticker');
    } else {
      setErrorMeta({ status, detail: errorDetail });
      setScreen('error-server');
    }
  }, []);

  const handleRefresh = useCallback(async (ticker) => {
    setIsRefreshing(true);
    await runPrediction(ticker);
    setIsRefreshing(false);
  }, [runPrediction]);

  return (
    <div className="dark min-h-screen flex flex-col bg-background text-on-surface antialiased">
      <Header
        activeTicker={activeTicker}
        onSelect={runPrediction}
        usingCache={usingCache}
      />

      <div className="flex-1">
        {screen === 'empty' && (
          <EmptyState onSelect={runPrediction} />
        )}

        {screen === 'loading' && (
          <LoadingState ticker={activeTicker} />
        )}

        {screen === 'prediction' && predData && (
          <PredictionView
            data={predData}
            onSelect={runPrediction}
            onRefresh={handleRefresh}
            isRefreshing={isRefreshing}
          />
        )}

        {screen === 'llm-fallback' && predData && (
          <LlmFallback
            data={predData}
            onSelect={runPrediction}
            onRefresh={handleRefresh}
            isRefreshing={isRefreshing}
          />
        )}

        {screen === 'error-ticker' && (
          <ErrorTicker
            ticker={activeTicker}
            onSelect={runPrediction}
          />
        )}

        {screen === 'error-server' && (
          <ErrorServer
            ticker={activeTicker}
            status={errorMeta.status}
            detail={errorMeta.detail}
            onRetry={runPrediction}
            onSelect={runPrediction}
          />
        )}
      </div>

      <Footer />
    </div>
  );
}

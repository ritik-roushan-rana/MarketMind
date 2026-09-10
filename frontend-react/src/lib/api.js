// VITE_API_BASE is set as an environment variable in Vercel's dashboard.
// Locally it falls back to localhost:8000 so nothing breaks during dev.
// Trailing slashes are stripped: a VITE_API_BASE ending in '/' would build
// URLs like https://host//tickers, and FastAPI 404s on the double slash.
const API_BASE = (import.meta.env.VITE_API_BASE ?? 'http://localhost:8000')
  .replace(/\/+$/, '');

// Vite inlines env vars at BUILD time, so a production bundle missing
// VITE_API_BASE ships the localhost fallback and every visitor's browser
// tries to reach a backend on their own machine. Fail loudly in the console
// instead of leaving that to be diagnosed from a generic "cannot reach API".
if (import.meta.env.PROD && !import.meta.env.VITE_API_BASE) {
  console.error(
    '[config] VITE_API_BASE is not set — this build will call ' +
    `${API_BASE}, which is not reachable from a visitor's browser. ` +
    'Set it in the Vercel dashboard and REDEPLOY (a rebuild is required).'
  );
}

async function request(path, timeoutMs = 60_000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE}${path}`, { signal: controller.signal });
    clearTimeout(timer);
    return res;
  } catch (err) {
    clearTimeout(timer);
    throw err;
  }
}

export async function fetchTickers() {
  try {
    const res = await request('/tickers', 5_000);
    if (!res.ok) return null;
    const data = await res.json();
    return data.tickers ?? null;
  } catch {
    return null;
  }
}

export async function fetchHealth() {
  try {
    const res = await request('/health', 5_000);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

/**
 * Returns { ok, status, data, errorDetail }
 * ok=true  → data is the prediction payload
 * ok=false → status is HTTP code (or 0 for network), errorDetail is a string
 */
export async function fetchPrediction(ticker) {
  try {
    const res = await request(`/predict/${ticker}`);
    if (res.status === 400) {
      return { ok: false, status: 400, data: null, errorDetail: 'Ticker not supported.' };
    }
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try { const j = await res.json(); detail = j.detail ?? detail; } catch {}
      return { ok: false, status: res.status, data: null, errorDetail: detail };
    }
    const data = await res.json();
    return { ok: true, status: 200, data, errorDetail: null };
  } catch (err) {
    if (err.name === 'AbortError') {
      return {
        ok: false, status: 504, data: null,
        errorDetail: 'Request timed out. The pipeline may be cold — try again in a few seconds.',
      };
    }
    return {
      ok: false, status: 0, data: null,
      errorDetail: `Cannot reach API at ${API_BASE}. Make sure the backend is running.`,
    };
  }
}

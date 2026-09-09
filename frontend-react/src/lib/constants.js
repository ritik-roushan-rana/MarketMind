// Kept for reference by other modules that import it.
// The actual runtime value used for fetch() lives in api.js and reads
// from import.meta.env.VITE_API_BASE (set in Vercel dashboard).
export const API_BASE = 'http://localhost:8000';

export const TICKERS = [
  'AAPL','MSFT','NVDA','AMZN','GOOGL','META','TSLA',
  'JPM','GS','BAC','MS','XOM','JNJ','WMT','CAT',
];

export const TICKER_META = {
  AAPL:  { name: 'Apple Inc',        sector: 'HARDWARE' },
  MSFT:  { name: 'Microsoft',        sector: 'SOFTWARE' },
  NVDA:  { name: 'NVIDIA Corp',      sector: 'SEMICONDUCTOR' },
  AMZN:  { name: 'Amazon.com',       sector: 'COMMERCE/CLOUD' },
  GOOGL: { name: 'Alphabet Inc',     sector: 'SEARCH/AI' },
  META:  { name: 'Meta Platforms',   sector: 'SOCIAL MEDIA' },
  TSLA:  { name: 'Tesla Inc',        sector: 'AUTOMOTIVE' },
  JPM:   { name: 'JPMorgan Chase',   sector: 'BANKING' },
  GS:    { name: 'Goldman Sachs',    sector: 'INVESTMENT BANK' },
  BAC:   { name: 'Bank of America',  sector: 'RETAIL BANKING' },
  MS:    { name: 'Morgan Stanley',   sector: 'WEALTH MGMT' },
  XOM:   { name: 'Exxon Mobil',      sector: 'INTEGRATED OIL' },
  JNJ:   { name: 'Johnson & Johnson',sector: 'HEALTHCARE' },
  WMT:   { name: 'Walmart Inc',      sector: 'CONSUMER RETAIL' },
  CAT:   { name: 'Caterpillar',      sector: 'INDUSTRIALS' },
};

export const FEATURE_LABELS = {
  news_count_3d:       'News volume (3-day)',
  news_count_7d:       'News volume (7-day)',
  news_count_1d:       'News volume (1-day)',
  avg_sentiment_3d:    'Avg sentiment (3-day)',
  avg_sentiment_7d:    'Avg sentiment (7-day)',
  avg_sentiment_1d:    'Avg sentiment (1-day)',
  sentiment_std_3d:    'Sentiment std dev (3-day)',
  sentiment_std_7d:    'Sentiment std dev (7-day)',
  sent_pos_ratio_3d:   'Positive sentiment ratio (3-day)',
  sent_neg_ratio_3d:   'Negative sentiment ratio (3-day)',
  news_count_zscore:   'News volume z-score',
  sentiment_momentum:  'Sentiment momentum',
  vol_5d:              'Price volatility (5-day)',
  vol_20d:             'Price volatility (20-day)',
  ret_1d:              'Price return (1-day)',
  ret_3d:              'Price return (3-day)',
  ret_5d:              'Price return (5-day)',
  ret_20d:             'Price return (20-day)',
  sma_20d:             'SMA 20-day',
  sma_50d:             'SMA 50-day',
  ema_3d:              'EMA 3-day',
  rsi_14:              'RSI (14-day)',
  macd:                'MACD',
  macd_signal:         'MACD Signal',
  bb_position:         'Bollinger Band position',
  vix_close:           'VIX (fear index)',
  spy_ret_1d:          'S&P 500 return (1-day)',
  spy_ret_3d:          'S&P 500 return (3-day)',
  vol_ratio:           'Volume ratio',
};

export function getFeatureLabel(raw) {
  return FEATURE_LABELS[raw] ?? raw.replace(/_/g, ' ');
}

export const LOADING_STAGES = [
  'Fetching live prices from Finnhub...',
  'Collecting recent news headlines...',
  'Running FinBERT sentiment scoring...',
  'Assembling feature vector...',
  'Running XGBoost inference...',
  'Computing SHAP explanations...',
  'Generating plain-English summary...',
];

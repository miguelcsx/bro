import type { PredictionData } from '../components/PredictionChart';

interface PredictionResult {
  symbol: string;
  name: string;
  historicalData: Array<{ date: string; price: number }>;
  predictions: PredictionData;
  upperBound?: PredictionData;
  lowerBound?: PredictionData;
  predictionType: string;
  timeframe: string;
}

/**
 * Tries to extract a stock symbol (e.g. "AAPL") from a string.
 * Returns the symbol in uppercase or null if not found.
 */
export function extractSymbolFromContent(content: string): string | null {
  // Simple regex: finds uppercase words with 1-5 letters (common for tickers)
  const match = content.match(/\b[A-Z]{1,5}\b/);
  return match ? match[0] : null;
}

/**
 * Checks if the content is likely asking for a prediction or forecast.
 */
export function containsPredictionQuery(content: string): boolean {
  const keywords = [
    'forecast', 'predict', 'prediction', 'outlook', 'future', 'estimate', 'expected', 'projection'
  ];
  return keywords.some(keyword => content.toLowerCase().includes(keyword));
}

/**
 * Dummy extractor for predictions from a backend response.
 * Replace with your actual logic for extracting prediction data.
 */
export function extractPredictionsFromResponse(response: any, symbol: string): PredictionResult {
  // Implement actual parsing logic here
  return {
    symbol,
    name: `${symbol} Stock`,
    historicalData: [],
    predictions: {},
    predictionType: 'price',
    timeframe: '7D'
  };
}

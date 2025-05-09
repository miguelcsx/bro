import { PredictionData } from '../components/PredictionChart';

/**
 * Extracts prediction data from the backend API response
 * Adapt this function to match your backend's specific response format
 */
export const extractPredictionsFromResponse = (
  apiResponse: any,
  symbol: string
): PredictionData | null => {
  try {
    // Direct access for the new API format (preferred)
    // If predictions are in the top-level 'predictions' field
    if (apiResponse?.predictions) {
      return apiResponse.predictions;
    }
    
    // If your backend returns predictions in a standard format, use that
    if (apiResponse?.predictions?.data) {
      return formatPredictionData(apiResponse.predictions.data, symbol);
    }
    
    // Check for function call responses in LangChain format
    if (apiResponse?.content) {
      const content = apiResponse.content;
      
      // Look for AIMessage with function calls related to predictions
      const toolCallRegex = /tool_calls=\[.*?name='(forecast_stock|predict_price|analyze_volatility|analyze_trend)'.*?\]/;
      const hasToolCall = content.match(toolCallRegex);
      
      if (hasToolCall) {
        // Look for ToolMessage with the prediction results
        const toolMessageRegex = /ToolMessage\(content='([^']+)'.*?name='(forecast_stock|predict_price|analyze_volatility|analyze_trend)'/g;
        let toolMatch;
        let predictionContent = '';
        
        while ((toolMatch = toolMessageRegex.exec(content)) !== null) {
          predictionContent = toolMatch[1];
        }
        
        if (predictionContent) {
          try {
            // Try to parse the tool message content as JSON
            const predictionData = JSON.parse(
              predictionContent.replace(/'/g, '"').replace(/\\"/g, '"').replace(/\\n/g, '')
            );
            
            // Check if we have the new format with 'text' and 'data' fields
            if (predictionData.text && predictionData.data) {
              return predictionData.data;
            }
            
            return formatPredictionData(predictionData, symbol);
          } catch (error) {
            console.error("Error parsing prediction tool message:", error);
          }
        }
      }
    }
    
    // Check if there's a predictions field with a different name
    const predictionFieldNames = [
      'predictions', 
      'forecast', 
      'projections', 
      'forecastData',
      'price_predictions',
      'volatility_predictions',
      'trend_analysis'
    ];
    
    for (const field of predictionFieldNames) {
      if (apiResponse?.[field]) {
        return formatPredictionData(apiResponse[field], symbol);
      }
    }
    
    return null;
  } catch (error) {
    console.error("Error extracting predictions from response:", error);
    return null;
  }
};

/**
 * Formats prediction data from various possible formats into the standardized PredictionData format
 */
export const formatPredictionData = (
  data: any, 
  symbol: string
): PredictionData => {
  // Default values
  let historicalData: { date: string, price: number }[] = [];
  let predictions: { date: string, price: number }[] = [];
  let upperBound: { date: string, price: number }[] = [];
  let lowerBound: { date: string, price: number }[] = [];
  let predictionType: 'price' | 'volatility' | 'trend' = 'price';
  let timeframe = '30D';
  let name = `${symbol} Stock`;
  
  // Handle different possible data formats from your backend
  if (Array.isArray(data)) {
    // Format 1: Array of prediction points
    if (data.length > 0 && 'date' in data[0] && 'price' in data[0]) {
      predictions = data;
    }
  } else if (typeof data === 'object') {
    // Format 2: Object with historical and prediction arrays
    if (data.historical && Array.isArray(data.historical)) {
      historicalData = data.historical.map((point: any) => ({
        date: point.date || point.timestamp || '',
        price: parseFloat(point.price || point.value || 0)
      }));
    }
    
    if (data.predictions && Array.isArray(data.predictions)) {
      predictions = data.predictions.map((point: any) => ({
        date: point.date || point.timestamp || '',
        price: parseFloat(point.price || point.value || 0)
      }));
    }
    
    // Format 3: Confidence intervals
    if (data.upper_bound && Array.isArray(data.upper_bound)) {
      upperBound = data.upper_bound.map((point: any) => ({
        date: point.date || point.timestamp || '',
        price: parseFloat(point.price || point.value || 0)
      }));
    }
    
    if (data.lower_bound && Array.isArray(data.lower_bound)) {
      lowerBound = data.lower_bound.map((point: any) => ({
        date: point.date || point.timestamp || '',
        price: parseFloat(point.price || point.value || 0)
      }));
    }
    
    // Format 4: Additional metadata
    if (data.prediction_type) {
      predictionType = data.prediction_type;
    } else if (data.type) {
      // Map backend type values to our expected format
      const typeMap: { [key: string]: 'price' | 'volatility' | 'trend' } = {
        'price_forecast': 'price',
        'volatility_analysis': 'volatility',
        'trend_analysis': 'trend'
      };
      predictionType = typeMap[data.type] || 'price';
    }
    
    if (data.timeframe) {
      timeframe = data.timeframe;
    }
    
    if (data.name) {
      name = data.name;
    }
    
    if (data.symbol) {
      symbol = data.symbol;
    }
  }
  
  return {
    symbol,
    name,
    historicalData,
    predictions,
    upperBound: upperBound.length > 0 ? upperBound : undefined,
    lowerBound: lowerBound.length > 0 ? lowerBound : undefined,
    predictionType,
    timeframe
  };
};

/**
 * Determines if a message contains prediction-related content
 */
export const containsPredictionQuery = (content: string): boolean => {
  const predictionKeywords = [
    'forecast',
    'predict',
    'projection',
    'volatility',
    'trend',
    'analysis',
    'future price',
    'price target',
    'in the future',
    'will go up',
    'will go down',
    'expected to',
    'price movement'
  ];
  
  const lowercaseContent = content.toLowerCase();
  return predictionKeywords.some(keyword => lowercaseContent.includes(keyword));
};

/**
 * Extracts the stock symbol from a text message
 */
export const extractSymbolFromContent = (content: string): string | null => {
  // Look for prediction indicators in the content text
  const predictionPatterns = [
    /(?:forecast|predict(?:ed|ion)|projection)(?:.*)(?:for|of)\s+([A-Z]+)/i,
    /([A-Z]+)(?:.*)(?:forecast|predict(?:ed|ion)|projection)/i,
    /volatility(?:.*)(?:for|of)\s+([A-Z]+)/i,
    /([A-Z]+)(?:.*)volatility/i,
    /trend(?:.*)(?:for|of)\s+([A-Z]+)/i,
    /([A-Z]+)(?:.*)trend/i,
    /([A-Z]{1,5}) (?:stock|price|shares)/i,
    /([A-Z]{1,5})(?:\s+in|\s+will|\s+may)/i
  ];
  
  // Check each pattern for a match
  for (const pattern of predictionPatterns) {
    const match = content.match(pattern);
    if (match && match[1]) {
      return match[1];
    }
  }
  
  return null;
};

/**
 * Creates mock prediction data from text that contains price prediction information
 * Used as a fallback when the API doesn't return structured data
 */
export const createMockPredictionFromText = (content: string): PredictionData | null => {
  // Extract stock symbol
  const symbol = extractSymbolFromContent(content);
  if (!symbol) {
    return null;
  }
  
  // Look for price predictions in the content
  const pricePattern = /predicted.*?price.*?is \$([0-9.,]+)/i;
  const lowerBoundPattern = /lower bound of \$([0-9.,]+)/i;
  const upperBoundPattern = /upper bound of \$([0-9.,]+)/i;
  
  const priceMatch = content.match(pricePattern);
  const lowerMatch = content.match(lowerBoundPattern);
  const upperMatch = content.match(upperBoundPattern);
  
  if (!priceMatch) {
    return null;
  }
  
  const predictedPrice = parseFloat(priceMatch[1].replace(/,/g, ''));
  const lowerBoundPrice = lowerMatch ? parseFloat(lowerMatch[1].replace(/,/g, '')) : predictedPrice * 0.95;
  const upperBoundPrice = upperMatch ? parseFloat(upperMatch[1].replace(/,/g, '')) : predictedPrice * 1.05;
  
  // Generate dates
  const today = new Date();
  const dates: string[] = [];
  const historicalPrices: number[] = [];
  const predictionPrices: number[] = [];
  const lowerBoundPrices: number[] = [];
  const upperBoundPrices: number[] = [];
  
  // Generate historical data (30 days before today)
  for (let i = 30; i >= 0; i--) {
    const date = new Date();
    date.setDate(today.getDate() - i);
    dates.push(date.toISOString().split('T')[0]);
    
    // Generate random historical prices that trend toward the prediction
    const randomFactor = 0.98 + Math.random() * 0.04; // Random between 0.98 and 1.02
    const trendFactor = 1 + ((i / 30) * 0.1); // Trend factor to make historical data trend toward prediction
    historicalPrices.push(predictedPrice * randomFactor * trendFactor);
  }
  
  // Generate prediction data (7 days after today)
  for (let i = 1; i <= 7; i++) {
    const date = new Date();
    date.setDate(today.getDate() + i);
    const dateStr = date.toISOString().split('T')[0];
    
    // First prediction point is the predicted price
    const price = i === 1 ? predictedPrice : predictedPrice * (0.98 + Math.random() * 0.04);
    const lower = i === 1 ? lowerBoundPrice : price * 0.95;
    const upper = i === 1 ? upperBoundPrice : price * 1.05;
    
    dates.push(dateStr);
    predictionPrices.push(price);
    lowerBoundPrices.push(lower);
    upperBoundPrices.push(upper);
  }
  
  // Format data for the PredictionData interface
  const historicalData = dates.slice(0, 31).map((date, index) => ({
    date,
    price: historicalPrices[index]
  }));
  
  const predictions = dates.slice(31).map((date, index) => ({
    date,
    price: predictionPrices[index]
  }));
  
  const upperBound = dates.slice(31).map((date, index) => ({
    date, 
    price: upperBoundPrices[index]
  }));
  
  const lowerBound = dates.slice(31).map((date, index) => ({
    date,
    price: lowerBoundPrices[index]
  }));
  
  return {
    symbol,
    name: `${symbol} Stock`,
    historicalData,
    predictions,
    upperBound,
    lowerBound,
    predictionType: 'price',
    timeframe: '7D'
  };
}; 
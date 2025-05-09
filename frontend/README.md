# Financial Chatbot with Interactive Charts

A React-based financial chatbot interface with real-time stock and prediction data visualization.

## Features

- Interactive chat interface for financial queries
- Real-time stock data visualization using recharts
- Financial forecasting and prediction visualization
- Responsive design that works on all devices

## Getting Started

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm start
   ```

## Connecting with the Backend

The frontend is designed to work with a backend API running at `http://localhost:8888/query`. The API is expected to:

1. Process natural language queries about stocks and financial predictions
2. Return stock data, prediction data, or text responses

### API Response Format

The API response should follow this format:

```json
{
  "success": true,
  "content": "String containing AIMessage and ToolMessage information from LangChain"
}
```

### Integrating Prediction Data

To enable prediction charts in the frontend, your backend should implement one of these approaches:

#### Option 1: Use MCP Tools for Predictions

1. Create a custom MCP tool in your backend:

```python
@tool
def forecast_stock(symbol: str) -> dict:
    """
    Generate price predictions for a stock
    
    Args:
        symbol: The stock symbol to forecast
        
    Returns:
        A dictionary with historical and prediction data
    """
    # Your forecasting logic here
    return {
        "historical": [
            {"date": "2023-01-01", "price": 100.0},
            # More historical data points...
        ],
        "predictions": [
            {"date": "2023-02-01", "price": 105.0},
            # More prediction data points...
        ],
        "upper_bound": [
            {"date": "2023-02-01", "price": 110.0},
            # More upper bound data points...
        ],
        "lower_bound": [
            {"date": "2023-02-01", "price": 100.0},
            # More lower bound data points...
        ],
        "prediction_type": "price", # Can be 'price', 'volatility', or 'trend'
        "timeframe": "30D"
    }
```

2. Configure your agent to call this tool when prediction-related queries are detected

#### Option 2: Add a Prediction Field to the Response

Alternatively, you can add a dedicated field in your API response:

```json
{
  "success": true,
  "content": "...",
  "predictions": {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "historical": [
      {"date": "2023-01-01", "price": 150.0}
    ],
    "predictions": [
      {"date": "2023-02-01", "price": 160.0}
    ],
    "upper_bound": [
      {"date": "2023-02-01", "price": 165.0}
    ],
    "lower_bound": [
      {"date": "2023-02-01", "price": 155.0}
    ],
    "prediction_type": "price",
    "timeframe": "30D"
  }
}
```

## Customizing the Prediction Charts

The prediction chart component can be customized to fit your specific needs:

1. Update styles in `src/components/PredictionChart.css`
2. Modify the chart configuration in `src/components/PredictionChart.tsx`
3. Adjust the data processing in `src/utils/predictionHelpers.ts`

## Handling Different Prediction Types

The frontend supports three types of predictions:

1. **Price Predictions**: Forecasts of future stock prices
2. **Volatility Predictions**: Analysis of expected price volatility
3. **Trend Analysis**: Directional trend predictions

You can specify the prediction type in the response data's `prediction_type` field.

## Testing Without Backend Integration

For testing purposes, the frontend includes a mock data generator that creates realistic-looking prediction data. To use it:

1. Look for the `generateMockPredictionData` function in the utilities
2. Uncomment it and modify as needed for testing
3. Make sure to disable it when connecting to a real backend

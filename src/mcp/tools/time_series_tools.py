"""
Time Series tools for MCP
"""

from mcp.types import TextContent
from pydantic import Field
from src.mcp.server import mcp_server
from src.ingestion.clients import yahoo_client
from src.analysis.time_series.fbprophet import FBProphetModel
from typing import Dict, List, Any
from src.ingestion.clients.yahoo import YahooFinanceClient
import pandas as pd
from datetime import datetime, timedelta

@mcp_server.tool()
def fbprophet_forecast(
     company: str = Field(..., description="Company ticker symbol"),
    predict_col: str = Field(..., description="Column to predict (e.g., 'Close')"),
    years_data: int = Field(..., description="Number of years of historical data to use"),
    future_days: int = Field(..., description="Number of days to forecast into the future"),
) -> TextContent:
    """
    Prophet forecast tool
    """

    try: 
        prophet_model = FBProphetModel(
            company=company,
            predict_col=predict_col,
            years_data=years_data,
            client=yahoo_client
        )

        forecast = prophet_model.forecast(days=future_days)

        return TextContent(
            type="text",
            text=f"Forecast for {company}:\n{forecast}",
            metadata={"company": company, "predict_col": predict_col}
        )
    except Exception as e:
        return TextContent(
            type="text",
            text=f"Error: {str(e)}",
            metadata={"company": company, "predict_col": predict_col}
        )

@mcp_server.tool()
def forecast_stock(
    symbol: str = Field(..., description="Company ticker symbol"),
    timeframe: str = Field("30D", description="Prediction timeframe (7D, 30D, 90D, 1Y)"),
    predict_col: str = Field("Close", description="Column to predict (e.g., 'Close')"),
    years_data: int = Field(2, description="Number of years of historical data to use"),
) -> Dict:
    """
    Returns structured price prediction data for frontend charting.
    This is a comprehensive tool that returns both the analysis text and the data
    needed to create interactive charts in the frontend.
    """
    try:
        # Calculate the future days based on timeframe
        days_map = {"7D": 7, "30D": 30, "90D": 90, "1Y": 365}
        future_days = days_map.get(timeframe, 30)
        
        # Get historical data
        client = YahooFinanceClient()
        historical_df = client.get_historic_data(symbol, years=years_data)
        
        # Create the model
        prophet_model = FBProphetModel(
            company=symbol,
            predict_col=predict_col,
            years_data=years_data,
            client=client
        )
        
        # Get forecast with confidence intervals
        forecast_df = prophet_model.forecast_dataframe(days=future_days)
        
        # Get company name
        company_info = client.get_company_info(symbol)
        name = company_info.get('longName', symbol)
        
        # Prepare historical data in the format required by frontend
        historical_data = []
        for date, row in historical_df.iterrows():
            historical_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": float(row[predict_col])
            })
        
        # Prepare prediction data
        predictions = []
        upper_bound = []
        lower_bound = []
        
        for _, row in forecast_df.iterrows():
            pred_date = row['ds'].strftime("%Y-%m-%d")
            
            # Main prediction
            predictions.append({
                "date": pred_date,
                "price": float(row['yhat'])
            })
            
            # Upper bound
            upper_bound.append({
                "date": pred_date,
                "price": float(row['yhat_upper'])
            })
            
            # Lower bound
            lower_bound.append({
                "date": pred_date,
                "price": float(row['yhat_lower'])
            })
        
        # Create a descriptive forecast text
        last_historical_price = historical_data[-1]["price"]
        last_prediction_price = predictions[-1]["price"]
        percent_change = ((last_prediction_price - last_historical_price) / last_historical_price) * 100
        
        forecast_text = f"I've forecasted the stock price for {name} ({symbol}) over the next {timeframe}. "
        if percent_change > 0:
            forecast_text += f"The price is expected to increase by approximately {percent_change:.2f}%. "
        else:
            forecast_text += f"The price is expected to decrease by approximately {abs(percent_change):.2f}%. "
            
        forecast_text += f"The final predicted price is ${last_prediction_price:.2f}, "
        forecast_text += f"with a confidence interval between ${lower_bound[-1]['price']:.2f} and ${upper_bound[-1]['price']:.2f}."
        
        # Return both the text analysis and the data structure
        return {
            "text": forecast_text,
            "data": {
                "symbol": symbol,
                "name": name,
                "historical": historical_data,
                "predictions": predictions,
                "upper_bound": upper_bound,
                "lower_bound": lower_bound,
                "prediction_type": "price",
                "timeframe": timeframe
            }
        }
    except Exception as e:
        return {
            "text": f"Error forecasting {symbol}: {str(e)}",
            "data": None
        }

@mcp_server.tool()
def analyze_trend(
    symbol: str = Field(..., description="Company ticker symbol"),
    timeframe: str = Field("30D", description="Prediction timeframe (7D, 30D, 90D, 1Y)"),
    predict_col: str = Field("Close", description="Column to predict (e.g., 'Close')"),
    years_data: int = Field(2, description="Number of years of historical data to use"),
) -> Dict:
    """
    Returns structured trend analysis data for frontend charting.
    This tool analyzes the trend direction and strength.
    """
    try:
        # Calculate the future days based on timeframe
        days_map = {"7D": 7, "30D": 30, "90D": 90, "1Y": 365}
        future_days = days_map.get(timeframe, 30)
        
        # Get historical data
        client = YahooFinanceClient()
        historical_df = client.get_historic_data(symbol, years=years_data)
        
        # Create the model and get forecast
        prophet_model = FBProphetModel(
            company=symbol,
            predict_col=predict_col,
            years_data=years_data,
            client=client
        )
        
        # Get components to analyze trend
        forecast_df, components = prophet_model.forecast_with_components(days=future_days)
        
        # Get company name
        company_info = client.get_company_info(symbol)
        name = company_info.get('longName', symbol)
        
        # Prepare historical data in the format required by frontend
        historical_data = []
        for date, row in historical_df.iterrows():
            historical_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": float(row[predict_col])
            })
        
        # Prepare trend data (using the trend component)
        predictions = []
        # Add some variance to make the trend more visually interesting
        import numpy as np
        
        for _, row in forecast_df.iterrows():
            pred_date = row['ds'].strftime("%Y-%m-%d")
            # Use trend component for trend analysis
            trend_value = float(row['trend'])
            
            predictions.append({
                "date": pred_date,
                "price": trend_value
            })
        
        # Calculate upper and lower bounds based on trend variance
        trend_std = np.std([p["price"] for p in predictions])
        upper_bound = []
        lower_bound = []
        
        for pred in predictions:
            upper_bound.append({
                "date": pred["date"],
                "price": pred["price"] + trend_std * 1.5
            })
            
            lower_bound.append({
                "date": pred["date"],
                "price": pred["price"] - trend_std * 1.5
            })
        
        # Analyze trend direction
        start_trend = predictions[0]["price"]
        end_trend = predictions[-1]["price"]
        trend_change = end_trend - start_trend
        
        # Create a descriptive trend analysis text
        trend_direction = "upward" if trend_change > 0 else "downward"
        trend_strength = "strong" if abs(trend_change) > (start_trend * 0.1) else "moderate"
        
        trend_text = f"I've analyzed the trend for {name} ({symbol}) over the next {timeframe}. "
        trend_text += f"The stock shows a {trend_strength} {trend_direction} trend. "
        
        if trend_change > 0:
            trend_text += f"The trend is expected to increase by approximately {(trend_change/start_trend)*100:.2f}%. "
        else:
            trend_text += f"The trend is expected to decrease by approximately {abs(trend_change/start_trend)*100:.2f}%. "
        
        # Return both the text analysis and the data structure
        return {
            "text": trend_text,
            "data": {
                "symbol": symbol,
                "name": name,
                "historical": historical_data,
                "predictions": predictions,
                "upper_bound": upper_bound,
                "lower_bound": lower_bound,
                "prediction_type": "trend",
                "timeframe": timeframe
            }
        }
    except Exception as e:
        return {
            "text": f"Error analyzing trend for {symbol}: {str(e)}",
            "data": None
        }

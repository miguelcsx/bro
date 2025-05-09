""" 
Volatility tools for MCP
"""

from mcp.server.fastmcp import Image
from mcp.types import TextContent, ImageContent
from typing import Tuple, Dict, List, Any
from pydantic import Field
from src.mcp.server import mcp_server
from src.ingestion.clients import yahoo_client
from src.analysis.volatility.garch import GARCHModel
from src.analysis.volatility.xgboost_volatility import XGBoostVolatility
from src.ingestion.clients.yahoo import YahooFinanceClient  # Ensure this is imported
import pandas as pd
import json
from datetime import datetime, timedelta

@mcp_server.tool()
def garch_volatility(
    company: str = Field(..., description="Company ticker symbol"),
    predict_col: str = Field(..., description="Column to predict (e.g., 'Close')"),
    years_data: int = Field(..., description="Number of years of historical data to use"),
    future_days: int = Field(..., description="Number of days to forecast into the future"),
) -> TextContent:
    """
    GARCH volatility tool
    """
    try:
        # Initialize the GARCH model
        garch_model = GARCHModel(company, predict_col, years_data, future_days)
        forecast = garch_model.forecast(days=future_days)
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
def xgboost_volatility(
    company: str = Field(..., description="Company ticker symbol"),
    predict_col: str = Field(..., description="Column to predict (e.g., 'Close')"),
    years_data: int = Field(..., description="Number of years of historical data to use"),
    future_days: int = Field(..., description="Number of days to forecast into the future"),
) -> TextContent:
    """
    XGBoost volatility tool
    """
    try:
        client = YahooFinanceClient()
        xgboost_model = XGBoostVolatility(company, predict_col, years_data, client=client)
        forecast = xgboost_model.forecast(days=future_days)
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
def analyze_volatility(
    symbol: str = Field(..., description="Company ticker symbol"),
    timeframe: str = Field("30D", description="Prediction timeframe (7D, 30D, 90D, 1Y)"),
    predict_col: str = Field("Close", description="Column to predict (e.g., 'Close')"),
    years_data: int = Field(2, description="Number of years of historical data to use"),
) -> Dict:
    """
    Returns structured volatility prediction data for frontend charting.
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
        xgboost_model = XGBoostVolatility(symbol, predict_col, years_data, client=client)
        
        # Get forecast with confidence intervals
        forecast_data = xgboost_model.forecast(days=future_days, with_confidence=True)
        
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
        
        for i, (date, forecast) in enumerate(forecast_data.items()):
            pred_date = date.strftime("%Y-%m-%d")
            
            # Main prediction
            predictions.append({
                "date": pred_date,
                "price": float(forecast['mean'])
            })
            
            # Upper bound
            upper_bound.append({
                "date": pred_date,
                "price": float(forecast['mean'] + forecast['std'])
            })
            
            # Lower bound
            lower_bound.append({
                "date": pred_date,
                "price": float(forecast['mean'] - forecast['std'])
            })
        
        # Create a descriptive forecast text
        forecast_text = f"I've analyzed the volatility for {name} ({symbol}) over the next {timeframe}. "
        forecast_text += f"Based on historical data, I expect the volatility to "
        
        # Determine if volatility is increasing or decreasing
        volatility_trend = "increase" if predictions[-1]["price"] > predictions[0]["price"] else "decrease"
        forecast_text += f"{volatility_trend} during this period. "
        forecast_text += f"The price is expected to move within a range of ${lower_bound[-1]['price']:.2f} to ${upper_bound[-1]['price']:.2f} at the end of the period."
        
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
                "prediction_type": "volatility",
                "timeframe": timeframe
            }
        }
    except Exception as e:
        return {
            "text": f"Error analyzing volatility for {symbol}: {str(e)}",
            "data": None
        }
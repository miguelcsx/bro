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
from src.analysis.volatility.rsi_measure import RSIModel
from src.ingestion.clients.yahoo import YahooFinanceClient 
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
    GARCH volatility forecasting tool with confidence intervals
    """
    try:
        # Initialize model with proper parameters
        garch_model = GARCHModel(
            company=company,
            predict_col=predict_col,
            years_data=years_data,
            client=yahoo_client  # Use shared Yahoo client
        )

        # Generate forecast and get structured data
        garch_model.forecast(days=future_days)
        forecast_data = garch_model.get_forecast_dict()

        # Format for human-readable output
        formatted_forecast = "\n".join(
            [f"{date}: {values['Predicted']:.2f}% ({values['Lower']:.2f}-{values['Upper']:.2f})" 
             for date, values in forecast_data.items()]
        )

        return TextContent(
            type="text",
            text=f"GARCH Volatility Forecast for {company} ({predict_col}):\n{formatted_forecast}",
            metadata={
                "company": company,
                "predict_col": predict_col,
                "raw_forecast": forecast_data  # Include structured data
            }
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
    XGBoost volatility forecasting tool with confidence intervals
    """
    try:
        # Initialize model with shared Yahoo client
        xgboost_model = XGBoostVolatility(
            company=company,
            predict_col=predict_col,
            years_data=years_data,
            client=yahoo_client  # Use pre-configured client
        )

        # Generate forecast and get structured data
        xgboost_model.forecast(days=future_days)
        forecast_data = xgboost_model.get_forecast_dict()

        # Format for human-readable output
        formatted_forecast = "\n".join(
            [f"{date}: ${values['Predicted']:.2f} (${values['Lower']:.2f}-${values['Upper']:.2f})" 
             for date, values in forecast_data.items()]
        )

        return TextContent(
            type="text",
            text=f"XGBoost Volatility Forecast for {company} ({predict_col}):\n{formatted_forecast}",
            metadata={
                "company": company,
                "predict_col": predict_col,
                "raw_forecast": forecast_data  # Structured data for APIs
            }
        )
        
    except Exception as e:
        return TextContent(
            type="text",
            text=f"Error: {str(e)}",
            metadata={"company": company, "predict_col": predict_col}
        )
    
@mcp_server.tool()
def rsi_analyzer(
    company: str = Field(..., description="Company ticker symbol"),
    window: int = Field(14, description="RSI calculation window (typically 14)"),
    years_data: int = Field(2, description="Years of historical data to analyze"),
    overbought: int = Field(70, description="Overbought threshold (70-100)"),
    oversold: int = Field(30, description="Oversold threshold (0-30)")
) -> TextContent:
    """
    RSI analysis tool with historical context and actionable insights
    Returns structured data with current status, historical context, and recent values
    """
    try:
        # Initialize model with shared configuration
        rsi_model = RSIModel(
            company=company,
            window=window,
            overbought=overbought,
            oversold=oversold,
            years_data=years_data,
            client=yahoo_client  # Use shared Yahoo client
        )

        # Get structured analysis results
        analysis_data = rsi_model.analyze()
        
        # Create human-readable summary
        summary = (
            f"RSI Analysis for {company}:\n"
            f"Current RSI: {analysis_data['current_rsi']:.2f} ({analysis_data['status'].capitalize()})\n"
            f"Recommended Action: {analysis_data['action']} ({analysis_data['confidence'].capitalize()} confidence)\n"
            f"Historical Context: {analysis_data['historical_context']['days_overbought']} overbought days, "
            f"{analysis_data['historical_context']['days_oversold']} oversold days"
        )

        return TextContent(
            type="text",
            text=summary,
            metadata={
                "company": company,
                "raw_analysis": analysis_data  # Preserve full structured data
            }
        )
        
    except Exception as e:
        return TextContent(
            type="text",
            text=f"RSI Analysis Error: {str(e)}",
            metadata={"company": company}
        )

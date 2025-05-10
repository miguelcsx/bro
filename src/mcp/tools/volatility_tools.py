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
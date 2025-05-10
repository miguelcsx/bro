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
    Prophet forecast tool returning structured forecast data
    """
    try: 
        prophet_model = FBProphetModel(
            company=company,
            predict_col=predict_col,
            years_data=years_data,
            client=yahoo_client
        )

        # Generate forecast and get dictionary
        prophet_model.forecast(days=future_days)
        forecast_data = prophet_model.get_forecast_dict()

        # Format dictionary for readable output
        formatted_output = "\n".join(
            [f"{date}: ${values['Predicted']:.2f} (${values['Lower']:.2f}-${values['Upper']:.2f})" 
             for date, values in forecast_data.items()]
        )

        return TextContent(
            type="text",
            text=f"Prophet Forecast for {company} ({predict_col}):\n{formatted_output}",
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

"""
Probabilistic tools for MCP
"""

from mcp.server.fastmcp import Image
from mcp.types import TextContent, ImageContent
from typing import Tuple
from src.analysis.probabilistic.hmm import HMMModel
from src.mcp.server import mcp_server
from src.ingestion.clients import yahoo_client
from src.analysis.probabilistic.arima import ARIMAModel
from src.analysis.probabilistic.kalman_filter import KalmanFilterModel
from pydantic import BaseModel, Field
from PIL import Image as PILImage

@mcp_server.tool()
def arima_forecast(
    company: str = Field(..., description="Company ticker symbol"),
    predict_col: str = Field(..., description="Column to predict (e.g., 'Close')"),
    years_data: int = Field(..., description="Number of years of historical data to use"),
    future_days: int = Field(..., description="Number of days to forecast into the future"),
) -> TextContent:
    """
    ARIMA forecast tool returning structured forecast data
    """
    try:        
        # Initialize the ARIMA model
        arima_model = ARIMAModel(
            company=company,
            predict_col=predict_col,
            years_data=years_data,
            client=yahoo_client
        )

        # Generate forecast and get dictionary
        arima_model.forecast(days=future_days)
        forecast_data = arima_model.get_forecast_dict()

        # Format dictionary for readable output
        formatted_output = "\n".join(
            [f"{date}: ${values['Predicted']:.2f} (${values['Lower']:.2f}-${values['Upper']:.2f})" 
             for date, values in forecast_data.items()]
        )

        return TextContent(
            type="text",
            text=f"ARIMA Forecast for {company} ({predict_col}):\n{formatted_output}",
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
def hmm_forecast(
    company: str = Field(..., description="Company ticker symbol"),
    predict_col: str = Field(..., description="Column to predict (e.g., 'Close')"),
    years_data: int = Field(..., description="Number of years of historical data to use"),
    future_days: int = Field(..., description="Number of days to forecast into the future"),
) -> TextContent:
    """
    HMM forecast tool returning structured forecast data
    """
    try:
        # Initialize the HMM model
        hmm = HMMModel(
            company=company,
            predict_col=predict_col,
            years_data=years_data,
            client=yahoo_client
        )

        # Generate forecast and get dictionary
        hmm.forecast(days=future_days)
        forecast_data = hmm.get_forecast_dict()
        
        # Format dictionary for readable output
        formatted_output = "\n".join(
            [f"{date}: ${values['Predicted']:.2f} (${values['Lower']:.2f}-${values['Upper']:.2f})" 
             for date, values in forecast_data.items()]
        )

        return TextContent(
            type="text",
            text=f"HMM Forecast for {company} ({predict_col}):\n{formatted_output}",
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
def kalman_forecast(
    company: str = Field(..., description="Company ticker symbol"),
    predict_col: str = Field(..., description="Column to predict (e.g., 'Close')"),
    years_data: int = Field(..., description="Number of years of historical data to use"),
    future_days: int = Field(..., description="Number of days to forecast into the future"),
) -> TextContent:
    """
    Kalman Filter forecast tool returning structured forecast data
    """
    try:
        # Initialize the HMM model
        kalman = KalmanFilterModel(
            company=company,
            predict_col=predict_col,
            years_data=years_data,
            client=yahoo_client
        )

        # Generate forecast and get dictionary
        kalman.forecast(days=future_days)
        forecast_data = kalman.get_forecast_dict()
        
        # Format dictionary for readable output
        formatted_output = "\n".join(
            [f"{date}: ${values['Predicted']:.2f} (${values['Lower']:.2f}-${values['Upper']:.2f})" 
             for date, values in forecast_data.items()]
        )

        return TextContent(
            type="text",
            text=f"Kalman Filter Forecast for {company} ({predict_col}):\n{formatted_output}",
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


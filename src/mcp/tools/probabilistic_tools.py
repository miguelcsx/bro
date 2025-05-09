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
from pydantic import BaseModel, Field
from PIL import Image as PILImage

@mcp_server.tool()
def arima_forecast(
    company: str = Field(..., description="Company ticker symbol"),
    predict_col: str = Field(..., description="Column to predict (e.g., 'Close')"),
    years_data: int = Field(..., description="Number of years of historical data to use"),
    future_days: int = Field(..., description="Number of days to forecast into the future"),
) -> dict:
    """
    ARIMA forecast tool
    """
    try:        
        # Initialize the ARIMA model
        arima_model = ARIMAModel(
            company=company,
            predict_col=predict_col,
            years_data=years_data,
            client=yahoo_client
        )

        # Generate forecast
        arima_model.forecast(days=future_days)

        # Get both text and structured prediction data
        response = arima_model.get_prediction_response(timeframe=f"{future_days}D")
        return response

    except Exception as e:
        return {
            "text": f"Error: {str(e)}",
            "data": None,
            "metadata": {"company": company, "predict_col": predict_col}
        }

@mcp_server.tool()
def hmm_forescast(
    company: str = Field(..., description="Company ticker symbol"),
    predict_col: str = Field(..., description="Column to predict (e.g., 'Close')"),
    years_data: int = Field(..., description="Number of years of historical data to use"),
    future_days: int = Field(..., description="Number of days to forecast into the future"),
) -> TextContent:
    """
    HMM forecast tool
    """
    try:
        # Initialize the HMM model
        hmm = HMMModel(
            company=company,
            predict_col=predict_col,
            years_data=years_data,
            client=yahoo_client
        )

        # Generate forecast
        forecast = hmm.forecast(days=future_days)

        # Save forecast results
        # hmm.save_forecast()

        img = PILImage.open(hmm.plot(show=False))
        img.thumbnail((100, 100))

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

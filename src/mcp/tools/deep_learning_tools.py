"""
Deep Learning tools for MCP
"""

from mcp.server.fastmcp import Image
from mcp.types import TextContent, ImageContent
from typing import Tuple
from src.mcp.server import mcp_server
from src.ingestion.clients import yahoo_client
from src.analysis.deep_learning.lstm import LSTMModel
from pydantic import BaseModel, Field
from PIL import Image as PILImage

@mcp_server.tool()
def lstm_forecast(
    company: str = Field(..., description="Company ticker symbol"),
    predict_col: str = Field(..., description="Column to predict (e.g., 'Close')"),
    years_data: int = Field(..., description="Number of years of historical data to use"),
    future_days: int = Field(..., description="Number of days to forecast into the future"),
) -> TextContent:
    """
    LSTM forecast tool
    """
    try:
        # Initialize the LSTM model
        lstm_model = LSTMModel(
            company=company,
            predict_col=predict_col,
            years_data=years_data,
            client=yahoo_client
        )

        # Generate forecast
        forecast = lstm_model.forecast(days=future_days)

        # Save forecast results
        # lstm_model.save_forecast()

        img = PILImage.open(lstm_model.plot(show=False))
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

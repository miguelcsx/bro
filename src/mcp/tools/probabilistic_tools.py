"""
Probabilistic tools for MCP
"""

from mcp.server.fastmcp import Image
from mcp.types import TextContent, ImageContent
from typing import Tuple
from src.mcp.server import mcp_server
from src.ingestion.clients.yahoo import YahooFinanceClient
from src.analysis.probabilistic.arima import ARIMAModel
from pydantic import BaseModel, Field
from PIL import Image as PILImage

@mcp_server.tool()
def arima_forecast(
    company: str = Field(..., description="Company ticker symbol"),
    predict_col: str = Field(..., description="Column to predict (e.g., 'Close')"),
    years_data: int = Field(..., description="Number of years of historical data to use"),
    future_days: int = Field(..., description="Number of days to forecast into the future"),
) -> Tuple[TextContent, Image]:
    """
    ARIMA forecast tool
    """
    try:
        # Create Yahoo Finance client
        yahoo_client = YahooFinanceClient()
        
        # Initialize the ARIMA model
        arima_model = ARIMAModel(
            company=company,
            predict_col=predict_col,
            years_data=years_data,
            client=yahoo_client
        )

        # Generate forecast
        forecast = arima_model.forecast(days=future_days)

        # Save forecast results
        # arima_model.save_forecast()

        img = PILImage.open(arima_model.plot(show=False))
        img.thumbnail((100, 100))

        return (
            TextContent(
            type="text",
            text=f"Forecast for {company}:\n{forecast}",
            metadata={"company": company, "predict_col": predict_col}
        ),
            Image(
                data=img.tobytes(),
                format="jpg",
            ) 
        )

    except Exception as e:
        return TextContent(
            type="text",
            text=f"Error: {str(e)}",
            metadata={"company": company, "predict_col": predict_col}
        )

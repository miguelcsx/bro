
from mcp.server.fastmcp import Image
from mcp.types import TextContent
from typing import Tuple
from src.analysis.machine_learning.classification_prediction import StockDirectionPredictor
from src.mcp.server import mcp_server
from src.ingestion.clients import yahoo_client
from pydantic import BaseModel, Field


@mcp_server.tool()
def ml_direction_forecast(
    company: str = Field(..., description="Company ticker symbol"),
    years_data: int = Field(5, description="Years of historical data to use"),
    prediction_days: int = Field(1, description="Number of days to forecast")
) -> TextContent:
    """
    Machine Learning stock direction forecast with model consensus probabilities
    Returns structured prediction data with model-level metrics
    """
    try:
        # Initialize predictor with shared configuration
        predictor = StockDirectionPredictor(
            company=company,
            years_data=years_data,
            client=yahoo_client  # Use shared Yahoo client
        )

        # Get structured prediction results
        prediction_data = predictor.predict_direction(days=prediction_days)
        
        # Create human-readable summary
        summary = (
            f"ML Direction Forecast for {company}:\n"
            f"Consensus Up Probability: {prediction_data['consensus']['up_prob']:.2%}\n"
            f"Consensus Down Probability: {prediction_data['consensus']['down_prob']:.2%}\n"
            f"Top Performing Model: {max(prediction_data['models'].items(), key=lambda x: x[1]['auc'])[0]} "
            f"(AUC: {max(prediction_data['models'].values(), key=lambda x: x['auc'])['auc']:.3f})"
        )

        return TextContent(
            type="text",
            text=summary,
            metadata={
                "company": company,
                "raw_prediction": prediction_data  # Preserve full structured data
            }
        )
        
    except Exception as e:
        return TextContent(
            type="text",
            text=f"ML Direction Forecast Error: {str(e)}",
            metadata={"company": company}
        )

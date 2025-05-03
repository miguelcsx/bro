import logging
import os
import pandas as pd
from datetime import datetime
from sklearn.metrics import mean_absolute_error, mean_squared_error
from src.ingestion.clients.yahoo import YahooFinanceClient
from src.analysis.probabilistic.arima import ARIMAModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('forecast.log'),
        logging.StreamHandler()
    ]
)

def main():
    try:
        client = YahooFinanceClient()
        forecaster = ARIMAModel(
            company="AAPL",
            predict_col="Close",
            years_data=5,
            client=client
        )
        
        # Generate forecast
        forecast = forecaster.forecast(days=15)  # Now calls the method properly
        
        print(f"Forecast for {forecaster.company}:\n{forecast}")
        

        # Plot results
        forecaster.plot(show=True)
        
        # Save data
        # forecaster.save_forecast()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()

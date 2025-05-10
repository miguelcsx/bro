"""
ARIMA (AutoRegressive Integrated Moving Average) model for time series forecasting.
Simplified implementation with essential features for stock price prediction.
"""

import os 
import numpy as np
import pandas as pd
import warnings
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime, timedelta

from src.ingestion.clients.yahoo import YahooFinanceClient

warnings.filterwarnings('ignore')

class ARIMAModel:
    """ARIMA forecaster using YahooFinanceClient for data access"""
    
    def __init__(self, company, predict_col='Close', years_data=5, client=None):
        self.company = company
        self.predict_col = predict_col
        self.years_data = years_data
        self.client = client or YahooFinanceClient()
        self.model = None
        self.data = None
        self.forecast_results = None
        self._load_data()

    def _generate_filename(self, file_type):
        """Generate standardized filenames"""
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{self.company}_{self.predict_col}_{file_type}_{date_str}"
    
    def save_forecast(self):
        """Save forecast results to CSV"""
        if self.forecast_results is None:
            raise ValueError("Run forecast() first")
            
        filename = self._generate_filename('forecast') + '.csv'
        filepath = os.path.join('results', filename)
        self.forecast_results.round(2).to_csv(filepath)
        print(f"Saved forecast to {filepath}")
        
    def _load_data(self):
        """Load historical data using YahooFinanceClient"""
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=self.years_data*365)
        
        # Get data from client
        df = self.client.get_historical_data(
            symbol=self.company,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval='1d'
        )
        
        # Check for empty DataFrame (e.g., symbol not found)
        if df is None or df.empty:
            raise ValueError(f"No historical data found for symbol '{self.company}'. Please check the ticker symbol.")
        
        # Validate and store data
        if self.predict_col not in df.columns:
            available = ', '.join(df.columns)
            raise ValueError(f"Column '{self.predict_col}' not found. Available: {available}")
            
        self.data = df[self.predict_col].dropna()
        
        print(f"\nLoaded {len(self.data)} trading days of {self.predict_col} data")
        print(f"Date range: {self.data.index[0].date()} - {self.data.index[-1].date()}")
    
    def _make_stationary(self, max_diff=3):
        """Find optimal differencing order using ADF test"""
        current = np.log(self.data)
        for d in range(max_diff+1):
            result = adfuller(current.dropna())
            if result[1] < 0.05:
                print(f"Stationary at d={d} (p={result[1]:.4f})")
                return current, d
            current = current.diff().dropna()
        raise ValueError(f"Not stationary after {max_diff} diffs")
    
    def _find_best_arima(self, p_range, q_range):
        """Grid search for best ARIMA parameters"""
        log_series, d = self._make_stationary()
        best_aic = np.inf
        best_model = None
        
        for p in p_range:
            for q in q_range:
                try:
                    model = ARIMA(log_series, order=(p, d, q))
                    results = model.fit()
                    if results.aic < best_aic:
                        best_aic = results.aic
                        best_model = results
                        print(f"New best: ARIMA({p},{d},{q}) AIC:{results.aic:.1f}")
                except Exception as e:
                    print(f"Skipping ARIMA({p},{d},{q}): {str(e)}")
                    continue
                    
        if not best_model:
            raise ValueError("No valid ARIMA model found")
            
        self.model = best_model
        return (p, d, q)
    
    def forecast(self, days=30, p_range=range(0,3), q_range=range(0,3)):
        """Generate business day forecast with confidence intervals"""
        # Find and fit best model
        order = self._find_best_arima(p_range, q_range)
        
        # Generate predictions
        forecast = self.model.get_forecast(steps=days)
        pred = forecast.predicted_mean
        conf = forecast.conf_int()
        
        # Reverse transformations
        if order[1] > 0:  # Reverse differencing
            last_value = np.log(self.data[-1])
            pred = pred.cumsum() + last_value
            
        pred = np.exp(pred)
        conf = np.exp(conf)
        
        # Create business day dates
        last_date = self.data.index[-1]
        future_dates = pd.date_range(
            start=last_date + pd.offsets.BDay(1),
            periods=days,
            freq='B'
        )
        
        self.forecast_results = pd.DataFrame({
            'Predicted': pred.values,
            'Lower': conf.iloc[:,0],
            'Upper': conf.iloc[:,1]
        }, index=future_dates)
        
        return self.forecast_results
    
    def get_forecast_dict(self):
        """
        Return the forecast results as a dictionary.
        The dictionary keys are the forecasted dates (as strings),
        and the values are dicts with 'Predicted', 'Lower', and 'Upper'.
        """
        if self.forecast_results is None:
            raise ValueError("Run forecast() first")
        
        # Convert index to string for JSON-friendly output
        forecast_dict = {
            str(idx.date()): {
                'Predicted': float(row['Predicted']),
                'Lower': float(row['Lower']),
                'Upper': float(row['Upper'])
            }
            for idx, row in self.forecast_results.iterrows()
        }
        return forecast_dict

 # Example usage remains the same
# if __name__ == "__main__":
#       model = ARIMAModel(company='AAPL')
#       forecast = model.forecast(days=10)
#       print(forecast)
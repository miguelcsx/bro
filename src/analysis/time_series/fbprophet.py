"""
FBProphet Model for forecasting timeseries
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
from src.ingestion.clients.yahoo import YahooFinanceClient

class FBProphetModel:
    """
    Facebook Prophet forecaster
    """
    
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
        
        # Validate and store data
        if self.predict_col not in df.columns:
            available = ', '.join(df.columns)
            raise ValueError(f"Column '{self.predict_col}' not found. Available: {available}")
            
        # Convert to Prophet format and remove timezone
        self.data = df[[self.predict_col]].copy()
        self.data.index = pd.to_datetime(self.data.index).tz_localize(None)  # Remove timezone
        self.data.index.name = 'ds'
        self.data = self.data.rename(columns={self.predict_col: 'y'}).reset_index()
        
        print(f"\nLoaded {len(self.data)} trading days of {self.predict_col} data")
        print(f"Date range: {self.data['ds'].iloc[0].date()} - {self.data['ds'].iloc[-1].date()}")
    
    def _tune_hyperparameters(self, horizon_days):
        """
        hyperparameter tuning using cross-validation
        """
        # Initialize base model with all potential seasonalities
        model = Prophet(
            seasonality_mode='multiplicative',
            daily_seasonality=False,  
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05,
            interval_width=0.95
        )
        
        # custom seasonalities based on forecast horizon
        if horizon_days <= 7:
            model.add_seasonality(name='daily', period=1, fourier_order=5)
        
        if horizon_days > 30:
            model.add_seasonality(name='monthly', period=30.5, fourier_order=7)
        
        if horizon_days > 90:
            model.add_seasonality(name='yearly', period=365.25, fourier_order=10)
        
        # US holidays
        model.add_country_holidays(country_name='US')
        
        return model 

    def _get_prophet_model(self, horizon_days):
        """
        Create and fit Prophet model with appropriate seasonality settings
        """
        model = self._tune_hyperparameters(horizon_days)
        model.fit(self.data)  
        return model

    def forecast(self, days=30):
        """
        Generate business day forecast with confidence intervals
        """
        
        self.model = self._get_prophet_model(days)
        last_date = self.data['ds'].iloc[-1]
        future_dates = pd.date_range(
            start=last_date + pd.offsets.BDay(1),
            periods=days,
            freq='B'
        ).tz_localize(None)  
        
        future = pd.DataFrame({'ds': future_dates})
        
        # forecast
        forecast = self.model.predict(future)
        
        self.forecast_results = forecast.set_index('ds')[['yhat', 'yhat_lower', 'yhat_upper']]
        self.forecast_results = self.forecast_results.rename(columns={
            'yhat': 'Predicted',
            'yhat_lower': 'Lower',
            'yhat_upper': 'Upper'
        })
        
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
    
if __name__ == "__main__":
       model = FBProphetModel(company='AAPL')
       forecast = model.forecast(days=10)
       print(forecast)
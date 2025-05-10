"""
Generalized Autoregressive Conditional Heteroskedasticity (GARCH)
model for measuting volatility in stock market prediction
"""

import os 
import numpy as np
import pandas as pd
import warnings
import matplotlib.pyplot as plt
from arch import arch_model
from datetime import datetime, timedelta
from src.ingestion.clients.yahoo import YahooFinanceClient

warnings.filterwarnings('ignore')

class GARCHModel:
    """
    GARCH volatility forecaster with training/testing visualization
    """
    
    def __init__(self, company, predict_col='Close', years_data=5, client=None):
        self.company = company
        self.predict_col = predict_col
        self.years_data = years_data
        self.client = client or YahooFinanceClient()
        self.model = None
        self.data = None
        self.forecast_results = None
        self.training_results = None
        self._load_data()

    def _generate_filename(self, file_type):
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{self.company}_{self.predict_col}_{file_type}_{date_str}"
    
    def save_forecast(self):
        if self.forecast_results is None:
            raise ValueError("Run forecast() first")
            
        os.makedirs('results', exist_ok=True)
        filename = self._generate_filename('forecast') + '.csv'
        filepath = os.path.join('results', filename)
        self.forecast_results.round(2).to_csv(filepath)
        print(f"Saved forecast to {filepath}")

    def _load_data(self):
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=self.years_data*365)
        
        df = self.client.get_historical_data(
            symbol=self.company,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval='1d'
        )
        
        # Ensure we have a DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        if self.predict_col not in df.columns:
            available = ', '.join(df.columns)
            raise ValueError(f"Column '{self.predict_col}' not found. Available: {available}")
            
        self.data = df[[self.predict_col]].dropna()
        print(f"\nLoaded {len(self.data)} trading days of {self.predict_col} data")
        print(f"Date range: {self.data.index[0].date()} - {self.data.index[-1].date()}")

    def _compute_returns(self):
        """
        Calculate percentage returns
        """
        return 100 * self.data[self.predict_col].pct_change().dropna()

    def _hyperparameter_tuning(self, returns):
        """
        Find optimal GARCH parameters using AIC
        """
        best_aic = np.inf
        best_order = (1, 1)
        
        for p in [1, 2, 3]:
            for q in [1, 2, 3]:
                try:
                    model = arch_model(returns, vol='GARCH', p=p, q=q, dist='normal')
                    res = model.fit(disp='off')
                    if res.aic < best_aic:
                        best_aic = res.aic
                        best_order = (p, q)
                        print(f"New best: GARCH({p},{q}) AIC:{res.aic:.1f}")
                except Exception as e:
                    print(f"Skipping GARCH({p},{q}): {str(e)}")
                    continue
                    
        return best_order

    def forecast(self, days=30):
        """
        Generate volatility forecast with backtesting
        """
        returns = self._compute_returns()
        
        test_size = int(len(returns) * 0.2)
        train_returns = returns[:-test_size]
        test_returns = returns[-test_size:]
        

        p, q = self._hyperparameter_tuning(train_returns)
        
        self.model = arch_model(train_returns, vol='GARCH', p=p, q=q, dist='ged')
        res = self.model.fit(disp='off')
        rolling_predictions = []
        
        for i in range(test_size):
            if i == 0:
                pred = res.forecast(horizon=1).variance.iloc[-1].values[0]
                rolling_predictions.append(pred)
            else:
                model = arch_model(returns[:-(test_size-i)], vol='GARCH', p=p, q=q, dist='normal')
                res = model.fit(disp='off')
                pred = res.forecast(horizon=1).variance.iloc[-1].values[0]
                rolling_predictions.append(pred)
        
        # Convert to annualized volatility
        rolling_predictions = np.sqrt(np.array(rolling_predictions) * 252)
        test_volatility = np.sqrt(test_returns.rolling(30).var().dropna() * 252)
        
        # Store backtest results
        self.training_results = pd.DataFrame({
            'True Volatility': test_volatility,
            'Predicted Volatility': rolling_predictions[-len(test_volatility):]
        }, index=test_returns.index[-len(test_volatility):])
        
        # Generate future forecast
        full_model = arch_model(returns, vol='GARCH', p=p, q=q, dist='normal')
        full_res = full_model.fit(disp='off')
        forecast = full_res.forecast(horizon=days)
        forecast_vol = np.sqrt(forecast.variance.iloc[-1] * 252)
        
        # Create future dates
        last_date = self.data.index[-1]
        future_dates = pd.date_range(
            start=last_date + pd.offsets.BDay(1),
            periods=days,
            freq='B'
        )
        
        self.forecast_results = pd.DataFrame({
            'Volatility': forecast_vol.values,
            'Lower': forecast_vol.values * 0.9,
            'Upper': forecast_vol.values * 1.1
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

if __name__ == "__main__":
       model = GARCHModel(company='AAPL')
       forecast = model.forecast(days=10)
       print(forecast)

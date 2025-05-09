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
    
    def plot(self, show=True):
        """Generate centered volatility plot"""
        if self.forecast_results is None or self.training_results is None:
            raise ValueError("Run forecast() first")

        # Create figure with adjusted size and layout
        fig = plt.figure(figsize=(14, 8))
        
        # Get the model parameters from the specification
        p = self.model.volatility.p
        q = self.model.volatility.q
        
        # Create a single axis that takes up most of the figure with margins
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])  # [left, bottom, width, height]
        
        # Main plot - Historical and forecasted volatility
        returns = self._compute_returns()
        historical_vol = returns.rolling(30).std() * np.sqrt(252)
        
        ax.plot(historical_vol, 
                label='Historical Volatility (30-day)', 
                color='#2c3e50',
                linewidth=2)
        
        # Training vs actual
        ax.plot(self.training_results.index,
                self.training_results['True Volatility'],
                color='#27ae60',
                linewidth=2,
                label='Actual Volatility (Test Set)')
        
        ax.plot(self.training_results.index,
                self.training_results['Predicted Volatility'],
                color='#e74c3c',
                linewidth=2,
                linestyle='--',
                label='Predicted Volatility (Test Set)')
        
        # Future forecast
        ax.plot(self.forecast_results.index,
                self.forecast_results['Volatility'],
                color='#F68E5F',
                linewidth=2,
                marker='*',
                markersize=8,
                label='Forecasted Volatility')
        
        ax.fill_between(self.forecast_results.index,
                        self.forecast_results['Lower'],
                        self.forecast_results['Upper'],
                        color='#3498db',
                        alpha=0.1)
        
        ax.axvline(x=self.training_results.index[0],
                color='#7f8c8d',
                linestyle=':',
                linewidth=1.5,
                alpha=0.7)
        
        ax.axvline(x=self.data.index[-1],
                color='#7f8c8d',
                linestyle=':',
                linewidth=1.5,
                alpha=0.7)
        
        ax.set_title(f"{self.company} Volatility Forecast\nGARCH({p},{q}) Model", 
                    fontsize=16, pad=20)
        ax.set_ylabel("Annualized Volatility (%)", fontsize=12)
        ax.legend(fontsize=10, loc='upper right')
        ax.grid(True, linestyle=':', alpha=0.4)
        
        # Adjust x-axis labels to prevent crowding
        ax.xaxis.set_major_locator(plt.MaxNLocator(10))
        
        # Save plot
        os.makedirs('images', exist_ok=True)
        filename = self._generate_filename('volatility_analysis') + '.png'
        filepath = os.path.join('images', filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()

        return filepath

#
# garch = GARCHVolatility(
#     company='AAPL',
#     predict_col='Close',
#     years_data=10
# )
# vol_forecast = garch.forecast(days=30)
# garch.save_forecast()
# garch.plot()

"""
Kalman Filter Model for stock price forecasting
"""

import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
from pykalman import KalmanFilter
import os
from tqdm import tqdm
from sklearn.metrics import mean_squared_error

from src.ingestion.clients.yahoo import YahooFinanceClient

class KalmanFilterModel:
    """
    Kalman Filter forecaster
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
        
        # Check for empty DataFrame
        if df is None or df.empty:
            raise ValueError(f"No historical data found for symbol '{self.company}'")
            
        if self.predict_col not in df.columns:
            available = ', '.join(df.columns)
            raise ValueError(f"Column '{self.predict_col}' not found. Available: {available}")
            
        self.data = df[[self.predict_col]].dropna()
        print(f"\nLoaded {len(self.data)} trading days of {self.predict_col} data")
        print(f"Date range: {self.data.index[0].date()} - {self.data.index[-1].date()}")

    def _initialize_kalman_filter(self):
        """Initialize Kalman Filter to model returns instead of prices"""
        prices = self.data[self.predict_col]
        returns = prices.pct_change().dropna()
        
        # Estimate parameters from historical returns
        obs_noise = returns.var()
        process_noise = returns.var() * 0.1  # Less noise for predictions
        
        kf = KalmanFilter(
            transition_matrices=[1],
            observation_matrices=[1],
            initial_state_mean=returns.iloc[0] if len(returns) > 0 else 0,
            initial_state_covariance=1,
            observation_covariance=obs_noise,
            transition_covariance=process_noise
        )
        return kf

    def forecast(self, days=30):
        """Forecast future returns and convert back to prices"""
        prices = self.data[self.predict_col]
        returns = prices.pct_change().dropna()
        last_price = prices.iloc[-1]
        
        self.model = self._initialize_kalman_filter()
        
        # Fit to returns
        state_means, state_covs = self.model.filter(returns.values)
        last_return = state_means[-1][0]
        last_cov = state_covs[-1][0][0]
        
        predicted_prices = []
        lower_bounds = []
        upper_bounds = []
        
        current_price = last_price
        
        for _ in range(days):
            # Predict next return
            next_return = last_return
            next_cov = last_cov + self.model.transition_covariance
            
            # Convert to price prediction
            pred_price = current_price * (1 + next_return)
            pred_std = current_price * np.sqrt(next_cov)
            
            predicted_prices.append(pred_price)
            lower_bounds.append(pred_price - 2*pred_std)
            upper_bounds.append(pred_price + 2*pred_std)
            
            # Update for next iteration
            current_price = pred_price
            last_return = next_return
            last_cov = next_cov
        
        # Create output DataFrame
        last_date = self.data.index[-1]
        future_dates = pd.date_range(
            start=last_date + pd.offsets.BDay(1),
            periods=days,
            freq='B'
        )
        
        self.forecast_results = pd.DataFrame({
            'Predicted': predicted_prices,
            'Lower': lower_bounds,
            'Upper': upper_bounds
        }, index=future_dates)
        
        return self.forecast_results

    def show_forecast(self):
        """
        Display the forecast results in a clean tabular format
        """
        if self.forecast_results is None:
            raise ValueError("Run forecast() first")
            
        print(f"\n{'='*50}")
        print(f"{self.company} {self.predict_col} Price Forecast")
        print(f"Kalman Filter Model")
        print(f"Forecast Period: {len(self.forecast_results)} business days")
        print(f"Last Historical Date: {self.data.index[-1].strftime('%Y-%m-%d')}")
        print(f"Last Historical Price: ${self.data[self.predict_col].iloc[-1]:.2f}")
        print('='*50)
        
        # Create a formatted table
        forecast_df = self.forecast_results.copy()
        forecast_df.index = forecast_df.index.strftime('%Y-%m-%d')
        forecast_df['Predicted'] = forecast_df['Predicted'].apply(lambda x: f"${x:.2f}")
        forecast_df['Range'] = forecast_df.apply(
            lambda x: f"${x['Lower']:.2f}-${x['Upper']:.2f}", axis=1
        )
        
        # Print the table with headers
        print("\nDate\t\tPredicted\tConfidence Range")
        print("-"*50)
        for date, row in forecast_df.iterrows():
            print(f"{date}\t{row['Predicted']}\t{row['Range']}")
        
        print('='*50)
        print(f"Note: Confidence range represents ±2 standard deviations\n")

    def plot(self, show=True):
        """Generate and save forecast plot"""
        if self.forecast_results is None:
            raise ValueError("Run forecast() first")

        # First show the numerical forecast
        self.show_forecast()

        plt.figure(figsize=(14, 7))
        plt.plot(self.data.index, self.data[self.predict_col], label='Historical Prices')
        plt.plot(self.forecast_results.index, self.forecast_results['Predicted'], 
                label='Kalman Filter Forecast', color='orange')
        plt.fill_between(
            self.forecast_results.index,
            self.forecast_results['Lower'],
            self.forecast_results['Upper'],
            color='orange', alpha=0.2
        )
        
        plt.title(f'{self.company} {self.predict_col} Price Forecast with Kalman Filter')
        plt.xlabel('Date')
        plt.ylabel('Price ($)')
        plt.legend()
        plt.grid(True)
        
        # Save the plot
        os.makedirs('plots', exist_ok=True)
        filename = self._generate_filename('forecast_plot') + '.png'
        filepath = os.path.join('plots', filename)
        plt.savefig(filepath)
        
        if show:
            plt.show()
        else:
            plt.close()
            
        print(f"Saved forecast plot to {filepath}")

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

    def evaluate_model(self):
        """
        Evaluate the Kalman Filter model on historical data
        Returns error metrics
        """
        prices = self.data[self.predict_col]
        
        # Run Kalman Filter on full dataset
        state_means, _ = self._initialize_kalman_filter().filter(prices.values)
        kalman_estimates = pd.Series(state_means.flatten(), index=prices.index)
        
        # Calculate error metrics
        mse = mean_squared_error(prices, kalman_estimates)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(prices - kalman_estimates))
        percentage_error = np.mean(np.abs(prices - kalman_estimates)/prices) * 100
        
        return {
            'MSE': mse,
            'RMSE': rmse,
            'MAE': mae,
            'Mean Percentage Error': percentage_error
        }

# # Example usage
# if __name__ == "__main__":
#      model = KalmanFilterModel(company='AAPL', years_data=2)
#      forecast = model.forecast(days=10)
#      print(forecast)
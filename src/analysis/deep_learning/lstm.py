"""
LSTM (Long-Short Term Memory) model for time series forecasting.
Simplified implementation with essential features for stock price prediction.
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from math import ceil
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')
from datetime import datetime, timedelta
import os

from src.ingestion.clients.yahoo import YahooFinanceClient


class LSTMModel:
    """
    LSTM forecaster using YahooFinanceClient for data access
    """

    def __init__(self, company, predict_col="Close", years_data=5, client=None,
                 lookback=30, hidden_size=50, num_layers=2, 
                 epochs=15, batch_size=16, learning_rate=0.001):
        self.lookback = lookback
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.company = company
        self.predict_col = predict_col
        self.years_data = years_data
        self.client = client or YahooFinanceClient()
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
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
            
        self.data = df[self.predict_col].dropna()
        
        print(f"\nLoaded {len(self.data)} trading days of {self.predict_col} data")
        print(f"Date range: {self.data.index[0].date()} - {self.data.index[-1].date()}")

    def _prepare_data(self):
        """
        prepare data for lstm prediction
        """
        data_values = self.data.values.reshape(-1, 1)
        scaled_data = self.scaler.fit_transform(data_values)
    
        # sequences
        def create_sequences(data, lookback):
            x, y = [], []
            for i in range(lookback, len(data)):
                x.append(data[i-lookback:i, 0])
                y.append(data[i, 0])
            return np.array(x), np.array(y)

        x, y = create_sequences(scaled_data, self.lookback)
        x = torch.FloatTensor(x).unsqueeze(2).to(self.device)
        y = torch.FloatTensor(y).to(self.device)

        return x, y
    
    def _train_model(self, x_train, y_train):
        model = LSTMNetwork(
        input_size=1,
        hidden_size=self.hidden_size,
        num_layers=self.num_layers
    ).to(self.device)
        
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=self.learning_rate)

        model.train()
        for epoch in range(self.epochs):
            for i in range(0, len(x_train), self.batch_size):
                inputs = x_train[i:i + self.batch_size].to(self.device)
                labels = y_train[i:i + self.batch_size].to(self.device)
                
                optimizer.zero_grad()
                outputs = model(inputs)
                loss = criterion(outputs.squeeze(), labels)
                loss.backward()
                optimizer.step()
            
            if (epoch+1) % 5 == 0:
                print(f'Epoch {epoch+1}/{self.epochs}, Loss: {loss.item():.6f}')
        
        return model

    def forecast(self, days=30):
        """
        generate bussiness day forecast with confidence intervals
        """

        x, y = self._prepare_data()
        self.model = self._train_model(x, y)

        # evaluate modelll
        self.model.eval()
        with torch.no_grad():


            # starts with the last lookback days of actual data
            last_sequence = self.data.values[-self.lookback:].reshape(-1, 1) 
            scaled_sequence = self.scaler.transform(last_sequence)
            
            predictions = []
            lower_bounds = []
            upper_bounds = []
            
            current_sequence = torch.FloatTensor(scaled_sequence[:, 0]).unsqueeze(0).unsqueeze(2).to(self.device)
            
            for _ in range(days):
                pred = self.model(current_sequence).cpu().numpy()[0, 0]
                predictions.append(pred)
                
                # confidence intervals
                lower_bounds.append(pred * 0.98)  # 2% below
                upper_bounds.append(pred * 1.02)  # 2% above
                
                # update sequence for next prediction
                new_sequence = torch.cat([
                    current_sequence[0, 1:, :],
                    torch.FloatTensor([[pred]]).to(self.device)
                ]).unsqueeze(0)
                current_sequence = new_sequence
            
            # inverse transform predictions
            predictions = np.array(predictions).reshape(-1, 1)
            predictions = self.scaler.inverse_transform(predictions)
            
            lower_bounds = np.array(lower_bounds).reshape(-1, 1)
            lower_bounds = self.scaler.inverse_transform(lower_bounds)
            
            upper_bounds = np.array(upper_bounds).reshape(-1, 1)
            upper_bounds = self.scaler.inverse_transform(upper_bounds)
        
        # Create business day dates
        last_date = self.data.index[-1]
        future_dates = pd.date_range(
            start=last_date + pd.offsets.BDay(1),
            periods=days,
            freq='B'
        )
        
        self.forecast_results = pd.DataFrame({
            'Predicted': predictions.flatten(),
            'Lower': lower_bounds.flatten(),
            'Upper': upper_bounds.flatten()
        }, index=future_dates)
        
        return self.forecast_results

    def plot(self, show=True):
        """
        generate and save forecast plot
        """
        if self.forecast_results is None:
            raise ValueError("Run forecast() first")

        plt.figure(figsize=(14, 7))
        
        # Historical data - more prominent
        plt.plot(self.data, 
                label='Historical', 
                color='#2c3e50',  # Dark blue-gray
                linewidth=2.5,
                alpha=0.9)
        
        # Forecast line - lighter and more subtle
        plt.plot(self.forecast_results.index, 
                self.forecast_results['Predicted'],
                color='#e74c3c',  # Lighter red
                linestyle='-',    # Solid but thin
                linewidth=1.5,
                alpha=0.7,
                marker='',        # Remove markers
                label=f'{len(self.forecast_results)}-Day Forecast')
        
        # Confidence interval - very subtle
        plt.fill_between(self.forecast_results.index,
                        self.forecast_results['Lower'],
                        self.forecast_results['Upper'],
                        color='#f39c12',  # Orange shade
                        alpha=0.15,       # More transparent
                        linewidth=0)      # No border
        
        # Forecast start indicator
        plt.axvline(x=self.data.index[-1],
                color='#7f8c8d',      # Gray
                linestyle=':',
                linewidth=1.5,
                alpha=0.7)
        
        # Formatting
        plt.title(f"{self.company} {self.predict_col} Forecast\nLSTM Model",
                fontsize=14, pad=20)
        plt.xlabel("Date", fontsize=12)
        plt.ylabel(f"{self.predict_col} Price ($)", fontsize=12)
        
        # Legend with subtle frame
        legend = plt.legend(frameon=True)
        frame = legend.get_frame()
        frame.set_facecolor('white')
        frame.set_alpha(0.8)
        frame.set_edgecolor('#bdc3c7')
        
        # Grid lines
        plt.grid(True, 
                linestyle=':', 
                alpha=0.4,
                color='#95a5a6')
        
        # Save plot
        filename = self._generate_filename('forecast') + '.png'
        filepath = os.path.join('images', filename)
        plt.savefig(filepath, 
                dpi=300, 
                bbox_inches='tight',
                facecolor='white')  # White background
        
        if show:
            plt.show()
        else:
            plt.close()

        return filepath


class LSTMNetwork(nn.Module):
    """
    class for lstm typical architecture implemented with pytorch
    """

    def __init__(self, input_size=1, hidden_size=50, num_layers=2, output_size=1):
        super(LSTMNetwork, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
    
    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out
    

# if __name__ == "__main__":
#     # Example usage
#     lstm = LSTMModel(
#         company='GOOG',
#         predict_col='Close',
#     )

#     # Get 2-day forecast
#     forecast = lstm.forecast(days=2)
    
#     # Print numerical predictions
#     print("\n2-Day Forecast:")
#     print(forecast[['Predicted', 'Lower', 'Upper']].round(2))
    
#     # Save and plot (optional)
#     lstm.save_forecast()
#     lstm.plot()

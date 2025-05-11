"""
Relative Strength Index (RSI) Analyzer
Measures overbought/oversold conditions with actionable insights
"""

import os
import numpy as np
import pandas as pd
import warnings
from datetime import datetime, timedelta
from typing import Tuple
from src.ingestion.clients.yahoo import YahooFinanceClient

warnings.filterwarnings('ignore')

class RSIModel:
    """
    RSI analyzer with historical context and actionable recommendations
    """
    
    def __init__(self, company, window=14, overbought=70, oversold=30, 
                 years_data=2, client=None):
        self.company = company
        self.window = window
        self.overbought = overbought
        self.oversold = oversold
        self.years_data = years_data
        self.client = client or YahooFinanceClient()
        self.data = None
        self.current_rsi = None
        self.status = None
        self._load_data()

    def _generate_filename(self, file_type):
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{self.company}_RSI_{file_type}_{date_str}"
    
    def save_analysis(self, df=None):
        """Save analysis results to CSV"""
        if not hasattr(self, 'analysis_results'):
            raise ValueError("Run analyze() first")
            
        os.makedirs('results', exist_ok=True)
        filename = self._generate_filename('analysis') + '.csv'
        filepath = os.path.join('results', filename)
        
        # Save either the provided DataFrame or create one from analysis_results
        if df is not None:
            df.to_csv(filepath)
        else:
            pd.DataFrame([self.analysis_results]).to_csv(filepath)
            
        print(f"Saved RSI analysis to {filepath}")

    def _load_data(self):
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=self.years_data*365)
        
        df = self.client.get_historical_data(
            symbol=self.company,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval='1d'
        )
        
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
            
        if 'Close' not in df.columns:
            available = ', '.join(df.columns)
            raise ValueError(f"'Close' column not found. Available: {available}")
            
        self.data = df[['Close']].dropna()
        print(f"\nLoaded {len(self.data)} trading days of data")
        print(f"Date range: {self.data.index[0].date()} - {self.data.index[-1].date()}")

    def _calculate_rsi(self) -> pd.Series:
        """Core RSI calculation with EMA smoothing"""
        delta = self.data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Use EMA for smoothing (standard in most platforms)
        avg_gain = gain.ewm(alpha=1/self.window, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/self.window, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def analyze(self) -> dict:
        """
        Perform complete RSI analysis with historical context
        """
        #  RSI
        self.data['RSI'] = self._calculate_rsi()
        self.current_rsi = self.data['RSI'].iloc[-1]
        
        # status
        if self.current_rsi >= self.overbought:
            self.status = "overbought"
            action = "Consider taking profits or waiting for pullback"
            confidence = "strong" if self.current_rsi > 80 else "moderate"
        elif self.current_rsi <= self.oversold:
            self.status = "oversold"
            action = "Potential buying opportunity (watch for confirmation)"
            confidence = "strong" if self.current_rsi < 20 else "moderate"
        else:
            self.status = "neutral"
            action = "No strong signal - monitor trend"
            confidence = "low"
        
        # Historical context
        historical_rsi = self.data['RSI'].dropna()
        days_overbought = len(historical_rsi[historical_rsi >= self.overbought])
        days_oversold = len(historical_rsi[historical_rsi <= self.oversold])
        
        # Recent values (last 10 trading days)
        recent_data = self.data.tail(10)
        recent_values = [{
            'date': str(idx.date()),
            'close': float(row['Close']),
            'rsi': float(row['RSI']) if pd.notna(row['RSI']) else None
        } for idx, row in recent_data.iterrows()]
        
        
        self.analysis_results = {
            'current_rsi': float(self.current_rsi),
            'status': self.status,
            'action': action,
            'confidence': confidence,
            'historical_context': {
                'days_overbought': days_overbought,
                'days_oversold': days_oversold,
                'avg_rsi': float(historical_rsi.mean()),
                'max_rsi': float(historical_rsi.max()),
                'min_rsi': float(historical_rsi.min())
            },
            'recent_values': recent_values
        }
        
        
        df = pd.DataFrame({
            'Metric': [
                'Current RSI', 'Status', 'Action', 'Confidence',
                'Days Overbought', 'Days Oversold', 
                'Average RSI', 'Max RSI', 'Min RSI'
            ],
            'Value': [
                self.current_rsi, self.status, action, confidence,
                days_overbought, days_oversold,
                historical_rsi.mean(), historical_rsi.max(), historical_rsi.min()
            ]
        })
        
        
        self.save_analysis(df)
        
        return self.analysis_results
    
    def get_analysis_dict(self):
        """
        Return the analysis results
        """
        if not hasattr(self, 'analysis_results'):
            self.analyze()
        
        return self.analysis_results

# Example usage
# if __name__ == "__main__":
#      rsi = RSIModel(company='AAPL', years_data=2)
#      analysis = rsi.analyze()
#      print(analysis)
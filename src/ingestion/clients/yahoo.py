"""
Yahoo Finance API client for fetching stock data.
"""

import yfinance as yf
import pandas as pd
from typing import Optional, Union, List, Dict, Any

class YahooFinanceClient:
    """Client for interacting with Yahoo Finance API."""
    
    def __init__(self):
        """Initialize Yahoo Finance client."""
        pass
    
    def get_ticker_data(self, symbol: str) -> yf.Ticker:
        """
        Get a Ticker object for the given symbol.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
            
        Returns:
            yf.Ticker object for the specified symbol
        """
        return yf.Ticker(symbol)
    
    def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get current stock quote for the given symbol.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
            
        Returns:
            Dictionary containing current stock information
        """
        ticker = self.get_ticker_data(symbol)
        return ticker.info
    
    def get_historical_data(self, symbol: str, period: str = "1y", 
                           interval: str = "1d", start: Optional[str] = None,
                           end: Optional[str] = None) -> pd.DataFrame:
        ticker = yf.Ticker(symbol)
        
        if start and end:
            df = ticker.history(start=start, end=end, interval=interval)
        else:
            df = ticker.history(period=period, interval=interval)
            
        # Set business day frequency and fill missing dates
        return df.asfreq('B', method='ffill').dropna(subset=['Close'])
    
    def get_multiple_tickers_data(self, symbols: List[str], period: str = "1d") -> pd.DataFrame:
        """
        Get data for multiple ticker symbols.
        
        Args:
            symbols: List of stock ticker symbols (e.g., ['AAPL', 'MSFT'])
            period: Data period (valid values: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            
        Returns:
            DataFrame containing data for all the specified symbols
        """
        return yf.download(
            tickers=" ".join(symbols),
            period=period,
            group_by='ticker'
        )

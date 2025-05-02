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
    
    def get_historical_data(
        self, 
        symbol: str, 
        period: str = "1mo", 
        interval: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical market data for the given symbol.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
            period: Data period (valid values: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval: Data interval (valid values: '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
            start: Start date in 'YYYY-MM-DD' format (if provided, period will be ignored)
            end: End date in 'YYYY-MM-DD' format (if provided, period will be ignored)
            
        Returns:
            DataFrame containing historical stock data
        """
        ticker = self.get_ticker_data(symbol)
        
        if start and end:
            return ticker.history(start=start, end=end, interval=interval)
        else:
            return ticker.history(period=period, interval=interval)
    
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

"""
Yahoo Finance API client for fetching stock data.
"""

from datetime import datetime
import yfinance as yf
import pandas as pd
from typing import Optional, Union, List, Dict, Any

from curl_cffi.requests.exceptions import HTTPError

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
        try:
            # For Facebook, we need to use META now
            if symbol.upper() in ["FB", "FACEBOOK"]:
                symbol = "META"
                
            # For simple tickers like Apple, Microsoft etc.
            ticker = self.get_ticker_data(symbol)
            info = ticker.info
            
            # If we get a NONE quote type, it means the symbol wasn't found
            if info.get('quoteType') == 'NONE' or not info:
                # Try common alternatives
                alternatives = {
                    "GOOGLE": "GOOGL",
                    "ALPHABET": "GOOGL",
                    "AMAZON": "AMZN",
                    "TESLA": "TSLA",
                    "MICROSOFT": "MSFT",
                    "APPLE": "AAPL",
                    "NETFLIX": "NFLX",
                    "FACEBOOK": "META",
                    "META PLATFORMS": "META",
                    "FB": "META"
                }
                
                # Check if we have an alternative
                alt_symbol = alternatives.get(symbol.upper())
                if alt_symbol:
                    ticker = self.get_ticker_data(alt_symbol)
                    info = ticker.info
                    if info and info.get('quoteType') != 'NONE':
                        print(f"[YahooFinanceClient] Using alternative symbol {alt_symbol} for {symbol}")
                        return info
            
            # If we got a valid result, return it
            if info and info.get('quoteType') != 'NONE':
                return info
                
            # If nothing worked, return a default structure with enough fields for the frontend
            print(f"[YahooFinanceClient] Symbol not found: {symbol}")
            return {
                "symbol": symbol,
                "quoteType": "EQUITY",
                "shortName": f"{symbol} (Not Found)",
                "longName": f"{symbol} (Not Found)",
                "regularMarketPrice": 0,
                "currentPrice": 0,
                "regularMarketChange": 0,
                "regularMarketChangePercent": 0,
                "marketState": "CLOSED",
                "currency": "USD",
                "previousClose": 0,
                "open": 0,
                "dayLow": 0,
                "dayHigh": 0,
                "volume": 0,
                "averageVolume": 0,
                "fiftyTwoWeekLow": 0,
                "fiftyTwoWeekHigh": 0,
                "sector": "Unknown",
                "industry": "Unknown",
                "country": "Unknown",
                "fullTimeEmployees": 0,
                "website": "",
                "longBusinessSummary": f"Information for {symbol} is not available."
            }
            
        except HTTPError as e:
            if "404" in str(e):
                print(f"[YahooFinanceClient] Symbol not found: {symbol}")
            else:
                print(f"[YahooFinanceClient] HTTP error fetching quote for {symbol}: {e}")
            # Return default data instead of empty dict
            return {
                "symbol": symbol,
                "quoteType": "EQUITY",
                "shortName": f"{symbol} (Not Found)",
                "longName": f"{symbol} (Not Found)",
                "regularMarketPrice": 0,
                "currentPrice": 0,
                "regularMarketChange": 0,
                "regularMarketChangePercent": 0,
                "marketState": "CLOSED"
            }
        except Exception as e:
            print(f"[YahooFinanceClient] Error fetching quote for {symbol}: {e}")
            return {
                "symbol": symbol,
                "quoteType": "EQUITY",
                "shortName": f"{symbol} (Error)",
                "longName": f"{symbol} (Error)",
                "regularMarketPrice": 0,
                "currentPrice": 0,
                "regularMarketChange": 0,
                "regularMarketChangePercent": 0,
                "marketState": "CLOSED"
            }

    def get_historical_data(self, symbol: str, period: str = "1y", 
                           interval: str = "1d", start: Optional[str] = None,
                           end: Optional[str] = None) -> pd.DataFrame:
        try:
            ticker = yf.Ticker(symbol)
            if start and end:
                df = ticker.history(start=start, end=end, interval=interval)
            else:
                df = ticker.history(period=period, interval=interval)
            
            # Verificar si el DataFrame está vacío o no tiene datos de cierre
            if df.empty or 'Close' not in df.columns:
                print(f"[YahooFinanceClient] No historical data available for: {symbol}")
                return pd.DataFrame()
                
            # Set business day frequency and fill missing dates
            return df.asfreq('B', method='ffill').dropna(subset=['Close'])
        except HTTPError as e:
            if "404" in str(e):
                print(f"[YahooFinanceClient] Historical data not found for symbol: {symbol}")
                return pd.DataFrame()
            else:
                print(f"[YahooFinanceClient] HTTP error fetching historical data for {symbol}: {e}")
                return pd.DataFrame()
        except Exception as e:
            print(f"[YahooFinanceClient] Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
    
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

    def get_news(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get latest news for a given symbol.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')

        Returns:
            List of dictionaries containing formatted news information with
            title, source, date, summary and url
        """
        try:
            raw_news = yf.Ticker(symbol).news
            formatted_news = []
            
            for item in raw_news:
                # Extract and format required fields with null checks
                news_item = {
                    "title": item.get("title", ""),
                    "source": item.get("publisher", [{}])[0].get("name", "Unknown"),
                    "date": item.get("pubDate", "").split("T")[0] if item.get("pubDate") else '1970-01-01',  # Fallback date
                    "summary": item.get("summary", ""),
                    "url": item.get("link", "")
                }
                formatted_news.append(news_item)
            
            # Safe sorting with date validation
            def safe_sort_key(item):
                try:
                    return datetime.fromisoformat(item["date"])
                except ValueError:
                    return datetime.min
                
            formatted_news.sort(
                key=safe_sort_key,
                reverse=True
            )
            
            return formatted_news
            
        except Exception as e:
            print(f"[YahooFinanceClient] Error fetching news for {symbol}: {e}")
            return []

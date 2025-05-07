"""
Tralalelo tralala
"""

from typing import List
from mcp.types import TextContent
from pydantic import Field
from src.mcp.server import mcp_server
from src.ingestion.clients import yahoo_client
from datetime import datetime


@mcp_server.tool()
def get_ticker_data(symbol: str) -> TextContent:
    """
    Get ticker data for a given symbol
    """
    return yahoo_client.get_ticker_data(symbol)


@mcp_server.tool()
def get_stock_quote(symbol: str) -> TextContent:
    """
    Get stock quote for a given symbol
    """
    return yahoo_client.get_stock_quote(symbol)


@mcp_server.tool()
def get_historical_data(symbol: str, period: str = "1y", interval: str = "1d") -> TextContent:
    """
    Get historical data for a given symbol
    """
    return yahoo_client.get_historical_data(symbol, period, interval)


@mcp_server.tool()
def get_multiple_tickers_data(symbols: List[str], period: str = "1d") -> TextContent:
    """
    Get multiple tickers data for a given list of symbols
    """
    return yahoo_client.get_multiple_tickers_data(symbols, period)


@mcp_server.tool()
def get_today_date() -> TextContent:
    """
    Get today's date
    """
    return datetime.now().strftime("%Y-%m-%d")


@mcp_server.tool()
def get_current_time() -> TextContent:
    """
    Get current time
    """
    return datetime.now().strftime("%H:%M:%S")


@mcp_server.tool()
def get_current_date() -> TextContent:
    """
    Get current date
    """
    return datetime.now().strftime("%Y-%m-%d")

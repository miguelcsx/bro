"""
MCP Server
"""


from mcp.server.fastmcp import FastMCP

mcp_server = FastMCP(
    name="Bro",
)

from src.mcp.tools.probabilistic_tools import arima_forecast

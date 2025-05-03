"""
MCP Server
"""


from mcp.server.fastmcp import FastMCP

mcp_server = FastMCP(
    name="Bro",
)

from  src.mcp.tools.probabilistic_tools import (
    arima_forecast,
    hmm_forescast
)

from src.mcp.tools.deep_learning_tools import (
    lstm_forecast,
)

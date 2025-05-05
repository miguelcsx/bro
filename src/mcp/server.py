"""
MCP Server
"""


from mcp.server.fastmcp import FastMCP

mcp_server = FastMCP(
    name="Bro",
)

import src.mcp.tools.time_series_tools
import src.mcp.tools.probabilistic_tools 
import src.mcp.tools.deep_learning_tools

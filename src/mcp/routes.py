"""
MCP Server routes
"""

from starlette.routing import Mount, Route, Host
from mcp.server.sse import SseServerTransport
from src.mcp.server import mcp_server

sse = SseServerTransport("/messages/")


async def handle_sse(request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as (
        read_stream,
        write_stream,
    ):
        await mcp_server._mcp_server.run(
            read_stream,
            write_stream,
            mcp_server._mcp_server.create_initialization_options()
        )

routes = [
    Route("/sse", handle_sse),
    Mount(
        "/messages/",
        app=sse.handle_post_message
    ),
]

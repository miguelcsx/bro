

from starlette.applications import Starlette
from starlette.routing import Mount, Route, Host
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from src.mcp.server import mcp_server
from src.mcp.routes import routes


middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

mcp_app = mcp_server.sse_app()


app = Starlette(
    debug=True,
    middleware=middleware,
    routes=routes,
)

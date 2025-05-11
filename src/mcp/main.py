"""
MCP Server 
"""

import uvicorn

from src.mcp.mount import app

def main():
    uvicorn.run(
        "src.mcp.main:app",
        host="localhost",
        port=5555,
        reload=False
    )

if __name__ == "__main__":
    main()

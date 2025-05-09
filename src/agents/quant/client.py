"""
MCP Client for Multi-Server
"""

from langchain_mcp_adapters.client import MultiServerMCPClient
from typing import List

# Configurar el cliente con más opciones
client = MultiServerMCPClient({
    "forecasting": {
        "url": "http://localhost:5555/sse",
        "transport": "sse",
        "timeout": 30,  # Aumentar timeout
        "retries": 3    # Añadir reintentos
    },
})

# Verificar las herramientas disponibles
tools = client.get_tools()
print(f"Herramientas disponibles: {[tool.name for tool in tools]}")  # Debug

# Exportar herramientas
__all__ = ["tools"]

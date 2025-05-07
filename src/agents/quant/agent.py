from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from src.utils import settings
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool, tool

"""
MCP Client for Multi-Server
"""

from langchain_mcp_adapters.client import MultiServerMCPClient
from typing import List, Dict, Any, Callable, Awaitable, Optional, Tuple


class ClientContextManager:
    def __init__(self, client, agent):
        self.client = client
        self.agent = agent

    async def __aenter__(self):
        await self.client.__aenter__()
        return self.client, self.agent

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)


async def create_agent_client() -> ClientContextManager:
    """Create and return the MCP client and agent for API use"""
    
    # Create the client that will be used
    client = MultiServerMCPClient({
        "forecasting": {
            "url": "http://localhost:5555/sse",
            "transport": "sse", 
            "timeout": 30,
            "retries": 3
        },
    })
    
    # Create a placeholder for the agent that we'll fill after entering the context
    agent = None
    
    # Return a modified context manager that initializes the agent on enter
    class EnhancedClientContextManager:
        def __init__(self, client):
            self.client = client
            self.agent = None

        async def __aenter__(self):
            # Enter the client context first
            await self.client.__aenter__()
            
            # Get tools after entering the context
            tools = self.client.get_tools()
            print(f"Available tools: {[t.name for t in tools]}")  # Debug
            
            # Create the model and agent
            model = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0,
                google_api_key=settings.GEMINI_API_KEY,
            )
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """
                    You are a quantitative financial agent. When using tools, you MUST follow these rules:

                    1. Core Behaviors:
                    - Provide direct, concise responses focused on financial analysis
                    - Respond with either tool outputs or natural language explanations
                    - Never include extraneous commentary or code

                    2. Analysis Approach:
                    - For current market data: Retrieve real-time quotes and prices
                    - For predictions: Analyze data patterns to select appropriate model:
                      - Standard market behavior: Use statistical forecasting
                      - Complex long-term trends: Use deep learning
                      - Cyclical patterns: Use time series analysis  
                      - Market regime shifts: Use state-based modeling

                    3. Response Style:
                    - Be precise and quantitative
                    - Focus on the specific financial metrics requested
                    - Provide context only when directly relevant
                    - Default to standard timeframes and metrics unless specified

                    4. Query Handling:
                    - Break complex requests into logical steps
                    - Establish temporal context when needed
                    - Focus on actionable financial insights
                    - Maintain consistency in data presentation

                    5. Output Format:
                    - Present results clearly and directly
                    - Include only relevant numerical data
                    - Format responses consistently
                    - Avoid technical jargon unless necessary

                    You should focus on providing accurate financial analysis while maintaining clear and direct communication.
            """),
                MessagesPlaceholder(variable_name="messages")
            ])
            
            # Create the agent with the tools from the active client
            self.agent = create_react_agent(
                model=model,
                tools=tools,
                prompt=prompt,
            )
            
            return self.client, self.agent

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    return EnhancedClientContextManager(client)


async def main():
    
    client, agent = await create_agent_client()
    
    try:
        query = input("Enter your query: ")
        response = await agent.ainvoke({
            "messages": [HumanMessage(content=query)],
        })
        
        if isinstance(response, dict) and "output" in response:
            print(response["output"])
        elif hasattr(response, 'content'):
            print(response.content)
        else:
            print(response)
    finally:
        # Make sure to close the client when done
        await client.__aexit__(None, None, None)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

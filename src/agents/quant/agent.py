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
from typing import List, Dict, Any, Callable, Awaitable, Optional

async def main():

    async with MultiServerMCPClient({
    "forecasting": {
        "url": "http://localhost:5555/sse",
        "transport": "sse",
        "timeout": 30,  # Increase timeout
        "retries": 3    # Add retries
    },
    }) as client:
        # Verify available tools
        tools = client.get_tools()
        print(f"Available tools: {[t.name for t in tools]}")  # Debug
        
        # Define the language model
        model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            google_api_key=settings.GEMINI_API_KEY,
        )

        # Create a more specific prompt that encourages tool usage
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
        You are a quantitative agent specialized in financial trading with access to tools such as prediction models (LSTM, ARIMA, etc.).

        Your goal is to respond directly and efficiently to user questions. If the user requests a forecast (for example, of a stock's opening price), you should:

        1. Choose the LSTM model by default if no other is specified.
        2. Assume the user wants a prediction for the next business day if no date is specified.
        3. Use two years of historical data by default.
        4. Execute the tool directly without asking additional technical questions.
        5. Include in your response the model's result and the name of the model used.

        Do not ask for parameters if you can reasonably assume them.
            """),
            MessagesPlaceholder(variable_name="messages")
        ])

        # Create agent with ReAct framework
        agent = create_react_agent(
            model=model,
            tools=tools,
            prompt=prompt,
        )
        
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


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

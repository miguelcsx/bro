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
            
            # Add debug tool for testing
            @tool
            def debug_info(message: str) -> str:
                """Use this tool to log debug information during processing"""
                print(f"[DEBUG] {message}")
                return f"Logged: {message}"
            
            # Create the model and agent
            model = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0,
                google_api_key=settings.GEMINI_API_KEY,
            )
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """
                 
You are a financial analyst, you are given a query and you need to answer it using the available tools, you need to return a json with the response.


Available tools and how to use them:

- get_ticker_data(symbol: str): Get general ticker data for the provided symbol.
- get_stock_quote(symbol: str): Get the current stock quote for the provided symbol.
- get_historical_data(symbol: str, period: str = '1y', interval: str = '1d'): Get historical data for the symbol, with optional period and interval.
- get_multiple_tickers_data(symbols: List[str], period: str = '1d'): Get data for multiple symbols for the given period.
- get_today_date(): Returns today's date.
- get_current_time(): Returns the current time.
- get_current_date(): Returns the current date.
- get_stock_news(symbol: str): Get recent news for the provided symbol.

Probabilistic forecasting tools:
- arima_forecast(company: str, predict_col: str, years_data: int, future_days: int): Forecast using ARIMA for the given company and column, with years of historical data and days into the future.
- hmm_forecast(company: str, predict_col: str, years_data: int, future_days: int): Forecast using a Hidden Markov Model.
- kalman_forecast(company: str, predict_col: str, years_data: int, future_days: int): Forecast using a Kalman Filter.

Time series forecasting tools:
- fbprophet_forecast(company: str, predict_col: str, years_data: int, future_days: int): Forecast using Facebook Prophet.

Deep learning tools:
- lstm_forecast(company: str, predict_col: str, years_data: int, future_days: int): Forecast using an LSTM model.

Machine learning tools:
- ml_direction_forecast(company: str, years_data: int, prediction_days: int): Predicts the probability of the stock going up or down using model consensus.

Volatility tools:
- garch_volatility(company: str, predict_col: str, years_data: int, future_days: int): Volatility forecast using GARCH.
- xgboost_volatility(company: str, predict_col: str, years_data: int, future_days: int): Volatility forecast using XGBoost.
- rsi_analyzer(company: str, window: int = 14, years_data: int = 2, overbought: int = 70, oversold: int = 30): Analyzes the Relative Strength Index (RSI) and provides historical context and recommendations.

Desired output format:
{{
  "message": "Stock analysis completed.",
  "stock_quote": {{}},
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "price": 152.0,
  "currency": "USD",
  "change": 2.0,
  "changePercent": 1.33,
  "marketState": "REGULAR",
  "details": {{
    "previousClose": 150.0,
    "open": 152.0,
    "dayLow": 151.0,
    "dayHigh": 155.0,
    "volume": 1000000,
    "averageVolume": 1200000,
    "fiftyTwoWeekLow": 130.0,
    "fiftyTwoWeekHigh": 160.0
  }},
  "company": {{
    "sector": "Technology",
    "industry": "Software",
    "country": "USA",
    "employees": 5000,
    "website": "https://example.com",
    "summary": "A leading tech company."
  }},
  "predictions": [
    {{
      "date": "2024-12-31",
      "predicted": 170.0,
      "lower": 165.0,
      "upper": 175.0
    }}
  ],
  "historical_data": [
    {{
      "date": "2024-01-01",
      "price": 140.0
    }}
  ],
  "news": [
    {{
      "title": "Tech Company Reports Record Earnings",
      "source": "Financial Times",
      "date": "2024-05-10",
      "summary": "The company reported a 20% increase in revenue.",
      "url": "https://example.com/news"
    }}
  ]
}}
"""),
                MessagesPlaceholder(variable_name="messages")
            ])
            
            # Combine MCP tools with our custom tools
            all_tools = tools + [debug_info]
            
            # Create the agent with the tools from the active client
            self.agent = create_react_agent(
                model=model,
                tools=all_tools,
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

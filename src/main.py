from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import uvicorn
import json
import re
from pydantic import BaseModel
from datetime import datetime
from src.agents.quant.agent import main as agent_main
from typing import Dict, List, Any, Optional
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Add CORS middleware to allow requests from our Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory="images"), name="images")

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def process_query(request: QueryRequest):
    # Create a function to run the agent with the query
    async def run_agent():
        # We'll use a modified version of the main function that takes a query and returns a result
        result = await agent_process_query(request.query)
        return result
    
    # Execute the agent
    result = await run_agent()
    return result

async def agent_process_query(query: str):
    """Process a query using the quant agent and return the result."""
    try:
        from src.agents.quant.agent import create_agent_client
        from src.ingestion.clients import yahoo_client

        context_manager = await create_agent_client()

        async with context_manager as (client, agent):
            response = await agent.ainvoke({
                "messages": [{"role": "user", "content": query}],
            })

            # save to file the response
            with open("response.txt", "w") as f:
                f.write(str(response))

            # Parse and extract the relevant data from the response
            result = extract_structured_data(response, query)
            
            # Return the structured response directly
            return result

    except Exception as e:
        print(f"Error in agent_process_query: {str(e)}")
        return {"success": False, "message": str(e)}

def extract_structured_data(response, original_query=None):
    """
    Extract structured data from agent responses in a consistent format
    matching the frontend requirements.
    """
    # Initialize result with default structure
    result = {
        "message": "Stock analysis completed.",
        "symbol": "",
        "name": "",
        "price": 0,
        "currency": "USD",
        "change": 0,
        "changePercent": 0,
        "marketState": "",
        "details": {
            "previousClose": 0,
            "open": 0,
            "dayLow": 0,
            "dayHigh": 0,
            "volume": 0,
            "averageVolume": 0,
            "fiftyTwoWeekLow": 0,
            "fiftyTwoWeekHigh": 0
        },
        "company": {
            "sector": "",
            "industry": "",
            "country": "",
            "employees": 0,
            "website": "",
            "summary": ""
        },
        "predictions": [],
        "historical_data": [],
        "news": []
    }
    
    try:
        # Convert response to string for processing if it's not already
        response_str = str(response)
        print(f"DEBUG - Response length: {len(response_str)} characters")
        
        # Find the last AI message which contains the final response
        ai_messages = re.findall(r"AIMessage\(content='([^']+)'", response_str)
        if ai_messages:
            result["message"] = ai_messages[-1]  # Get the last AI message
            print(f"DEBUG - Found AI message: {result['message'][:100]}...")
        
        # Extract stock symbol from tools usage
        symbol = None
        
        # Check for stock quote tool usage
        stock_tool_match = re.search(r"Tool=get_stock_quote\s+Input={'symbol':\s*'([^']+)'}", response_str)
        if stock_tool_match:
            symbol = stock_tool_match.group(1)
            print(f"DEBUG - Found symbol from tool usage: {symbol}")
            
        # Look for stock quote tool message
        stock_data = None
        tool_match = re.search(r"ToolMessage\(content=(.+?), name='get_stock_quote'", response_str, re.DOTALL)
        if tool_match:
            # Try to extract the JSON content from the tool message
            content_str = tool_match.group(1)
            print(f"DEBUG - Found stock quote tool message, content length: {len(content_str)}")
            
            # Clean up the content string - handle both quoted and raw JSON
            if content_str.startswith("'") and content_str.endswith("'"):
                # Remove the outer quotes and unescape
                content_str = content_str[1:-1].replace("\\'", "'").replace('\\"', '"').replace('\\n', '\n')
                
                try:
                    # Try to parse as JSON
                    stock_data = json.loads(content_str)
                    print(f"DEBUG - Successfully parsed stock data JSON")
                    
                    # If we found a symbol in the response but not from get_stock_quote, capture it
                    if not symbol and "symbol" in stock_data:
                        symbol = stock_data["symbol"]
                        print(f"DEBUG - Extracted symbol from stock data: {symbol}")
                        
                    # Map stock data to output format
                    result["symbol"] = stock_data.get("symbol", "")
                    result["name"] = stock_data.get("longName") or stock_data.get("shortName") or ""
                    result["price"] = stock_data.get("currentPrice") or stock_data.get("regularMarketPrice") or 0
                    result["currency"] = stock_data.get("currency", "USD")
                    result["change"] = stock_data.get("regularMarketChange", 0)
                    result["changePercent"] = stock_data.get("regularMarketChangePercent", 0)
                    result["marketState"] = stock_data.get("marketState", "")
                    
                    # Map details
                    result["details"] = {
                        "previousClose": stock_data.get("previousClose", 0),
                        "open": stock_data.get("open", 0),
                        "dayLow": stock_data.get("dayLow") or stock_data.get("regularMarketDayLow", 0),
                        "dayHigh": stock_data.get("dayHigh") or stock_data.get("regularMarketDayHigh", 0),
                        "volume": stock_data.get("volume") or stock_data.get("regularMarketVolume", 0),
                        "averageVolume": stock_data.get("averageVolume", 0),
                        "fiftyTwoWeekLow": stock_data.get("fiftyTwoWeekLow", 0),
                        "fiftyTwoWeekHigh": stock_data.get("fiftyTwoWeekHigh", 0)
                    }
                    
                    # Map company info
                    result["company"] = {
                        "sector": stock_data.get("sector", ""),
                        "industry": stock_data.get("industry", ""),
                        "country": stock_data.get("country", ""),
                        "employees": stock_data.get("fullTimeEmployees", 0),
                        "website": stock_data.get("website", ""),
                        "summary": stock_data.get("longBusinessSummary", "")
                    }
                    
                    # Include the full stock_quote data as well
                    result["stock_quote"] = stock_data
                except json.JSONDecodeError as e:
                    print(f"Error decoding stock data: {e}")
        
        # Extract forecasts from forecast tool - try multiple patterns
        prediction_patterns = [
            r"ToolMessage\(content=(.+?), name='forecast_stock'", 
            r"name='forecast_stock', content=(.+?)\)",
            r"forecast_stock\((.+?)\)",
            r"Action: forecast_stock\s+Action Input: (.+?)\n"
        ]
        
        for pattern in prediction_patterns:
            prediction_match = re.search(pattern, response_str, re.DOTALL)
            if prediction_match:
                content_str = prediction_match.group(1)
                print(f"DEBUG - Found prediction data with pattern {pattern}, content length: {len(content_str)}")
                
                if content_str.startswith("'") and content_str.endswith("'"):
                    content_str = content_str[1:-1].replace("\\'", "'").replace('\\"', '"').replace('\\n', '\n')
                
                try:
                    # Try to parse as JSON or extract JSON from the string
                    if '{' in content_str and '}' in content_str:
                        # Find the JSON part
                        json_start = content_str.find('{')
                        json_end = content_str.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = content_str[json_start:json_end]
                            forecast_data = json.loads(json_str)
                            print(f"DEBUG - Successfully parsed prediction JSON")
                            
                            # Try different keys that might contain the forecast data
                            if "forecast" in forecast_data:
                                forecast_list = forecast_data["forecast"]
                            elif "predictions" in forecast_data:
                                forecast_list = forecast_data["predictions"]
                            else:
                                # If no list found, try to use the data itself if it's a list
                                forecast_list = forecast_data if isinstance(forecast_data, list) else []
                            
                            # Extract the prediction data
                            result["predictions"] = [
                                {
                                    "date": point.get("date", ""),
                                    "predicted": point.get("predicted", 0),
                                    "lower": point.get("lower_bound", 0) if "lower_bound" in point else point.get("lower", 0),
                                    "upper": point.get("upper_bound", 0) if "upper_bound" in point else point.get("upper", 0)
                                }
                                for point in forecast_list
                            ]
                            
                            print(f"DEBUG - Extracted {len(result['predictions'])} prediction points")
                            
                            # If historical data is included
                            if "historical" in forecast_data:
                                result["historical_data"] = [
                                    {
                                        "date": point.get("date", ""),
                                        "price": point.get("price", 0)
                                    }
                                    for point in forecast_data.get("historical", [])
                                ]
                                print(f"DEBUG - Extracted {len(result['historical_data'])} historical data points")
                            
                            # If we found predictions, break out of the pattern loop
                            if result["predictions"]:
                                break
                except json.JSONDecodeError as e:
                    print(f"Error parsing forecast data: {e}")
                except Exception as e:
                    print(f"Unexpected error processing forecast data: {e}")
        
        # Check if we found predictions
        if result["predictions"]:
            print(f"DEBUG - Final predictions: {result['predictions']}")
        else:
            print("DEBUG - No predictions found in any pattern")
        
        # If we have a symbol but no historical data, fetch it directly from Yahoo
        if symbol and not result["historical_data"]:
            try:
                from src.ingestion.clients import yahoo_client
                df = yahoo_client.get_historical_data(symbol, period="30d", interval="1d")
                
                if not df.empty:
                    # Convert DataFrame to list of dictionaries
                    historical_data = []
                    for date, row in df.iterrows():
                        historical_data.append({
                            "date": date.strftime('%Y-%m-%d'),
                            "price": row.get('Close', 0)
                        })
                    
                    # Sort by date
                    historical_data.sort(key=lambda x: x["date"])
                    result["historical_data"] = historical_data
                    print(f"DEBUG - Fetched {len(historical_data)} historical data points from Yahoo")
            except Exception as e:
                print(f"Error fetching historical data for {symbol}: {e}")
        
        # Extract news data - try multiple patterns
        news_patterns = [
            r"ToolMessage\(content=(.+?), name='get_stock_news'",
            r"name='get_stock_news', content=(.+?)\)",
            r"get_stock_news\((.+?)\)",
            r"Action: get_stock_news\s+Action Input: (.+?)\n"
        ]
        
        for pattern in news_patterns:
            news_match = re.search(pattern, response_str, re.DOTALL)
            if news_match:
                content_str = news_match.group(1)
                print(f"DEBUG - Found news data with pattern {pattern}, content length: {len(content_str)}")
                
                if content_str.startswith("'") and content_str.endswith("'"):
                    content_str = content_str[1:-1].replace("\\'", "'").replace('\\"', '"').replace('\\n', '\n')
                
                try:
                    # Try to parse as JSON or extract JSON from the string
                    if '[' in content_str and ']' in content_str:
                        # Find the JSON part
                        json_start = content_str.find('[')
                        json_end = content_str.rfind(']') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = content_str[json_start:json_end]
                            news_data = json.loads(json_str)
                            print(f"DEBUG - Successfully parsed news JSON")
                            
                            if isinstance(news_data, list):
                                result["news"] = [
                                    {
                                        "title": article.get("title", "News update"),
                                        "source": article.get("source", "Financial source") or article.get("publisher", ""),
                                        "date": article.get("date", datetime.fromtimestamp(article.get("providerPublishTime", 0)).strftime("%Y-%m-%d")),
                                        "summary": article.get("summary", "Market update"),
                                        "url": article.get("url", "#") or article.get("link", "")
                                    }
                                    for article in news_data
                                ]
                                print(f"DEBUG - Extracted {len(result['news'])} news items")
                                
                                # If we found news, break out of the pattern loop
                                if result["news"]:
                                    break
                except json.JSONDecodeError as e:
                    print(f"Error parsing news data: {e}")
                except Exception as e:
                    print(f"Unexpected error processing news data: {e}")
        
        # Check if we found news
        if result["news"]:
            print(f"DEBUG - Final news items: {len(result['news'])}")
        else:
            print("DEBUG - No news found in any pattern")
        
        # If we have a symbol but no news, fetch them directly
        if symbol and not result["news"]:
            try:
                from src.ingestion.clients import yahoo_client
                news_data = yahoo_client.get_news(symbol)
                
                if news_data and isinstance(news_data, list):
                    result["news"] = [
                        {
                            "title": article.get("title", "News update"),
                            "source": article.get("publisher", "Financial source"),
                            "date": datetime.fromtimestamp(article.get("providerPublishTime", 0)).strftime("%Y-%m-%d"),
                            "summary": article.get("summary", "Market update"),
                            "url": article.get("link", "#")
                        }
                        for article in news_data[:5]  # Limit to 5 news items
                    ]
                    print(f"DEBUG - Fetched {len(result['news'])} news items from Yahoo")
            except Exception as e:
                print(f"Error fetching news for {symbol}: {e}")
        
        return result
            
    except Exception as e:
        print(f"Error extracting structured data: {e}")
        import traceback
        traceback.print_exc()
        return {"message": "Unable to process response"}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8888, reload=True)

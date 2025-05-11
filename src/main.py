from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import uvicorn
import json
import re
from pydantic import BaseModel
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

        context_manager = await create_agent_client()

        async with context_manager as (client, agent):
            response = await agent.ainvoke({
                "messages": [{"role": "user", "content": query}],
            })

            # Parse and extract the relevant data from the response
            extracted_data = extract_structured_data(response)
            
            # Return a consistently structured response
            return {
                "success": True,
                "message": extracted_data["message"],
                "data": extracted_data["data"]
            }

    except Exception as e:
        return {"success": False, "message": str(e), "data": None}

def extract_structured_data(response):
    """
    Extract structured data from agent responses in a consistent format.
    Returns a dictionary with:
    - message: The human-readable text response
    - data: Structured data for visualization (if available)
    """
    result = {
        "message": "",
        "data": None
    }
    
    try:
        # Convert response to string for processing if it's not already
        response_str = str(response)
        
        # Find the last AI message which contains the final response
        ai_messages = re.findall(r"AIMessage\(content='([^']+)'", response_str)
        if ai_messages:
            result["message"] = ai_messages[-1]  # Get the last AI message
        
        # Look for stock quote tool message
        tool_match = re.search(r"ToolMessage\(content=(.+?), name='get_stock_quote'", response_str, re.DOTALL)
        if tool_match:
            # Try to extract the JSON content from the tool message
            content_str = tool_match.group(1)
            
            # Clean up the content string - handle both quoted and raw JSON
            if content_str.startswith("'") and content_str.endswith("'"):
                # Remove the outer quotes and unescape
                content_str = content_str[1:-1].replace("\\'", "'").replace('\\"', '"').replace('\\n', '\n')
                
                try:
                    # Try to parse as JSON
                    stock_data = json.loads(content_str)
                    
                    # Extract only the most relevant data for the frontend
                    result["data"] = {
                        "type": "stock_quote",
                        "symbol": stock_data.get("symbol"),
                        "name": stock_data.get("longName") or stock_data.get("shortName"),
                        "price": stock_data.get("currentPrice") or stock_data.get("regularMarketPrice"),
                        "currency": stock_data.get("currency", "USD"),
                        "change": stock_data.get("regularMarketChange"),
                        "changePercent": stock_data.get("regularMarketChangePercent"),
                        "marketState": stock_data.get("marketState"),
                        "details": {
                            "previousClose": stock_data.get("previousClose"),
                            "open": stock_data.get("open"),
                            "dayLow": stock_data.get("dayLow") or stock_data.get("regularMarketDayLow"),
                            "dayHigh": stock_data.get("dayHigh") or stock_data.get("regularMarketDayHigh"),
                            "volume": stock_data.get("volume") or stock_data.get("regularMarketVolume"),
                            "averageVolume": stock_data.get("averageVolume"),
                            "fiftyTwoWeekLow": stock_data.get("fiftyTwoWeekLow"),
                            "fiftyTwoWeekHigh": stock_data.get("fiftyTwoWeekHigh"),
                        },
                        "company": {
                            "sector": stock_data.get("sector"),
                            "industry": stock_data.get("industry"),
                            "country": stock_data.get("country"),
                            "employees": stock_data.get("fullTimeEmployees"),
                            "website": stock_data.get("website"),
                            "summary": stock_data.get("longBusinessSummary")
                        }
                    }
                except json.JSONDecodeError:
                    pass
        
        # Check for prediction data
        prediction_match = re.search(r"raw_forecast", response_str)
        if prediction_match:
            # Process prediction data logic here
            pass
            
        return result
            
    except Exception as e:
        print(f"Error extracting structured data: {e}")
        return {"message": "Unable to process response", "data": None}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8888, reload=True)

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import uvicorn
import json
import re
from pydantic import BaseModel
from src.agents.quant.agent import main as agent_main
from typing import Dict, List, Any, Optional

app = FastAPI()

# Add CORS middleware to allow requests from our Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

            # Initialize prediction data as None
            prediction_data = None
            content_text = ""

            # Check for prediction tools in the response
            if isinstance(response, list):
                # Look for prediction tool usage in the messages
                for msg in response:
                    msg_str = str(msg)
                    
                    # Check if this is a tool message with prediction data
                    prediction_tools = ['forecast_stock', 'analyze_volatility', 'analyze_trend']
                    if any(tool in msg_str for tool in prediction_tools):
                        # Extract tool name and response
                        for tool in prediction_tools:
                            if tool in msg_str:
                                # Try to extract the tool result which contains both text and data
                                try:
                                    # Look for ToolMessage with prediction data
                                    # The pattern matches text like: ToolMessage(content='{"text": "...", "data": {...}}' ...
                                    pattern = f"ToolMessage\\(content='([^']+)'[^)]*name='{tool}'[^)]*\\)"
                                    match = re.search(pattern, msg_str)
                                    
                                    if match:
                                        tool_content = match.group(1)
                                        # Clean up the content string
                                        tool_content = tool_content.replace('\\"', '"').replace("\\'", "'").replace("\\n", "")
                                        
                                        # Try to parse as JSON
                                        try:
                                            tool_result = json.loads(tool_content)
                                            if "text" in tool_result and "data" in tool_result:
                                                content_text = tool_result["text"]
                                                prediction_data = tool_result["data"]
                                                break
                                        except json.JSONDecodeError:
                                            pass
                                except Exception as e:
                                    print(f"Error extracting prediction data: {e}")

                # If we didn't find structured prediction data, get the last AIMessage content
                if not content_text:
                    for msg in reversed(response):
                        if hasattr(msg, 'content') and isinstance(msg.content, str) and msg.content.strip():
                            content_text = msg.content.strip()
                            break
                
                # Return both the content and prediction data if available
                if prediction_data:
                    return {
                        "content": str(response),  # Keep the original full response for debugging
                        "ai_response": content_text,  # Just the text part for display
                        "predictions": prediction_data,  # Structured data for charts
                        "success": True
                    }
                else:
                    return {"content": str(response), "success": True}

            # Handle direct AIMessage response (unlikely with tools)
            elif hasattr(response, 'content') and isinstance(response.content, str):
                return {"content": str(response), "success": True}

            return {"content": str(response), "success": True}

    except Exception as e:
        return {"error": str(e), "success": False}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8888, reload=True)
 
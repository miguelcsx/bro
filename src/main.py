from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import uvicorn
import json
from pydantic import BaseModel
from src.agents.quant.agent import main as agent_main

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
        
        # First await the coroutine to get the context manager
        context_manager = await create_agent_client()
        
        # Then use the context manager in the async with statement
        async with context_manager as (client, agent):
            response = await agent.ainvoke({
                "messages": [{"role": "user", "content": query}],
            })
            
            # Check if response is a dict with output
            if isinstance(response, dict) and "output" in response:
                return {"content": response["output"], "success": True}
            elif hasattr(response, 'content'):
                return {"content": response.content, "success": True}
            else:
                return {"content": str(response), "success": True}
            
    except Exception as e:
        return {"error": str(e), "success": False}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8888, reload=True)
 
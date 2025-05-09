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

        context_manager = await create_agent_client()

        async with context_manager as (client, agent):
            response = await agent.ainvoke({
                "messages": [{"role": "user", "content": query}],
            })

            # Extract the final AIMessage content
            if isinstance(response, list):
                # Look for the last AIMessage with content
                for msg in reversed(response):
                    if hasattr(msg, 'content') and isinstance(msg.content, str) and msg.content.strip():
                        return {"content": msg.content.strip(), "success": True}
                
                # If no content found, return the last message
                return {"content": str(response[-1]), "success": True}

            # Handle direct AIMessage response
            elif hasattr(response, 'content') and isinstance(response.content, str):
                return {"content": response.content.strip(), "success": True}

            return {"content": str(response), "success": True}

    except Exception as e:
        return {"error": str(e), "success": False}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8888, reload=True)
 
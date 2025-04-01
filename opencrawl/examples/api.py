import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import os
from search_agent import ResearchAgent

app = FastAPI(title="Research Agent API")

# Enable CORS - allowing the Next.js server to access the API
app.add_middleware(
    CORSMiddleware,
    # Allow both the client-side app and server-side Next.js to access the API
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store for ongoing research and results
research_tasks = {}
research_results = {}

# Initialize research agent
agent = ResearchAgent()

class QueryRequest(BaseModel):
    query: str

class ResearchResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[str] = None
    questions: Optional[List[str]] = None

@app.post("/research", response_model=ResearchResponse)
async def start_research(request: QueryRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    research_tasks[task_id] = "pending"
    research_results[task_id] = {
        "result": None,
        "questions": None
    }
    
    # Start the research in the background
    background_tasks.add_task(run_research, task_id, request.query)
    
    return ResearchResponse(
        task_id=task_id,
        status="pending"
    )

@app.get("/research/{task_id}", response_model=ResearchResponse)
async def get_research_status(task_id: str):
    if task_id not in research_tasks:
        raise HTTPException(status_code=404, detail="Research task not found")
    
    status = research_tasks[task_id]
    result = research_results[task_id].get("result")
    questions = research_results[task_id].get("questions")
    
    return ResearchResponse(
        task_id=task_id,
        status=status,
        result=result,
        questions=questions
    )

async def run_research(task_id: str, query: str):
    try:
        # Generate questions
        questions = await agent.generate_questions(query)
        research_results[task_id]["questions"] = questions
        
        # Update task to indicate questions are ready
        research_tasks[task_id] = "questions_ready"
        
        # Continue with the research
        all_urls = []
        for question in questions:
            urls = await agent.brave_search(question)
            all_urls.extend(urls)
        
        # Crawl URLs
        crawl_data = await agent.crawl_urls(all_urls)
        
        # Generate response
        response = await agent.generate_response(query, crawl_data)
        
        # Save result
        research_results[task_id]["result"] = response
        research_tasks[task_id] = "completed"
        
        # Save to file
        output_dir = "research_results"
        os.makedirs(output_dir, exist_ok=True)
        filename = query.lower().replace(" ", "_")[:50] + ".md"
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# Research Results: {query}\n\n")
            f.write(response)
            
    except Exception as e:
        research_tasks[task_id] = "failed"
        research_results[task_id]["result"] = f"Error during research: {str(e)}"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8020) 
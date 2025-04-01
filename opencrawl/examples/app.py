#!/usr/bin/env python
"""
TurboAPI wrapper for OpenCrawl API
"""
import sys
import os
import asyncio
from typing import List, Dict, Any, Optional
import uuid
from fastapi import Request, HTTPException

from turboapi import TurboAPI
from satya import Model, Field
from opencrawl.open_crawl_api import process_urls

app = TurboAPI(title="OpenCrawl API", 
               description="API for crawling websites, analyzing content, and storing data",
               version="1.0.0")

# Define request and response models with Satya
class CrawlRequest(Model):
    """Request model for crawling URLs"""
    user_id: Optional[str] = Field(description="User/session identifier (UUID)", required=False)
    thread_id: Optional[str] = Field(description="Thread identifier (UUID)", required=False)
    urls: List[str] = Field(description="List of URLs to crawl")

class ContentAnalysis(Model):
    """Content analysis information"""
    title: Optional[str] = Field(description="Title of the webpage", required=False)
    summary: Optional[str] = Field(description="Summary of the webpage content", required=False)
    main_topics: Optional[List[str]] = Field(description="Main topics covered on the page", required=False)
    key_points: Optional[List[str]] = Field(description="Key points extracted from the content", required=False)
    analyzed_at: Optional[str] = Field(description="When the content was analyzed", required=False)

class CrawlInfo(Model):
    """Crawl information"""
    success: bool = Field(description="Whether the crawl was successful")
    content_length: Optional[int] = Field(description="Length of the HTML content", required=False)
    has_markdown: Optional[bool] = Field(description="Whether markdown was generated", required=False)
    crawled_at: str = Field(description="When the URL was crawled")

class CrawlResult(Model):
    """Result model for a single crawled URL"""
    url: str = Field(description="The URL that was crawled")
    session_id: str = Field(description="Session identifier")
    content_type: str = Field(description="Type of content extracted")
    content_analysis: Optional[ContentAnalysis] = Field(description="Content analysis results", required=False)
    crawl_info: CrawlInfo = Field(description="Information about the crawl process")
    error: Optional[str] = Field(description="Error message if the crawl failed", required=False)

class CrawlResponse(Model):
    """Response model for crawling URLs"""
    results: List[CrawlResult] = Field(description="Results for each crawled URL")
    total: int = Field(description="Total number of URLs processed")
    successful: int = Field(description="Number of successfully crawled URLs")
    failed: int = Field(description="Number of failed crawls")

@app.get("/")
def read_root():
    """Root endpoint returning basic information"""
    return {
        "service": "OpenCrawl API",
        "version": "1.0.0",
        "description": "API for crawling websites, analyzing content, and storing data",
        "endpoints": [
            {"path": "/", "method": "GET", "description": "This information"},
            {"path": "/crawl", "method": "POST", "description": "Crawl websites and get metadata"}
        ]
    }

@app.post("/crawl", response_model=CrawlResponse)
async def crawl_websites(request: Request):
    """
    Crawl websites, analyze content, and return metadata
    
    - **user_id**: Optional user/session identifier (UUID). If not provided, a new UUID will be generated.
    - **thread_id**: Optional thread identifier (UUID). If not provided, a new UUID will be generated.
    - **urls**: List of URLs to crawl
    
    Returns metadata for each crawled URL including content analysis.
    """
    try:
        # Parse the JSON body
        body = await request.json()
        
        # Create a CrawlRequest object from the body
        crawl_request = CrawlRequest(
            user_id=body.get("user_id"),
            thread_id=body.get("thread_id"),
            urls=body.get("urls", [])
        )
        
        # Generate UUIDs if not provided
        user_id = crawl_request.user_id if crawl_request.user_id else str(uuid.uuid4())
        thread_id = crawl_request.thread_id if crawl_request.thread_id else str(uuid.uuid4())
        
        # Process URLs using OpenCrawl API
        results = await process_urls(user_id, thread_id, crawl_request.urls)
        
        # Count successful and failed crawls
        successful = sum(1 for r in results if r.get("crawl_info", {}).get("success", False))
        failed = len(results) - successful
        
        # Format response
        formatted_results = []
        for result in results:
            # Handle potential missing fields with default values
            formatted_result = {
                "url": result.get("url", "unknown"),
                "session_id": result.get("session_id", user_id),
                "content_type": result.get("content_type", "unknown"),
                "crawl_info": result.get("crawl_info", {"success": False, "crawled_at": "unknown"}),
            }
            
            # Add content analysis if available
            if "content_analysis" in result and result["content_analysis"]:
                formatted_result["content_analysis"] = result["content_analysis"]
            
            # Add error message if available
            if "error" in result:
                formatted_result["error"] = result["error"]
                
            formatted_results.append(formatted_result)
        
        # Create and return response
        response = {
            "results": formatted_results,
            "total": len(results),
            "successful": successful,
            "failed": failed
        }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Run the application with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import List, Optional
import scraper
import os

app = FastAPI(
    title="Google Maps Scraper API",
    description="API to scrape business data from Google Maps using Playwright.",
    version="1.0.0"
)

import redis

# Redis Configuration
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL)

API_KEY_NAME = "access_token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key_header: str = Security(api_key_header)):
    expected_token = os.environ.get("API_TOKEN")
    if not expected_token:
        # If API_TOKEN is not set in env, allow access (or you could decide to block)
        # For security, better to default to block or warn. 
        # Here we will assume if no token is set server-side, auth is disabled/open, 
        # OR we could enforce it. Let's enforce it if the user wants "auth".
        # But for "simple" usage, let's say if env var is missing, raise error configuration 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server authentication configuration error: API_TOKEN not set"
        )
        
    if api_key_header == expected_token:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials"
    )

class ScrapeRequest(BaseModel):
    query: str = Field(..., description="Search query for Google Maps (e.g., 'restaurants in New York')")
    headless: bool = Field(True, description="Run browser in headless mode")
    limit: int = Field(10, description="Maximum number of results to scrape", ge=1)

class BusinessResult(BaseModel):
    name: Optional[str] = None
    rating: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None

@app.post("/scrape", response_model=List[BusinessResult])
def scrape_google_maps(request: ScrapeRequest, api_key: str = Depends(get_api_key)):
    """
    Scrape Google Maps for business information.
    Required Header: access_token
    """
    results = scraper.run(request.query, headless=request.headless)
    return results
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Async Endpoints
import celery_app
from celery.result import AsyncResult

@app.post("/scrape/task", status_code=202)
def scrape_task_endpoint(request: ScrapeRequest, api_key: str = Depends(get_api_key)):
    """
    Start an asynchronous scraping task.
    Returns a task_id to check status later.
    """
    task = celery_app.scrape_task.delay(request.query, request.headless, request.limit)
    # Store task ID in history
    try:
        redis_client.lpush("job_history", task.id)
    except Exception as e:
        print(f"Error storing job history: {e}")
        
    return {"task_id": task.id, "status": "Pending"}

@app.get("/scrape/tasks/{task_id}")
def get_task_status(task_id: str, api_key: str = Depends(get_api_key)):
    """
    Check the status of a scraping task.
    """
    task_result = AsyncResult(task_id, app=celery_app.app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
    }
    
    if task_result.status == 'SUCCESS':
        response["result"] = task_result.result
    elif task_result.status == 'FAILURE':
        response["error"] = str(task_result.result)
        
    return response

@app.get("/scrape/jobs")
def get_job_history(api_key: str = Depends(get_api_key)):
    """
    Get a list of all executed job IDs.
    """
    try:
        # Get all items from the list
        job_ids = redis_client.lrange("job_history", 0, -1)
        # Convert bytes to string
        job_ids = [jid.decode('utf-8') for jid in job_ids]
        return {"jobs": job_ids, "count": len(job_ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi_mcp import FastApiMCP

# Initialize MCP Server
mcp = FastApiMCP(app)
mcp.mount_http()


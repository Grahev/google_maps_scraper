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
    try:
        results = scraper.run(request.query, headless=request.headless)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}

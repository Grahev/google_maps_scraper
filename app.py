from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import scraper
import sys

app = FastAPI(
    title="Google Maps Scraper API",
    description="API to scrape business data from Google Maps using Playwright.",
    version="1.0.0"
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
def scrape_google_maps(request: ScrapeRequest):
    """
    Scrape Google Maps for business information.
    """
    try:
        results = scraper.run(request.query, headless=request.headless)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}

import os
from celery import Celery
import scraper
import json

# Get Redis URL from environment or default to localhost
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

app = Celery('scraper_app', broker=REDIS_URL, backend=REDIS_URL)

@app.task(bind=True)
def scrape_task(self, query: str, headless: bool = True, limit: int = 10):
    """
    Celery task to run the scraper.
    """
    print(f"Starting scrape task for query: {query} with limit: {limit}")
    try:
        results = scraper.run(query, headless=headless, limit=limit)
        return results
    except Exception as e:
        # You might want to log the error specifically
        print(f"Error in scrape task: {e}")
        # Re-raise so Celery marks it as failed
        raise e

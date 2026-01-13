# Google Maps Scraper API

This project wraps a Google Maps scraper in a FastAPI application, allowing you to scrape business data via a RESTful API.

## Features

-   Scrape Google Maps results (Name, Rating, Address, Website, Phone).
-   FastAPI interface.
-   Dockerized for easy deployment.
-   Playwright-based scraping.

## Prerequisites

-   Python 3.9+ (for local run)
-   Docker and Docker Compose (for containerized run)

## Local Setup

1.  **Clone the repository.**
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Install Playwright browsers:**
    ```bash
    playwright install chromium
    ```
4.  **Run the application:**
    ```bash
    uvicorn app:app --reload
    ```
5.  **Access the API Documentation:**
    Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

## Docker Setup

1.  **Build and run the container:**
    ```bash
    docker-compose up --build
    ```
2.  **Access the API:**
    The API will be available at [http://localhost:8000](http://localhost:8000).

## API Usage

### Scrape Endpoint

**POST** `/scrape`

**Request Body:**

```json
{
  "query": "restaurants in New York",
  "headless": true
}
```

**Response:**

```json
[
  {
    "name": "Restaurant Name",
    "rating": "4.5",
    "address": "123 Main St, New York, NY",
    "website": "http://example.com",
    "phone": "+1 212-555-1234"
  }
]
```

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

### Health Check

**GET** `/health`

Check if the API is running.

**Response:**
```json
{
  "status": "ok"
}
```

### Scrape (Synchronous)

**POST** `/scrape`

Scrape Google Maps results synchronously. **Note:** This might timeout for long queries.

**Headers:**
- `access_token`: Your API token (if configured)

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

### Scrape (Asynchronous)

**POST** `/scrape/task`

Start an asynchronous scraping task. This is recommended to avoid timeouts.

**Headers:**
- `access_token`: Your API token (if configured)

**Request Body:**

```json
{
  "query": "restaurants in New York",
  "headless": true
}
```

**Response:**

```json
{
  "task_id": "unique-task-id",
  "status": "Pending"
}
```

### Check Task Status

**GET** `/scrape/tasks/{task_id}`

Check the status and get results of an asynchronous task.

**Headers:**
- `access_token`: Your API token (if configured)

**Response (Pending):**
```json
{
  "task_id": "unique-task-id",
  "status": "PENDING"
}
```

**Response (Success):**
```json
{
  "task_id": "unique-task-id",
  "status": "SUCCESS",
  "result": [
      {
        "name": "Restaurant Name",
        "rating": "4.5",
        "address": "123 Main St, New York, NY",
        "website": "http://example.com",
        "phone": "+1 212-555-1234"
      }
  ]
}
```

## n8n Integration

You can easily connect this API to n8n using the **HTTP Request** node.

1.  **Add an HTTP Request Node** to your workflow.
2.  **Method:** select `POST` (for scraping) or `GET` (for checking status).
3.  **URL:** Enter your API URL (e.g., `http://your-api-ip:8000/scrape/task`).
4.  **Authentication:**
    *   If you set an `API_TOKEN` in your environment variables, go to **Headers**.
    *   Add a new header:
        *   **Name:** `access_token`
        *   **Value:** `YOUR_API_TOKEN`
5.  **Body Parameters (for POST requests):**
    *   Select **JSON**.
    *   Enter the parameters:
        ```json
        {
          "query": "dentists in London",
          "headless": true
        }
        ```
6.  **Execute Node** to see the response.

**Recommended Workflow for n8n:**
1.  **HTTP Request (POST /scrape/task):** Start the scrape job.
2.  **Wait:** Add a Wait node (e.g., 30-60 seconds) to give the scraper time.
3.  **HTTP Request (GET /scrape/tasks/{task_id}):** Check these results using the `task_id` from step 1.
    *   Use an expression for the URL: `http://your-api-ip:8000/scrape/tasks/{{$json["task_id"]}}`

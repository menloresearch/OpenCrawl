# OpenCrawl API

This directory contains a FastAPI-based REST API for the OpenCrawl library, allowing you to crawl websites, analyze content, and store data using HTTP requests.

## Quick Start

The easiest way to run the API is using Docker:

```bash
# Run the API with Docker Compose
./run-api.sh
```

This will start:
- PostgreSQL 17 database
- Kafka and Zookeeper
- OpenCrawl API on port 8000

## API Endpoints

### GET /

Returns basic information about the API.

```bash
curl http://localhost:8000/
```

### GET /health

Health check endpoint.

```bash
curl http://localhost:8000/health
```

### POST /crawl

Crawl websites, analyze content, and get metadata.

```bash
curl -X POST http://localhost:8000/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com", "https://news.ycombinator.com"],
    "user_id": "optional-user-id",
    "thread_id": "optional-thread-id"
  }'
```

If `user_id` and `thread_id` are not provided, they will be automatically generated.

## Request Schema

```json
{
  "user_id": "string (optional)",
  "thread_id": "string (optional)",
  "urls": ["string", "string", ...]
}
```

## Response Schema

```json
{
  "results": [
    {
      "url": "string",
      "session_id": "string",
      "content_type": "string",
      "content_analysis": {
        "title": "string",
        "summary": "string",
        "main_topics": ["string", ...],
        "key_points": ["string", ...],
        "analyzed_at": "string"
      },
      "crawl_info": {
        "success": true,
        "content_length": 0,
        "has_markdown": true,
        "crawled_at": "string"
      },
      "error": "string (if failed)"
    }
  ],
  "total": 0,
  "successful": 0,
  "failed": 0
}
```

## Manual Setup

If you prefer to run the API without Docker:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure PostgreSQL and Kafka are available.

3. Set environment variables:
   ```bash
   export POSTGRES_CONNECTION_STRING="postgresql://postgres:postgres@localhost:5432/opencrawl"
   export KAFKA_BROKERS="localhost:9092"
   export KAFKA_TOPIC="pathik_crawl_data"
   ```

4. Run the API:
   ```bash
   python app.py
   ```

## Using with cURL

```bash
# Health check
curl http://localhost:8000/health

# Crawl websites
curl -X POST http://localhost:8000/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"]
  }'
``` 
# OpenCrawl API

A robust API for crawling websites, analyzing their content, and storing the processed data in a PostgreSQL database.

## Overview

OpenCrawl API provides a streamlined interface for crawling websites, extracting structured information, and storing the results. It uses Kafka for streaming data between components and supports LLM-based content analysis.

## Features

- Crawls web pages and extracts content
- Streams data through Kafka
- Analyzes content using LLM (via Groq API)
- Stores structured data in PostgreSQL
- Handles errors gracefully with fallback mechanisms
- Supports multiple URLs in parallel

## Requirements

- Python 3.8+
- PostgreSQL database
- Kafka (optional but recommended)
- Groq API key (for content analysis)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   # PostgreSQL connection string
   export POSTGRES_CONNECTION_STRING="postgresql://username:password@hostname:port/database"
   
   # Groq API key (for content analysis)
   export GROQ_API_KEY="your-groq-api-key"
   
   # Kafka configuration (if using Kafka)
   export KAFKA_BROKERS="localhost:9092"
   export KAFKA_TOPIC="pathik_crawl_data"
   export KAFKA_MAX_REQUEST_SIZE="10485760"
   export KAFKA_MESSAGE_MAX_BYTES="10485760"
   export KAFKA_REPLICA_FETCH_MAX_BYTES="10485760"
   ```

## Usage

### Basic Usage

```python
import asyncio
import uuid
from open_crawl_api import process_urls

async def example():
    user_id = str(uuid.uuid4())  # Generate a unique user ID
    thread_id = str(uuid.uuid4())  # Generate a unique thread ID
    urls = ["https://example.com", "https://another-example.com"]
    
    # Process URLs and get metadata
    metadata = await process_urls(user_id, thread_id, urls)
    
    # Print results
    print(f"Processed {len(metadata)} URLs")
    for item in metadata:
        print(f"URL: {item.get('url')}")
        if "content_analysis" in item and item["content_analysis"]:
            print(f"Title: {item['content_analysis'].get('title')}")
            print(f"Summary: {item['content_analysis'].get('summary')[:100]}...")

# Run the example
asyncio.run(example())
```

### API Reference

#### `process_urls(user_id, thread_id, urls)`

Processes a list of URLs and returns metadata.

**Parameters:**
- `user_id` (str): User/session identifier
- `thread_id` (str): Thread UUID
- `urls` (List[str]): List of URLs to crawl

**Returns:**
- List of dictionaries containing metadata for each URL

### Metadata Structure

The returned metadata includes:

```json
{
  "url": "https://example.com",
  "session_id": "user-id",
  "content_type": "both",
  "content_analysis": {
    "title": "Page Title",
    "summary": "Page summary...",
    "main_topics": ["Topic 1", "Topic 2"],
    "key_points": ["Point 1", "Point 2"],
    "analyzed_at": "2023-01-01T12:00:00"
  },
  "crawl_info": {
    "success": true,
    "content_length": 12345,
    "has_markdown": true,
    "crawled_at": "2023-01-01T12:00:00"
  }
}
```

## Database Schema

The API stores data in the following PostgreSQL tables:

- `crawler_users`: Stores user information
- `crawler_threads`: Stores thread information
- `crawler_websites`: Stores website data and metadata

## Troubleshooting

### Kafka Connection Issues

If Kafka is not available, the API will automatically fall back to a simulation mode. You'll see a message like:

```
Failed to connect to Kafka broker(s) localhost:9092: NoBrokersAvailable
Using fallback simulation mode without actual streaming.
```

This is normal if Kafka is not running, and the API will still function.

### Missing API Key

If the GROQ_API_KEY environment variable is not set, content analysis will be skipped. You'll see:

```
Warning: GROQ_API_KEY environment variable not set!
Content analysis will be skipped.
```

### Database Connection Issues

Ensure your PostgreSQL database is running and the connection string is correct. The API needs permissions to create tables if they don't exist.

## License

[Insert license information here]

## Acknowledgments

- Uses [pathik](https://github.com/path/to/pathik) for web crawling
- Uses [satya](https://github.com/path/to/satya) for data validation 
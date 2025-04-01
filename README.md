# OpenCrawl

A powerful web crawling and content analysis library that allows you to crawl websites, analyze their content using LLMs, and store the structured data for further use.

## Features

- Website crawling with [Pathik](https://github.com/menloresearch/pathik)
- Content analysis using LLMs (Groq, OpenAI, etc.)
- Structured data extraction from web pages
- PostgreSQL storage of crawled data
- Kafka integration for scalable processing

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/opencrawl.git
cd opencrawl

# Install the package
pip install -e .
```

## Docker Setup

OpenCrawl includes a Docker Compose configuration for easy setup of required services:

```bash
# Start PostgreSQL and Kafka
docker-compose up -d

# View Kafka UI (optional)
open http://localhost:9000
```

### Troubleshooting Docker Setup

If you encounter errors with Docker volumes, such as:
- PostgreSQL compatibility issues between versions
- Zookeeper snapshot/log inconsistency errors

You can use the included cleanup script:

```bash
# Run the cleanup script to remove incompatible volumes
./docker-cleanup.sh

# Then restart the services
docker-compose up -d
```

This will remove all existing Docker volumes and create fresh ones, which is useful when upgrading or when volumes become corrupted.

## Quick Start

```python
import asyncio
import os
from opencrawl import OpenCrawl

async def main():
    # Initialize OpenCrawl with API key from environment variable
    crawler = OpenCrawl(
        content_analyzer_config={
            "api_key": os.getenv("GROQ_API_KEY")
        }
    )
    
    # Process a list of URLs
    results = await crawler.process_urls(
        urls=["https://example.com", "https://news.ycombinator.com"],
        verbose=True
    )
    
    # Print the results
    for result in results:
        print(f"URL: {result.get('url')}")
        content_analysis = result.get("content_analysis")
        if content_analysis:
            print(f"Title: {content_analysis.get('title')}")
            print(f"Topics: {', '.join(content_analysis.get('main_topics', []))}")
            print(f"Summary: {content_analysis.get('summary')[:100]}...")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
```

## Customizing the ContentAnalyzer

You can customize the ContentAnalyzer with different LLM configurations:

```python
from opencrawl import OpenCrawl

# Initialize with custom model configuration
crawler = OpenCrawl(
    content_analyzer_config={
        "api_key": "your-api-key",
        "model": "openai/gpt-4o",  # Change the model
        "max_tokens": 32000,        # Adjust token limit
        "max_concurrent": 10,       # Increase concurrent requests
        "extra_config": {           # Additional LLM configuration
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
    }
)

# Or configure later
crawler = OpenCrawl()
crawler.setup_content_analyzer(
    api_key="your-api-key",
    model="anthropic/claude-3-opus-20240229",
    max_tokens=100000
)
```

## Database Configuration

OpenCrawl automatically creates the necessary tables in your PostgreSQL database. The default database configuration is included in the Docker Compose setup.

## Advanced Usage

### Custom Kafka Configuration

```python
crawler = OpenCrawl(
    kafka_config={
        "brokers": "kafka:9092",
        "topic": "custom_topic",
        "max_request_size": 20971520,  # 20MB
    }
)
```

### Processing URLs with Custom Thread and User IDs

```python
results = await crawler.process_urls(
    urls=["https://example.com"],
    user_id="custom-user-id",
    thread_id="custom-thread-id",
    thread_name="My Research Project",
    content_type="both",  # Extract both HTML and Markdown
    parallel=True,        # Process URLs in parallel
    verbose=True          # Show detailed logs
)
```

## License

MIT 
# OpenCrawl

A powerful web crawling and content analysis library that allows you to crawl websites, analyze their content using LLMs, and store the structured data for further use. Built with ethics and efficiency in mind.

## Features

- Website crawling with [Pathik](https://github.com/menloresearch/pathik-menlo)
- Content analysis using LLMs (Groq, OpenAI, etc.)
- Structured data extraction from web pages
- PostgreSQL storage of crawled data
- Kafka integration for scalable processing

## Ethical Crawling

OpenCrawl is built with ethical web crawling in mind. Our crawler, Pathik, strictly adheres to website robots.txt files and respects website crawling policies. This means:

- Only crawls websites that explicitly allow crawling through robots.txt
- Respects crawl rate limits and delays between requests
- Follows website-specific crawling rules
- Helps maintain a sustainable and respectful web ecosystem

This approach ensures:
- Safe and secure crawling practices
- Respect for website owners' preferences
- Reduced server load on target websites
- Compliance with web standards and best practices

## Efficient Data Processing

OpenCrawl uses Kafka for high-throughput data processing, enabling efficient and ethical crawling at scale:

### Why Kafka?
- **Parallel Processing**: Process multiple URLs simultaneously while respecting rate limits
- **Stream Processing**: Real-time analysis of crawled content
- **Scalability**: Handle large volumes of data without overwhelming target servers
- **Reliability**: Ensure no data is lost during processing
- **Backpressure**: Automatically adjust processing speed based on system load

### Ethical Throughput
While Kafka enables high throughput, we maintain ethical crawling practices:
- Rate limiting per domain
- Respectful delays between requests
- Queue-based processing to prevent server overload
- Smart batching of requests to optimize efficiency while staying within limits

## Installation

You can install OpenCrawl directly from PyPI:

```bash
pip install opencrawl
```

Or install from source:

```bash
# Clone the repository
git clone https://github.com/menloresearch/opencrawl.git
cd opencrawl

# Install the package
pip install -e .
```

## Documentation

- [Changelog](CHANGELOG.md) - List of changes and version history
- [Security Policy](SECURITY.md) - Security guidelines and reporting

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
    
    # Process a list of URLs with ethical rate limiting
    results = await crawler.process_urls(
        urls=["https://example.com", "https://news.ycombinator.com"],
        verbose=True,
        rate_limit=1.0  # 1 request per second per domain
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
        "rate_limit": 2.0,             # 2 requests per second per domain
        "batch_size": 100,             # Process URLs in batches
        "max_concurrent": 10           # Maximum concurrent requests
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
    content_type="both",     # Extract both HTML and Markdown
    parallel=True,          # Process URLs in parallel
    rate_limit=1.0,        # Respect rate limits
    verbose=True           # Show detailed logs
)
```

## Contributing

We welcome contributions that help make web crawling more ethical and efficient! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

## License

MIT 
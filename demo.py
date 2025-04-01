#!/usr/bin/env python3
import asyncio
import os
import sys
import time

# Add opencrawl to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Set up environment variables for demo
os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5432/opencrawl"
os.environ["KAFKA_BROKERS"] = "localhost:9092"

try:
    # Import the demo function
    print("Importing OpenCrawl library...")
    from opencrawl import OpenCrawl
    
    async def run_demo():
        # Configure your API key for content analysis
        api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print("Warning: No API key found. Content analysis will be disabled.")
            print("Set GROQ_API_KEY or OPENAI_API_KEY environment variable for full functionality.")
        
        # Initialize OpenCrawl
        crawler = OpenCrawl(
            content_analyzer_config={"api_key": api_key} if api_key else None
        )
        
        # Test URLs
        urls = [
            "https://www.example.com",
            "https://news.ycombinator.com"
        ]
        
        print(f"\nProcessing {len(urls)} URLs...")
        
        # Process URLs
        results = await crawler.process_urls(
            urls=urls,
            verbose=True
        )
        
        print("\nResults Summary:")
        print("=" * 50)
        for i, result in enumerate(results):
            print(f"Result {i+1}:")
            print(f"  URL: {result.get('url')}")
            success = result.get('success')
            if success is None and 'crawl_info' in result:
                success = result['crawl_info'].get('success', False)
            print(f"  Success: {success}")
            
            content_analysis = result.get("content_analysis")
            if content_analysis:
                print(f"  Title: {content_analysis.get('title', 'Unknown')}")
                print(f"  Topics: {', '.join(content_analysis.get('main_topics', ['None']))}")
                summary = content_analysis.get('summary', 'None')
                if summary:
                    print(f"  Summary: {summary[:100]}...")
            print("-" * 40)

    if __name__ == "__main__":
        asyncio.run(run_demo())
        
except Exception as e:
    print(f"Error loading OpenCrawl: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

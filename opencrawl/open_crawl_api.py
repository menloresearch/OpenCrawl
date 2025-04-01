#!/usr/bin/env python
"""
API wrapper for the integrated website crawler pipeline.
Takes user_id, thread_id, and a list of URLs, and returns metadata.
"""
import os
import sys
import asyncio
from datetime import datetime
from typing import List, Dict, Any
import dotenv

dotenv.load_dotenv()

# Add the parent directory to the path to ensure we can import pathik
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import pathik

# Handle import for website_crawler_db based on environment
try:
    # Try absolute import first (for Docker)
    from OpenCrawl.opencrawl.website_crawler_db import (
        setup_database, 
        store_website_data, 
        create_thread, 
        thread_exists, 
        create_user
    )
except ImportError:
    try:
        # Try direct opencrawl package
        from opencrawl.website_crawler_db import (
            setup_database, 
            store_website_data, 
            create_thread, 
            thread_exists, 
            create_user
        )
    except ImportError:
        # Fall back to relative import (for local development)
        from website_crawler_db import (
            setup_database, 
            store_website_data, 
            create_thread, 
            thread_exists, 
            create_user
        )

async def crawl_urls(
    user_id: str,
    thread_id: str,
    urls: List[str]
) -> List[Dict[str, Any]]:
    """
    Crawls the provided URLs, analyzes the content, and returns metadata.
    
    Args:
        user_id: User/session identifier
        thread_id: Thread UUID
        urls: List of URLs to crawl
        
    Returns:
        List of dictionaries containing the metadata for each crawled URL
    """
    # Setup database
    conn, cursor = setup_database()
    if not conn or not cursor:
        raise Exception("Failed to setup database")
    
    # Ensure user exists in database (create with auto-generated username and email if not)
    cursor.execute("SELECT 1 FROM public.crawler_users WHERE user_id = %s", (user_id,))
    user_exists = cursor.fetchone() is not None
    
    if not user_exists:
        print(f"User {user_id} does not exist, creating it...")
        # Create a user with auto-generated username and email
        username = f"auto_user_{user_id[:8]}"
        email = f"auto_{user_id[:8]}@example.com"
        # Create user with the exact user_id we were given
        cursor.execute(
            "INSERT INTO public.crawler_users (user_id, username, email) VALUES (%s, %s, %s) RETURNING user_id",
            (user_id, username, email)
        )
        conn.commit()
        print(f"User created with ID: {user_id}")
    
    # Ensure thread exists in database
    if not thread_exists(conn, cursor, thread_id):
        print(f"Thread {thread_id} does not exist, creating it...")
        result = create_thread(conn, cursor, "Auto-created Thread", user_id, thread_id)
        if not result:
            raise Exception(f"Failed to create thread with ID {thread_id}")
    
    # Track metadata for each URL
    metadata_list = []
    
    try:
        # Set up Kafka configuration
        os.environ["KAFKA_BROKERS"] = "localhost:9092"
        os.environ["KAFKA_TOPIC"] = "pathik_crawl_data"
        os.environ["KAFKA_MAX_REQUEST_SIZE"] = "10485760"  # 10MB
        os.environ["KAFKA_MESSAGE_MAX_BYTES"] = "10485760"  # 10MB
        os.environ["KAFKA_REPLICA_FETCH_MAX_BYTES"] = "10485760"  # 10MB
        
        # Stream URLs to Kafka using pathik's built-in functionality
        print(f"Session ID: {user_id}")
        results = {}
        try:
            results = pathik.stream_to_kafka(
                urls=urls,
                content_type="html",
                topic=os.environ["KAFKA_TOPIC"],
                session=user_id,  # Use user_id as session_id
                parallel=True,
                compression_type="gzip",
                max_message_size=10485760  # 10MB
            )
        except Exception as e:
            print(f"Error with Kafka streaming: {e}")
            print("Continuing with fallback mode...")
            # The pathik library should automatically fall back to simulation mode without Kafka
        
        # Import ContentAnalyzer only when needed (helps with dependency management)
        try:
            from opencrawl import ContentAnalyzer
        except ImportError:
            from opencrawl.opencrawl import ContentAnalyzer
        
        # Initialize content analyzer with a try/except block to handle missing API key
        try:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                print("Warning: GROQ_API_KEY environment variable not set!")
                print("Content analysis will be skipped.")
                analyzer = None
            else:
                analyzer = ContentAnalyzer(api_key=api_key)
        except Exception as e:
            print(f"Error initializing ContentAnalyzer: {e}")
            analyzer = None
            
        # Process each URL's result
        analysis_tasks = {}
        
        # Start analysis for all successful crawls
        for url, result in results.items():
            if result.get("success", False):
                if analyzer:
                    analysis_task = analyzer.process_webpage(url, result.get("html", ""))
                    analysis_tasks[url] = {
                        "task": analysis_task,
                        "result": result,
                        "start_time": datetime.now()
                    }
                else:
                    # Skip content analysis if analyzer is not available
                    website_data = {
                        "url": url,
                        "raw_html": result.get("html", ""),
                        "website_summary": result.get("markdown", "")[:500] + "..." if result.get("markdown") else "",
                        "thread_id": thread_id,
                        "website_type": "other",
                        "user_id": user_id,
                        "crawled_at": datetime.now(),
                        "metadata": {
                            "url": url,
                            "session_id": user_id,
                            "content_type": "html",
                            "content_analysis": None,
                            "crawl_info": {
                                "success": True,
                                "content_length": len(result.get("html", "")),
                                "has_markdown": bool(result.get("markdown")),
                                "crawled_at": datetime.now().isoformat()
                            }
                        }
                    }
                    
                    # Store in database
                    try:
                        store_website_data(conn, cursor, website_data)
                        print(f"✅ Successfully stored data for {url}")
                        # Add to metadata list (only the metadata portion)
                        metadata_list.append(website_data["metadata"])
                    except Exception as e:
                        print(f"❌ Error storing website data: {e}")
                        metadata_list.append({
                            "url": url,
                            "session_id": user_id,
                            "thread_id": thread_id,
                            "error": str(e),
                            "success": False,
                            "crawled_at": datetime.now().isoformat()
                        })
        
        # Process results and store them for URLs that had analysis tasks
        if analyzer:
            for url, task_info in analysis_tasks.items():
                try:
                    result = task_info["result"]
                    webpage_data = await task_info["task"]
                    
                    # Prepare website data
                    website_data = {
                        "url": url,
                        "raw_html": result.get("html", ""),
                        "website_summary": result.get("markdown", "")[:500] + "..." if result.get("markdown") else "",
                        "thread_id": thread_id,
                        "website_type": "other",
                        "user_id": user_id,
                        "crawled_at": datetime.now(),
                        "metadata": {
                            "url": url,  # Add URL to metadata for easier reference
                            "session_id": user_id,
                            "content_type": "html",
                            "content_analysis": None,
                            "crawl_info": {
                                "success": True,
                                "content_length": len(result.get("html", "")),
                                "has_markdown": bool(result.get("markdown")),
                                "crawled_at": datetime.now().isoformat()
                            }
                        }
                    }
                    
                    # Update with analysis results if available
                    if webpage_data:
                        website_data["website_type"] = webpage_data.main_topics[0] if webpage_data.main_topics else "other"
                        website_data["website_summary"] = webpage_data.summary
                        website_data["metadata"]["content_analysis"] = {
                            "title": webpage_data.title,
                            "summary": webpage_data.summary,
                            "main_topics": webpage_data.main_topics,
                            "key_points": webpage_data.key_points,
                            "analyzed_at": datetime.now().isoformat()
                        }
                    
                    # Store in database
                    try:
                        store_website_data(conn, cursor, website_data)
                        print(f"✅ Successfully stored data for {url}")
                    except Exception as e:
                        print(f"❌ Error storing website data: {e}")
                    
                    # Add to metadata list (only the metadata portion)
                    metadata_list.append(website_data["metadata"])
                    
                except Exception as e:
                    # Add failed entry to metadata list
                    print(f"❌ Error processing {url}: {e}")
                    metadata_list.append({
                        "url": url,
                        "session_id": user_id,
                        "thread_id": thread_id,
                        "error": str(e),
                        "success": False,
                        "crawled_at": datetime.now().isoformat()
                    })
    
    finally:
        # Close database connection
        cursor.close()
        conn.close()
    
    return metadata_list

async def process_urls(
    user_id: str,
    thread_id: str,
    urls: List[str]
) -> List[Dict[str, Any]]:
    """
    Public API function to crawl URLs and return metadata.
    
    Args:
        user_id: User/session identifier
        thread_id: Thread UUID
        urls: List of URLs to crawl
        
    Returns:
        List of dictionaries containing the metadata for each crawled URL
    """
    return await crawl_urls(user_id, thread_id, urls)

# Example usage
if __name__ == "__main__":
    import uuid
    
    async def example():
        user_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())
        urls = ["https://stackoverflow.com/questions/21020347/how-can-i-send-large-messages-with-kafka-over-15mb","https://github.com/menloresearch"]
        
        print(f"Processing URLs with user_id: {user_id} and thread_id: {thread_id}")
        metadata = await process_urls(user_id, thread_id, urls)
        
        print(f"\nProcessed {len(metadata)} URLs")
        print("Metadata:")
        for item in metadata:
            print(f"- URL: {item.get('url', 'Unknown')}")
            print(f"  Success: {item.get('success', item.get('crawl_info', {}).get('success', False))}")
            if "content_analysis" in item and item["content_analysis"]:
                print(f"  Title: {item['content_analysis'].get('title', 'Unknown')}")
                print(f"  Summary: {item['content_analysis'].get('summary', 'None')[:100]}...")
    
    asyncio.run(example()) 
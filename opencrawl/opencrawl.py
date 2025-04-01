#!/usr/bin/env python
"""
Integrated website crawler library for processing and analyzing web content.
"""
import os
import sys
import uuid
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple, Union
from satya import Model, Field
import dotenv

dotenv.load_dotenv()

# Add the parent directory to the path to ensure we can import pathik
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import pathik
from bhumi.base_client import BaseLLMClient, LLMConfig
from .website_crawler_db import setup_database, create_user, create_thread, store_website_data, thread_exists

# Define structured data schema
class WebpageContent(Model):
    """Structured information extracted from a webpage"""
    url: str = Field(description="The URL of the webpage")
    title: str = Field(description="The title of the webpage")
    summary: str = Field(description="A summary of the webpage content")
    main_topics: List[str] = Field(description="List of main topics covered on the page")
    key_points: List[str] = Field(description="List of key points or facts extracted from the content")
    extracted_at: datetime = Field(description="When the information was extracted")

class ContentAnalyzer:
    """Handles content analysis using LLM"""
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "groq/qwen-2.5-32b", 
        max_tokens: int = 123000,
        max_concurrent: int = 5,
        extra_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the content analyzer with customizable LLM configuration.
        
        Args:
            api_key: API key for the LLM provider
            model: Model name to use
            max_tokens: Maximum number of tokens for LLM responses
            max_concurrent: Maximum number of concurrent LLM requests
            extra_config: Additional configuration options for the LLM
        """
        # Set default extra_config if not provided
        if extra_config is None:
            extra_config = {"response_format": {"type": "json_object"}}
        
        self.config = LLMConfig(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            extra_config=extra_config
        )
        self.client = BaseLLMClient(config=self.config, max_concurrent=max_concurrent)

    async def process_webpage(self, url: str, content: str) -> Optional[WebpageContent]:
        """Process a single webpage and extract structured information"""
        # Prepare enhanced prompt for the LLM with explicit instructions for topics and key points
        prompt = f"""Extract key information from this webpage content.
URL: {url}

Based on the content, you MUST identify:
1. A concise title for the page
2. A summary of the main content (100-200 words)
3. At least 3-5 main topics covered on the page (be specific)
4. At least 3-5 key points or facts from the content

Content:
{content[:9000]}

Return ONLY a JSON object with the following fields:
- url: The URL of the webpage
- title: The title of the webpage
- summary: A concise summary of the content
- main_topics: List of main topics covered (MUST extract at least 3 topics)
- key_points: List of key facts or points (MUST extract at least 3 points)
- extracted_at: Current timestamp
"""
        
        try:
            # Get structured response from LLM
            response = await self.client.completion([
                {"role": "system", "content": """You are a web content analyzer expert at extracting structured data.
                    Your task is to extract specific information from webpage content.
                    IMPORTANT: 
                    - If you cannot find explicit topics, infer them from the content.
                    - Always return at least 3 main topics and 3 key points.
                    - If content is unclear, extract broader topics or categories.
                    - Make summaries concise but informative.
                    - Return data in the exact JSON schema requested."""},
                {"role": "user", "content": prompt}
            ])
            
            # Clean and parse the response
            text_response = response["text"]
            
            # Improved JSON extraction to handle various formats returned by LLMs
            try:
                # First try direct JSON parsing
                data = json.loads(text_response)
            except json.JSONDecodeError:
                # Handle markdown code block format
                if "```json" in text_response or "```" in text_response:
                    # Extract content between code blocks
                    lines = text_response.split("\n")
                    # Remove markdown code block markers
                    if lines and lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].endswith("```"):
                        lines[-1] = lines[-1].rstrip("`")
                    elif lines and lines[-1] == "```":
                        lines = lines[:-1]
                    
                    # Rejoin and try to parse again
                    json_str = "\n".join(lines).strip()
                    try:
                        data = json.loads(json_str)
                    except json.JSONDecodeError:
                        # Last attempt: try to extract JSON between curly braces
                        import re
                        json_match = re.search(r'\{.*\}', text_response, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                            data = json.loads(json_str)
                        else:
                            raise ValueError(f"Could not extract valid JSON from LLM response: {text_response[:100]}...")
                else:
                    raise ValueError(f"Invalid response format from LLM: {text_response[:100]}...")
            
            # Ensure all required fields are present with fallback values
            current_time = datetime.now()
            
            # Check for missing or empty fields and apply defaults
            if not data.get("url"):
                data["url"] = url
                
            if not data.get("title"):
                # Extract domain name as fallback title
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                data["title"] = f"Content from {domain}"
                
            if not data.get("summary"):
                # Create a summary from the first part of the content
                summary = "Content could not be fully analyzed. This appears to be a web page."
                if content and len(content) > 100:
                    content_preview = content[:100].replace("\n", " ")
                    summary += f" Preview: {content_preview}..."
                data["summary"] = summary
            
            # Handle main_topics field
            if not data.get("main_topics") or not isinstance(data["main_topics"], list) or len(data["main_topics"]) == 0:
                # Extract domain and path elements as fallback topics
                from urllib.parse import urlparse
                parsed_url = urlparse(url)
                domain = parsed_url.netloc
                path_parts = [p for p in parsed_url.path.split("/") if p]
                
                fallback_topics = []
                # Add domain as a topic
                fallback_topics.append(f"Content from {domain}")
                
                # Add path elements as topics
                if path_parts:
                    for part in path_parts[:2]:  # Use up to 2 path parts
                        topic = part.replace('-', ' ').replace('_', ' ').title()
                        if topic and len(topic) > 2:
                            fallback_topics.append(topic)
                
                # Add "General Information" as a catch-all
                if len(fallback_topics) < 3:
                    fallback_topics.append("General Information")
                    fallback_topics.append("Web Content")
                    fallback_topics.append("Online Resource")
                
                data["main_topics"] = fallback_topics[:5]  # Limit to 5 topics
            
            # Handle key_points field
            if not data.get("key_points") or not isinstance(data["key_points"], list) or len(data["key_points"]) == 0:
                # Generate generic key points
                fallback_points = []
                
                # Try to extract sentences as key points
                import re
                sentences = re.split(r'[.!?]', content[:1000])
                clean_sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
                
                if clean_sentences:
                    # Use top 3 sentences as key points
                    for i, sentence in enumerate(clean_sentences[:3]):
                        fallback_points.append(f"{sentence}.")
                
                # Add generic fallbacks if needed
                if len(fallback_points) < 3:
                    fallback_points.append(f"Content was retrieved from {url}")
                    fallback_points.append("The page contains web-based information")
                    fallback_points.append("Additional details may be available on the original website")
                
                data["key_points"] = fallback_points[:5]  # Limit to 5 key points
            
            # Add extraction timestamp if missing
            if not data.get("extracted_at"):
                data["extracted_at"] = current_time
            
            # Create and validate WebpageContent object
            webpage_data = WebpageContent(**data)
            return webpage_data
            
        except Exception as e:
            print(f"Error processing {url}: {e}")
            # Provide a fallback WebpageContent with generic information
            try:
                # Extract domain name for the title
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                
                # Create a summary from the first part of the content
                summary = "Content could not be fully analyzed. This appears to be a web page."
                if content and len(content) > 100:
                    content_preview = content[:100].replace("\n", " ")
                    summary += f" Preview: {content_preview}..."
                
                # Create fallback data
                fallback_data = {
                    "url": url,
                    "title": f"Content from {domain}",
                    "summary": summary,
                    "main_topics": ["Web Content", "Online Resource", domain.replace("www.", "")],
                    "key_points": [
                        f"Content was retrieved from {url}",
                        "Analysis was limited due to content format",
                        "Visit the original URL for complete information"
                    ],
                    "extracted_at": datetime.now()
                }
                
                return WebpageContent(**fallback_data)
            except Exception as inner_e:
                print(f"Even fallback creation failed for {url}: {inner_e}")
                return None

class OpenCrawl:
    """Main interface for the OpenCrawl library"""
    
    def __init__(
        self,
        db_config: Optional[Dict[str, Any]] = None,
        kafka_config: Optional[Dict[str, Any]] = None,
        content_analyzer_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the OpenCrawl library with customizable components.
        
        Args:
            db_config: Database configuration options
            kafka_config: Kafka configuration options
            content_analyzer_config: Content analyzer configuration options
        """
        # Default configurations
        self.db_config = db_config or {}
        
        # Default Kafka configuration
        self.kafka_config = {
            "brokers": "localhost:9092",
            "topic": "pathik_crawl_data",
            "max_request_size": 10485760,  # 10MB
            "message_max_bytes": 10485760,  # 10MB
            "replica_fetch_max_bytes": 10485760,  # 10MB
            **(kafka_config or {})
        }
        
        # Set Kafka environment variables
        for key, value in self.kafka_config.items():
            if key.upper() != "BROKERS":  # Special case for brokers
                os.environ[f"KAFKA_{key.upper()}"] = str(value)
            else:
                os.environ["KAFKA_BROKERS"] = str(value)
        
        # Initialize content analyzer if configuration is provided
        self.content_analyzer = None
        if content_analyzer_config:
            self._setup_content_analyzer(content_analyzer_config)
    
    def _setup_content_analyzer(self, config: Dict[str, Any]):
        """Set up the content analyzer with the provided configuration"""
        if "api_key" in config:
            self.content_analyzer = ContentAnalyzer(**config)
        else:
            # Try to get API key from environment variables if not provided
            api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
            if api_key:
                config["api_key"] = api_key
                self.content_analyzer = ContentAnalyzer(**config)
            else:
                print("Warning: No API key provided for content analyzer. Content analysis will be disabled.")
    
    def setup_content_analyzer(self, **config):
        """
        Set up content analyzer with custom configuration.
        
        Args:
            **config: Configuration options for ContentAnalyzer
                - api_key: API key for the LLM provider
                - model: Model name to use (default: "groq/qwen-2.5-32b")
                - max_tokens: Maximum number of tokens (default: 123000)
                - max_concurrent: Maximum concurrent requests (default: 5)
                - extra_config: Additional LLM configuration
        """
        self._setup_content_analyzer(config)
        return self.content_analyzer is not None
    
    async def process_urls(
        self,
        urls: List[str],
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        thread_name: str = "Auto-created Thread",
        content_type: str = "both",
        parallel: bool = True,
        verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Process a list of URLs by crawling and analyzing their content.
        
        Args:
            urls: List of URLs to process
            user_id: User identifier (auto-generated if not provided)
            thread_id: Thread identifier (auto-generated if not provided)
            thread_name: Name for the thread if it needs to be created
            content_type: Type of content to extract ("html", "markdown", or "both")
            parallel: Whether to process URLs in parallel
            verbose: Whether to print detailed progress information
            
        Returns:
            List of metadata dictionaries for each processed URL
        """
        # Generate IDs if not provided
        if not user_id:
            user_id = str(uuid.uuid4())
            if verbose:
                print(f"Generated user_id: {user_id}")
        
        if not thread_id:
            thread_id = str(uuid.uuid4())
            if verbose:
                print(f"Generated thread_id: {thread_id}")
        
        # Setup database
        conn, cursor = setup_database()
        if not conn or not cursor:
            raise Exception("Failed to setup database")
        
        # Create session ID for tracking
        session_id = str(uuid.uuid4())
        
        try:
            # Ensure user exists in database
            cursor.execute("SELECT 1 FROM public.crawler_users WHERE user_id = %s", (user_id,))
            user_exists = cursor.fetchone() is not None
            
            if not user_exists:
                if verbose:
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
                if verbose:
                    print(f"User created with ID: {user_id}")
            
            # Ensure thread exists in database
            if not thread_exists(conn, cursor, thread_id):
                if verbose:
                    print(f"Thread {thread_id} does not exist, creating it...")
                result = create_thread(conn, cursor, thread_name, user_id, thread_id)
                if not result:
                    raise Exception(f"Failed to create thread with ID {thread_id}")
            
            # Track metadata for each URL
            metadata_list = []
            
            # Stream URLs to Kafka using pathik's built-in functionality
            if verbose:
                print(f"Streaming {len(urls)} URLs for processing...")
                print(f"Session ID: {session_id}")
            
            results = pathik.stream_to_kafka(
                urls=urls,
                content_type=content_type,
                topic=self.kafka_config["topic"],
                session=session_id,
                parallel=parallel,
                compression_type="gzip",
                max_message_size=self.kafka_config["max_request_size"]
            )
            
            # Process results
            analysis_tasks = {}
            
            # Start analysis for all successful crawls
            for url, result in results.items():
                if result.get("success", False):
                    if self.content_analyzer:
                        analysis_task = self.content_analyzer.process_webpage(url, result.get("html", ""))
                        analysis_tasks[url] = {
                            "task": analysis_task,
                            "result": result,
                            "start_time": datetime.now()
                        }
                        if verbose:
                            print(f"Started analysis for {url}")
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
                                "session_id": session_id,
                                "content_type": content_type,
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
                            if verbose:
                                print(f"Successfully stored data for {url}")
                            # Add to metadata list (only the metadata portion)
                            metadata_list.append(website_data["metadata"])
                        except Exception as e:
                            if verbose:
                                print(f"Error storing website data: {e}")
                            metadata_list.append({
                                "url": url,
                                "session_id": session_id,
                                "thread_id": thread_id,
                                "error": str(e),
                                "success": False,
                                "crawled_at": datetime.now().isoformat()
                            })
                else:
                    # Add failed entry to metadata list
                    if verbose:
                        print(f"Failed to crawl {url}")
                        if "error" in result:
                            print(f"Error: {result['error']}")
                    
                    metadata_list.append({
                        "url": url,
                        "session_id": session_id,
                        "thread_id": thread_id,
                        "error": result.get("error", "Unknown error"),
                        "success": False,
                        "crawled_at": datetime.now().isoformat()
                    })
            
            # Process results and store them for URLs that had analysis tasks
            if self.content_analyzer and analysis_tasks:
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
                                "url": url,
                                "session_id": session_id,
                                "content_type": content_type,
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
                            if verbose:
                                print(f"Successfully stored data for {url}")
                        except Exception as e:
                            if verbose:
                                print(f"Error storing website data: {e}")
                            website_data["metadata"]["error"] = str(e)
                        
                        # Add to metadata list (only the metadata portion)
                        metadata_list.append(website_data["metadata"])
                        
                    except Exception as e:
                        # Add failed entry to metadata list
                        if verbose:
                            print(f"Error processing {url}: {e}")
                        metadata_list.append({
                            "url": url,
                            "session_id": session_id,
                            "thread_id": thread_id,
                            "error": str(e),
                            "success": False,
                            "crawled_at": datetime.now().isoformat()
                        })
            
            return metadata_list
            
        finally:
            # Close database connection
            cursor.close()
            conn.close()

    @staticmethod
    async def demo():
        """Run a demonstration of the OpenCrawl library"""
        print("=" * 60)
        print("OPENCRAWL LIBRARY DEMO")
        print("=" * 60)
        
        # Get API key from environment
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("Warning: GROQ_API_KEY environment variable not set!")
            print("Content analysis will be skipped.")
        
        # Initialize OpenCrawl with content analyzer if API key is available
        crawler = OpenCrawl(
            content_analyzer_config={"api_key": api_key} if api_key else None
        )
        
        # Test URLs
        test_urls = [
            "https://stackoverflow.com/questions/21020347/how-can-i-send-large-messages-with-kafka-over-15mb",
        ]
        
        print(f"\nProcessing {len(test_urls)} URLs...")
        
        # Process URLs
        results = await crawler.process_urls(
            urls=test_urls,
            verbose=True
        )
        
        print("\nResults Summary:")
        print("=" * 50)
        for i, result in enumerate(results):
            print(f"Result {i+1}:")
            print(f"  URL: {result.get('url')}")
            print(f"  Success: {result.get('success', result.get('crawl_info', {}).get('success', False))}")
            
            content_analysis = result.get("content_analysis")
            if content_analysis:
                print(f"  Title: {content_analysis.get('title', 'Unknown')}")
                print(f"  Topics: {', '.join(content_analysis.get('main_topics', ['None']))}")
                print(f"  Summary: {content_analysis.get('summary', 'None')[:100]}...")
            print("-" * 40)
        
        print("\nDEMO COMPLETED")

# Example usage
if __name__ == "__main__":
    asyncio.run(OpenCrawl.demo()) 
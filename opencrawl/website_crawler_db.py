#!/usr/bin/env python
"""
Website crawler database script using satya for validation and psycopg2 for PostgreSQL connectivity.
This handles the storage and validation of website data collected by multiple users.
"""
import os
import sys
import uuid
import json
import time
from typing import List, Dict, Optional, Union, Literal, Any
from datetime import datetime
from enum import Enum
from uuid import UUID
import psycopg2
import psycopg2.extensions
from psycopg2.extras import execute_values, Json

# Register UUID type with psycopg2
psycopg2.extensions.register_adapter(uuid.UUID, lambda u: psycopg2.extensions.QuotedString(str(u)))

# Import satya for validation
from satya import StreamValidator, Model, Field

# Configuration
POSTGRES_CONNECTION_STRING = os.environ.get(
    "POSTGRES_CONNECTION_STRING", 
    "postgresql://postgres:postgres@postgres:5432/opencrawl"
)

# Models for validation
class WebsiteType(str, Enum):
    """Enum for different website types"""
    NEWS = "news"
    BLOG = "blog"
    ECOMMERCE = "ecommerce"
    SOCIAL = "social_media"
    DOCUMENTATION = "documentation"
    ACADEMIC = "academic"
    CORPORATE = "corporate"
    OTHER = "other"

class WebsiteData(Model):
    """Model for validating website data"""
    url: str = Field(
        url=True,
        description="Website URL"
    )
    raw_html: str = Field(
        description="Raw HTML content of the website"
    )
    website_summary: Optional[str] = Field(
        required=False,
        description="Summary of the website content"
    )
    thread_id: UUID = Field(
        pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        description="Thread UUID v4"
    )
    website_type: WebsiteType = Field(
        description="Type of website"
    )
    user_id: UUID = Field(
        pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        description="User UUID v4"
    )
    crawled_at: datetime = Field(
        description="Timestamp when the website was crawled"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        required=False,
        description="Additional metadata about the website"
    )

def setup_database():
    """Connect to PostgreSQL and set up tables"""
    try:
        # Connect to PostgreSQL using connection string
        print(f"Connecting to PostgreSQL with connection string: {POSTGRES_CONNECTION_STRING}")
        conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        cursor = conn.cursor()
        
        # Debug: Check if we can execute a simple query
        cursor.execute("SELECT current_database(), current_schema()")
        db_info = cursor.fetchone()
        print(f"Connected to database: {db_info[0]}, schema: {db_info[1]}")
        
        # Create extensions
        cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS \"btree_gin\"")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS \"pg_trgm\"")
        
        # Create users table
        print("Creating users table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.crawler_users (
                user_id UUID PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                email VARCHAR(255) UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create threads table
        print("Creating threads table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.crawler_threads (
                thread_id UUID PRIMARY KEY,
                thread_name VARCHAR(255) NOT NULL,
                user_id UUID NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES public.crawler_users(user_id)
            )
        """)
        
        # Create websites table
        print("Creating websites table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.crawler_websites (
                id SERIAL PRIMARY KEY,
                url TEXT NOT NULL,
                raw_html TEXT,
                website_summary TEXT,
                thread_id UUID NOT NULL,
                website_type VARCHAR(50) NOT NULL,
                user_id UUID NOT NULL,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB,
                FOREIGN KEY (thread_id) REFERENCES public.crawler_threads(thread_id),
                FOREIGN KEY (user_id) REFERENCES public.crawler_users(user_id)
            )
        """)
        
        # Create indexes
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_website_url ON public.crawler_websites(url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_website_thread ON public.crawler_websites(thread_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_website_user ON public.crawler_websites(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_website_type ON public.crawler_websites(website_type)")
        
        conn.commit()
        print("Database tables initialized")
        return conn, cursor
    
    except Exception as e:
        print(f"❌ Error setting up PostgreSQL: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def create_user(conn, cursor, username, email):
    """Create a new user in the database"""
    try:
        user_id = uuid.uuid4()
        cursor.execute(
            "INSERT INTO public.crawler_users (user_id, username, email) VALUES (%s, %s, %s) RETURNING user_id",
            (user_id, username, email)
        )
        conn.commit()
        user_id_str = str(user_id)
        print(f"User created with ID: {user_id_str}")
        return user_id_str
    except Exception as e:
        print(f"Error creating user: {e}")
        conn.rollback()
        return None

def create_thread(conn, cursor, title, user_id, thread_id=None):
    """Create a new thread in the database with optional thread_id"""
    try:
        # Ensure user_id is a valid UUID
        try:
            user_id_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            print(f"Invalid user_id format: {user_id}")
            return None
            
        if thread_id is None:
            thread_id_uuid = uuid.uuid4()
            thread_id_str = str(thread_id_uuid)
        else:
            # Ensure thread_id is a valid UUID
            try:
                thread_id_uuid = uuid.UUID(thread_id) if isinstance(thread_id, str) else thread_id
                thread_id_str = str(thread_id_uuid)
            except ValueError:
                print(f"Invalid thread_id format: {thread_id}")
                return None
        
        cursor.execute(
            "INSERT INTO public.crawler_threads (thread_id, thread_name, user_id) VALUES (%s, %s, %s) RETURNING thread_id",
            (thread_id_uuid, title, user_id_uuid)
        )
        conn.commit()
        print(f"Thread created with ID: {thread_id_str}")
        return thread_id_str
    except Exception as e:
        print(f"Error creating thread: {e}")
        conn.rollback()
        return None

def store_website_data(conn, cursor, website_data):
    """Validate and store website data in the database"""
    try:
        # Convert string IDs to UUIDs if needed
        if "thread_id" in website_data and isinstance(website_data["thread_id"], str):
            try:
                website_data["thread_id"] = uuid.UUID(website_data["thread_id"])
            except ValueError:
                print(f"Invalid thread_id format: {website_data['thread_id']}")
                return False
                
        if "user_id" in website_data and isinstance(website_data["user_id"], str):
            try:
                website_data["user_id"] = uuid.UUID(website_data["user_id"])
            except ValueError:
                print(f"Invalid user_id format: {website_data['user_id']}")
                return False
        
        # Validate using satya
        validator = WebsiteData.validator()
        result = validator.validate(website_data)
        
        if not result.is_valid:
            print("❌ Invalid website data:")
            for error in result.errors:
                print(f"  Error in {error.field}: {error.message}")
            return False
        
        # If valid, insert into database
        cursor.execute(
            """
            INSERT INTO public.crawler_websites 
            (url, raw_html, website_summary, thread_id, website_type, user_id, crawled_at, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                website_data["url"],
                website_data["raw_html"],
                website_data.get("website_summary"),
                website_data["thread_id"],
                website_data["website_type"],
                website_data["user_id"],
                website_data.get("crawled_at", datetime.now()),
                Json(website_data.get("metadata", {}))
            )
        )
        website_id = cursor.fetchone()[0]
        conn.commit()
        print(f"✅ Website data stored with ID: {website_id}")
        return website_id
    except Exception as e:
        print(f"❌ Error storing website data: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return None

def get_websites_by_thread(conn, cursor, thread_id):
    """Retrieve all websites for a specific thread"""
    try:
        cursor.execute(
            """
            SELECT id, url, website_summary, website_type, crawled_at
            FROM public.crawler_websites
            WHERE thread_id = %s
            ORDER BY crawled_at DESC
            """,
            (thread_id,)
        )
        websites = cursor.fetchall()
        return websites
    except Exception as e:
        print(f"Error retrieving websites: {e}")
        return []

def get_websites_by_user(conn, cursor, user_id):
    """Retrieve all websites crawled by a specific user"""
    try:
        cursor.execute(
            """
            SELECT id, url, website_summary, website_type, thread_id, crawled_at
            FROM public.crawler_websites
            WHERE user_id = %s
            ORDER BY crawled_at DESC
            """,
            (user_id,)
        )
        websites = cursor.fetchall()
        return websites
    except Exception as e:
        print(f"Error retrieving websites: {e}")
        return []

def thread_exists(conn, cursor, thread_id):
    """Check if a thread exists in the database"""
    try:
        # Ensure thread_id is a valid UUID
        try:
            thread_id_uuid = uuid.UUID(thread_id) if isinstance(thread_id, str) else thread_id
        except ValueError:
            print(f"Invalid thread_id format: {thread_id}")
            return False
            
        cursor.execute(
            "SELECT 1 FROM public.crawler_threads WHERE thread_id = %s",
            (thread_id_uuid,)
        )
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"Error checking thread existence: {e}")
        return False

def run_demo():
    """Run a demonstration of the database operations"""
    print("=" * 60)
    print("WEBSITE CRAWLER DATABASE DEMO")
    print("=" * 60)
    
    # Set up database
    conn, cursor = setup_database()
    if not conn or not cursor:
        print("Failed to set up database, exiting")
        return False
    
    try:
        # Create demo users
        print("\nCreating demo users...")
        user1_id = create_user(conn, cursor, "alice_researcher", "alice@example.com")
        user2_id = create_user(conn, cursor, "bob_analyst", "bob@example.com")
        user3_id = create_user(conn, cursor, "charlie_crawler", "charlie@example.com")
        
        # Create threads
        print("\nCreating threads...")
        thread1_id = create_thread(conn, cursor, "AI Research Papers", user1_id)
        thread2_id = create_thread(conn, cursor, "Technology News", user2_id)
        thread3_id = create_thread(conn, cursor, "Programming Tutorials", user3_id)
        
        # Store website data
        print("\nStoring website data...")
        
        # Example website data for validation
        website1 = {
            "url": "https://example.com/ai-research",
            "raw_html": "<html><body><h1>AI Research</h1><p>Latest findings in AI</p></body></html>",
            "website_summary": "Website about the latest AI research findings",
            "thread_id": thread1_id,
            "website_type": "academic",
            "user_id": user1_id,
            "crawled_at": datetime.now(),
            "metadata": {
                "keywords": ["AI", "machine learning", "research"],
                "language": "en"
            }
        }
        
        website2 = {
            "url": "https://example.com/tech-news",
            "raw_html": "<html><body><h1>Tech News</h1><p>Latest in technology</p></body></html>",
            "website_summary": "Latest technology news and updates",
            "thread_id": thread2_id,
            "website_type": "news",
            "user_id": user2_id,
            "crawled_at": datetime.now(),
            "metadata": {
                "keywords": ["technology", "news", "updates"],
                "language": "en"
            }
        }
        
        website3 = {
            "url": "https://example.com/python-tutorial",
            "raw_html": "<html><body><h1>Python Tutorial</h1><p>Learn Python programming</p></body></html>",
            "website_summary": "Comprehensive Python programming tutorial",
            "thread_id": thread3_id,
            "website_type": "documentation",
            "user_id": user3_id,
            "crawled_at": datetime.now(),
            "metadata": {
                "keywords": ["python", "programming", "tutorial"],
                "language": "en"
            }
        }
        
        # Store data
        store_website_data(conn, cursor, website1)
        store_website_data(conn, cursor, website2)
        store_website_data(conn, cursor, website3)
        
        # Invalid data example
        print("\nTesting validation with invalid data...")
        invalid_website = {
            "url": "not-a-valid-url",  # Invalid URL
            "raw_html": "<html><body>Test</body></html>",
            "thread_id": "not-a-valid-uuid",  # Invalid UUID
            "website_type": "invalid_type",  # Invalid enum value
            "user_id": user1_id
        }
        
        store_website_data(conn, cursor, invalid_website)
        
        # Retrieve and display data
        print("\nRetrieving websites by thread...")
        thread1_websites = get_websites_by_thread(conn, cursor, thread1_id)
        print(f"Thread 1 ({thread1_id}) websites:")
        for website in thread1_websites:
            print(f"  - {website[1]} ({website[3]}) - {website[2]}")
        
        print("\nRetrieving websites by user...")
        user1_websites = get_websites_by_user(conn, cursor, user1_id)
        print(f"User 1 ({user1_id}) websites:")
        for website in user1_websites:
            print(f"  - {website[1]} ({website[3]}) - Thread: {website[4]}")
        
        print("\nDemo completed successfully!")
        return True
        
    except Exception as e:
        print(f"\nError in demo: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Close connection
        cursor.close()
        conn.close()
        print("Database connection closed")

if __name__ == "__main__":
    try:
        success = run_demo()
        if success:
            print("\nDEMO COMPLETED SUCCESSFULLY ✅")
            sys.exit(0)
        else:
            print("\nDEMO COMPLETED WITH ERRORS ❌")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 
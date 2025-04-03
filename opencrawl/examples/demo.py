#!/usr/bin/env python3
import asyncio
import os
import sys
import time
import requests
import json
from kafka import KafkaConsumer
import threading
import uuid

# Add opencrawl to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Set up environment variables for demo
os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5432/opencrawl"
os.environ["KAFKA_BROKERS"] = "localhost:9092"  # This now points to Redpanda

# Flag to track if Kafka messages were received
kafka_messages_received = False
# Generate a unique session ID
session_id = str(uuid.uuid4())

def listen_to_kafka():
    """Listen to Kafka/Redpanda messages in a separate thread"""
    global kafka_messages_received
    
    print(f"Starting Kafka consumer for session: {session_id}")
    print("Waiting for messages from Redpanda...")
    
    try:
        # Create a Kafka consumer
        consumer = KafkaConsumer(
            "pathik_crawl_data",  # Topic name
            bootstrap_servers=["localhost:9092"],  # Redpanda broker
            auto_offset_reset="latest",  # Start from the latest message
            enable_auto_commit=True,
            group_id=f"demo-consumer-{session_id}",  # Unique consumer group
            value_deserializer=lambda x: json.loads(x.decode("utf-8"))
        )
        
        # Listen for messages
        message_count = 0
        for message in consumer:
            message_data = message.value
            
            # Check if this message is from our current session
            if message_data.get("session") == session_id:
                message_count += 1
                print(f"\n✅ Received Kafka message #{message_count} for URL: {message_data.get('url', 'Unknown')}")
                
                # Mark that we received Kafka messages
                kafka_messages_received = True
                
                # If we've received messages for all URLs, we can stop
                if message_count >= 2:  # We're crawling 2 URLs
                    print("✅ Successfully received all messages from Redpanda!")
                    break
        
        consumer.close()
        
    except Exception as e:
        print(f"❌ Error listening to Kafka: {e}")

async def run_demo():
    # Start Kafka listener in a separate thread
    kafka_thread = threading.Thread(target=listen_to_kafka)
    kafka_thread.daemon = True
    kafka_thread.start()
    
    # Give the consumer time to connect
    await asyncio.sleep(2)
    
    # Test URLs
    urls = [
        "https://www.example.com",
        "https://news.ycombinator.com"
    ]
    
    print(f"\nProcessing {len(urls)} URLs...")
    
    # Use the local API instead of direct Kafka connection
    response = requests.post(
        "http://localhost:8000/crawl",
        json={"urls": urls, "user_id": session_id},  # Add session_id as user_id
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        results = response.json()
        print("\nResults Summary from API:")
        print("=" * 50)
        for result in results.get("results", []):
            print(f"\nURL: {result.get('url')}")
            content_analysis = result.get("content_analysis", {})
            if content_analysis:
                print(f"Title: {content_analysis.get('title', 'Unknown')}")
                print(f"Summary: {content_analysis.get('summary', '')[:100]}...")
    else:
        print(f"Error: {response.status_code} - {response.text}")
    
    # Wait for Kafka messages to be processed
    print("\nWaiting for Kafka messages (max 15 seconds)...")
    for _ in range(15):
        if kafka_messages_received:
            break
        await asyncio.sleep(1)
    
    if not kafka_messages_received:
        print("❌ No Kafka messages received after 15 seconds.")
        print("The system might not be using Redpanda/Kafka correctly.")
    
    # Let the Kafka listener finish
    await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(run_demo()) 
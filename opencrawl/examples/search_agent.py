import requests
import json
import asyncio
import os
import dotenv
from typing import List, Dict, Any
from bhumi.base_client import BaseLLMClient, LLMConfig

# Load environment variables
dotenv.load_dotenv()

# API keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")  # You'll need to get this from Brave

class ResearchAgent:
    def __init__(self):
        # Configure LLM client
        config = LLMConfig(
            api_key=GROQ_API_KEY,
            model="groq/llama-3.3-70b-versatile",
            debug=False,
            max_retries=3,
            max_tokens=32768

        )
        self.llm_client = BaseLLMClient(config, debug=False)
        
    async def generate_questions(self, query: str) -> List[str]:
        """Generate 3 research questions based on the user query."""
        prompt = [
            {"role": "system", "content": "You are a research assistant. Generate 3 specific questions that would help research the user's query in depth. Make the questions clear and specific."},
            {"role": "user", "content": f"Generate 3 specific questions to research this query: {query}"}
        ]
        
        response = await self.llm_client.completion(prompt)
        questions_text = response['text']
        
        # Parse the questions from the response
        questions = []
        for line in questions_text.split('\n'):
            line = line.strip()
            if line and (line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
                questions.append(line[3:].strip())
        
        # If we didn't get exactly 3 questions, handle it
        if len(questions) != 3:
            # Simple fallback - split by numbers or just take the first 3 sentences
            import re
            questions = re.findall(r'\d+\.\s*(.*?)(?=\d+\.|\Z)', questions_text)
            if len(questions) < 3:
                sentences = [s.strip() for s in re.split(r'[.!?]+', questions_text) if s.strip()]
                questions = questions + sentences[:3-len(questions)]
            questions = questions[:3]  # Ensure we have at most 3
            
        return questions
    
    async def brave_search(self, query: str, count: int = 5) -> List[str]:
        """Perform a search using Brave Search API and return top URLs."""
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": BRAVE_API_KEY
        }
        params = {
            "q": query,
            "count": count
        }
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error searching Brave: {response.status_code} - {response.text}")
            return []
            
        results = response.json()
        urls = [web["url"] for web in results.get("web", {}).get("results", [])[:count]]
        return urls
    
    async def crawl_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Crawl URLs using opencrawl API."""
        url = "https://opencrawl.p2w.app/crawl"
        payload = json.dumps({"urls": urls})
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code != 200:
            print(f"Error crawling: {response.status_code} - {response.text}")
            return []
            
        # Return the "results" list from the response
        data = response.json()
        return data.get("results", [])
    
    async def generate_response(self, query: str, crawl_data: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive response based on crawled data."""
        # Prepare context from crawled data
        context = ""
        sources = []
        
        for i, item in enumerate(crawl_data):
            # Extract data from the correct nested structure
            content_analysis = item.get("content_analysis", {})
            title = content_analysis.get("title", "Unknown Title")
            summary = content_analysis.get("summary", "")
            key_points = content_analysis.get("key_points", [])
            url = item.get("url", "")
            
            # Add to sources for citation
            source_id = i + 1
            sources.append({"id": source_id, "title": title, "url": url})
            
            # Format the content
            context += f"Source {source_id} - {title} ({url}):\n"
            context += f"Summary: {summary}\n"
            if key_points:
                context += "Key points:\n"
                for point in key_points:
                    context += f"- {point}\n"
            context += "\n"
        
        prompt = [
            {"role": "system", "content": """You are a research assistant. Use the provided information to answer the user's query thoroughly and accurately. 
Format your response in clean markdown with proper headings, bullet points, and formatting. 
IMPORTANT: For any information you use, cite the source using the format (Source X) where X is the source number.
At the end of your response, include a References section that lists all sources with their titles and URLs as clickable markdown links.
Make sure URLs are properly formatted as markdown links."""},
            {"role": "user", "content": f"Based on the following information, please answer this query: {query}\n\nInformation:\n{context}"}
        ]
        
        response = await self.llm_client.completion(prompt)
        
        # If the LLM doesn't include URLs properly, ensure they're properly formatted
        formatted_response = response['text']
        
        # Add a References section if not already present
        if "References:" not in formatted_response and "REFERENCES" not in formatted_response.upper():
            formatted_response += "\n\n## References\n"
            for source in sources:
                formatted_response += f"Source {source['id']}: [{source['title']}]({source['url']})\n"
        
        return formatted_response
    
    async def research(self, query: str) -> str:
        """Conduct full research process on a query."""
        print(f"Starting research on: {query}")
        
        # Step 1: Generate subquestions
        questions = await self.generate_questions(query)
        print(f"Generated questions: {questions}")
        
        # Step 2: Search for each question
        all_urls = []
        for question in questions:
            urls = await self.brave_search(question)
            print(f"Question: {question} - Found {len(urls)} URLs")
            all_urls.extend(urls)
        
        # Step 3: Crawl all URLs
        print(f"Crawling {len(all_urls)} URLs...")
        crawl_data = await self.crawl_urls(all_urls)
        print(f"Crawled {len(crawl_data)} pages successfully")
        
        # Step 4: Generate final response
        response = await self.generate_response(query, crawl_data)
        
        return response

async def main():
    # Initialize the research agent
    agent = ResearchAgent()
    
    # Example usage
    query = input("Enter your research query: ")
    result = await agent.research(query)
    
    print("\n----- RESEARCH RESULTS -----\n")
    print(result)
    # Save results to markdown file
    output_dir = "research_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename from query
    filename = query.lower().replace(" ", "_")[:50] + ".md"
    output_path = os.path.join(output_dir, filename)
    
    # Write results to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Research Results: {query}\n\n")
        f.write(result)
    
    print(f"\nResults saved to: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())

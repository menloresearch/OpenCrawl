# OpenCrawl

This project integrates multiple AI services to create a research assistant that:
1. Takes user queries
2. Generates specific research questions
3. Searches the web for relevant information
4. Crawls websites to gather detailed content
5. Synthesizes the information into comprehensive responses

## Components

- **Backend**: FastAPI server that handles the research process
- **Frontend**: Next.js application with shadcn/ui components
- **Search**: Uses Brave Search API for web searches
- **Crawling**: Uses OpenCrawl for website content extraction
- **LLM**: Uses Groq API for text generation

## Setup

### Prerequisites

- Python 3.8+
- Node.js and npm
- API keys for:
  - Groq (`GROQ_API_KEY`)
  - Brave Search (`BRAVE_API_KEY`)

### Installation

1. Create a `.env` file in the project root with your API keys:

```
GROQ_API_KEY=your_groq_api_key
BRAVE_API_KEY=your_brave_api_key
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Install frontend dependencies:

```bash
cd frontend
npm install
```

## Running the Application

For development, you can use the provided script to run both the backend and frontend:

```bash
./run_dev.sh
```

This will start:
- Backend on http://localhost:8000
- Frontend on http://localhost:3000

Alternatively, you can run them separately:

### Backend Only

```bash
python api.py
```

### Frontend Only

```bash
cd frontend
npm run dev
```

## API Endpoints

- `POST /research` - Start a new research task
- `GET /research/{task_id}` - Get status and results of a research task

## Usage

1. Open the frontend in your browser (http://localhost:3000)
2. Enter your research query in the input field
3. Click "Research" and wait for the results
4. View the generated questions and final research results in the tabs 
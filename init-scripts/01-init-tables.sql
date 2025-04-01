-- OpenCrawl Database Initialization Script
-- Creates the necessary tables for the OpenCrawl Library

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schema
CREATE SCHEMA IF NOT EXISTS public;

-- Create users table
CREATE TABLE IF NOT EXISTS public.crawler_users (
    user_id UUID PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create threads table
CREATE TABLE IF NOT EXISTS public.crawler_threads (
    thread_id UUID PRIMARY KEY,
    thread_name VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES public.crawler_users(user_id)
);

-- Create website data table
CREATE TABLE IF NOT EXISTS public.crawler_websites (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    website_type VARCHAR(255),
    thread_id UUID NOT NULL,
    user_id UUID NOT NULL,
    raw_html TEXT,
    website_summary TEXT,
    crawled_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (thread_id) REFERENCES public.crawler_threads(thread_id),
    FOREIGN KEY (user_id) REFERENCES public.crawler_users(user_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_website_url ON public.crawler_websites(url);
CREATE INDEX IF NOT EXISTS idx_website_thread_id ON public.crawler_websites(thread_id);
CREATE INDEX IF NOT EXISTS idx_website_user_id ON public.crawler_websites(user_id);
CREATE INDEX IF NOT EXISTS idx_website_metadata ON public.crawler_websites USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_website_type ON public.crawler_websites(website_type);

-- Create a basic search index using trigram matching for website content
CREATE INDEX IF NOT EXISTS idx_website_summary_trgm ON public.crawler_websites USING GIN (website_summary gin_trgm_ops);

-- Create a default test user
INSERT INTO public.crawler_users (user_id, username, email)
VALUES
    ('11111111-1111-4111-a111-111111111111', 'testuser', 'test@opencrawl.org')
ON CONFLICT (user_id) DO NOTHING;

-- Create a default test thread
INSERT INTO public.crawler_threads (thread_id, thread_name, user_id)
VALUES
    ('22222222-2222-4222-a222-222222222222', 'Test Thread', '11111111-1111-4111-a111-111111111111')
ON CONFLICT (thread_id) DO NOTHING; 
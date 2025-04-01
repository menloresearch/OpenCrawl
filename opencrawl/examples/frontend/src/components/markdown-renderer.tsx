import React from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';
import remarkGfm from 'remark-gfm';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  return (
    <div className={`prose dark:prose-invert max-w-none ${className}`}>
      <ReactMarkdown
        rehypePlugins={[rehypeRaw, rehypeSanitize]}
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ node, ...props }) => (
            <a 
              {...props} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 hover:underline"
            />
          ),
          p: ({ node, ...props }) => (
            <p {...props} className="my-2" />
          ),
          ul: ({ node, ...props }) => (
            <ul {...props} className="list-disc pl-6 my-2" />
          ),
          ol: ({ node, ...props }) => (
            <ol {...props} className="list-decimal pl-6 my-2" />
          ),
          li: ({ node, ...props }) => (
            <li {...props} className="my-1" />
          ),
          h1: ({ node, ...props }) => (
            <h1 {...props} className="text-2xl font-bold my-4" />
          ),
          h2: ({ node, ...props }) => (
            <h2 {...props} className="text-xl font-bold my-3" />
          ),
          h3: ({ node, ...props }) => (
            <h3 {...props} className="text-lg font-bold my-2" />
          ),
          blockquote: ({ node, ...props }) => (
            <blockquote {...props} className="border-l-4 border-gray-200 pl-4 my-2 italic" />
          ),
          code: ({ node, inline, ...props }) => (
            inline 
              ? <code {...props} className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-sm" />
              : <code {...props} className="block bg-gray-100 dark:bg-gray-800 p-3 rounded text-sm overflow-x-auto" />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
} 
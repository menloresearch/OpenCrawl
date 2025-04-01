"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { FileIcon, HomeIcon } from "lucide-react";

interface ResearchResult {
  id: string;
  title: string;
  date: string;
}

export default function ResultsPage() {
  const [results, setResults] = useState<ResearchResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchResults() {
      try {
        // This would normally fetch from an API, but for demo we'll create mock data
        // In a real implementation, you'd fetch from your backend
        const mockResults = [
          { id: "what_is_machine_learning", title: "What is Machine Learning", date: "2024-03-28" },
          { id: "how_does_cryptocurrency_work", title: "How does Cryptocurrency work", date: "2024-03-27" },
          { id: "benefits_of_meditation", title: "Benefits of Meditation", date: "2024-03-26" },
        ];
        
        setResults(mockResults);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching results:", error);
        setLoading(false);
      }
    }

    fetchResults();
  }, []);

  return (
    <div className="container mx-auto py-10">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">OpenCrawl Results</h1>
        <Link href="/">
          <Button variant="outline">
            <HomeIcon className="mr-2 h-4 w-4" />
            Back to OpenCrawl
          </Button>
        </Link>
      </div>

      {loading ? (
        <p>Loading research results...</p>
      ) : results.length === 0 ? (
        <Card>
          <CardContent className="py-8">
            <p className="text-center text-muted-foreground">No research results found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {results.map((result) => (
            <Link href={`/results/${result.id}`} key={result.id}>
              <Card className="h-full hover:bg-accent/50 transition-colors cursor-pointer">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <FileIcon className="mr-2 h-5 w-5" />
                    {result.title}
                  </CardTitle>
                  <CardDescription>Created on {result.date}</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    Click to view research results
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
} 
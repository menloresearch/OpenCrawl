"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Loader2, Search, Globe, BookOpen, Brain } from "lucide-react";
import { startResearch, getResearchStatus, type ResearchStatus } from "./actions";
import { MarkdownRenderer } from "@/components/markdown-renderer";
import Link from "next/link";
import { Progress } from "@/components/ui/progress";

export default function Home() {
  const [query, setQuery] = useState("");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState("idle");
  const [questions, setQuestions] = useState<string[]>([]);
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const [progressValue, setProgressValue] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);

  const researchSteps = [
    { icon: Brain, text: "Generating research questions..." },
    { icon: Search, text: "Searching for relevant information..." },
    { icon: Globe, text: "Crawling websites for content..." },
    { icon: BookOpen, text: "Synthesizing information..." },
  ];

  // Poll for research status when taskId is set
  useEffect(() => {
    if (!taskId) return;

    const intervalId = setInterval(async () => {
      try {
        const data = await getResearchStatus(taskId);
        setStatus(data.status);
        
        // Update progress based on status
        if (data.status === "pending") {
          setCurrentStep(0);
          setProgressValue(15);
        } else if (data.status === "questions_ready") {
          setCurrentStep(1);
          setProgressValue(40);
        } else if (data.status === "completed") {
          setCurrentStep(3);
          setProgressValue(100);
        }
        
        if (data.questions) {
          setQuestions(data.questions);
          if (currentStep < 1) {
            setCurrentStep(1);
            setProgressValue(40);
          }
        }
        
        if (data.result) {
          setResult(data.result);
          setCurrentStep(3);
          setProgressValue(100);
          clearInterval(intervalId);
        }
        
        if (data.status === "failed") {
          setError("Research failed. Please try again.");
          clearInterval(intervalId);
        }
        
        if (data.status === "completed") {
          clearInterval(intervalId);
        }
      } catch (err: any) {
        console.error("Error polling research status:", err);
        setError(err.message);
        clearInterval(intervalId);
      }
    }, 2000);

    // Simulate progress for better UX
    const progressInterval = setInterval(() => {
      setProgressValue((prev) => {
        if (prev >= 95) return prev;
        if (status === "pending" && prev < 35) return prev + 1;
        if (status === "questions_ready" && prev < 75) return prev + 0.5;
        return prev;
      });

      if (status === "pending" && progressValue > 25 && currentStep < 1) {
        setCurrentStep(1);
      } else if (status === "questions_ready" && progressValue > 60 && currentStep < 2) {
        setCurrentStep(2);
      }
    }, 300);

    return () => {
      clearInterval(intervalId);
      clearInterval(progressInterval);
    };
  }, [taskId, status, progressValue, currentStep]);

  const handleStartResearch = async () => {
    if (!query.trim()) {
      setError("Please enter a research query");
      return;
    }

    setError("");
    setStatus("pending");
    setResult("");
    setQuestions([]);
    setProgressValue(5);
    setCurrentStep(0);
    
    try {
      const data = await startResearch(query);
      setTaskId(data.task_id);
    } catch (err: any) {
      console.error("Error starting research:", err);
      setError(err.message);
      setStatus("idle");
    }
  };

  return (
    <div className="container mx-auto py-10">
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle className="text-2xl">OpenCrawl</CardTitle>
              <CardDescription>
                Ask a question and our AI will research it for you using multiple sources.
              </CardDescription>
            </div>
            <Link href="/results">
              <Button variant="outline" size="sm">
                View All Results
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-end space-x-2 mb-6">
            <div className="flex-1">
              <Input
                placeholder="Enter your research question..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full"
                disabled={status !== "idle" && status !== "completed" && status !== "failed"}
              />
            </div>
            <Button 
              onClick={handleStartResearch} 
              disabled={status !== "idle" && status !== "completed" && status !== "failed"}
            >
              {status === "pending" || status === "questions_ready" ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Researching...
                </>
              ) : "Research"}
            </Button>
          </div>

          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {(status === "pending" || status === "questions_ready") && (
            <div className="mb-6">
              <div className="flex justify-between mb-2 text-sm text-muted-foreground">
                <span>Researching...</span>
                <span>{Math.round(progressValue)}%</span>
              </div>
              <Progress value={progressValue} className="mb-4" />
              
              <div className="space-y-3">
                {researchSteps.map((step, idx) => {
                  const StepIcon = step.icon;
                  return (
                    <div 
                      key={idx} 
                      className={`flex items-center gap-3 p-3 rounded-md transition-colors ${
                        currentStep === idx 
                          ? "bg-primary/10 text-primary"
                          : currentStep > idx 
                            ? "text-muted-foreground" 
                            : "text-muted-foreground/50"
                      }`}
                    >
                      <div className={`${currentStep === idx ? "animate-pulse" : ""}`}>
                        <StepIcon className="h-5 w-5" />
                      </div>
                      <div className="flex-1">
                        {step.text}
                      </div>
                      {currentStep === idx && (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {status !== "idle" && (
            <Tabs defaultValue="result" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="questions">Research Questions</TabsTrigger>
                <TabsTrigger value="result">Research Results</TabsTrigger>
              </TabsList>
              
              <TabsContent value="questions">
                <Card>
                  <CardHeader>
                    <CardTitle>Generated Questions</CardTitle>
                    <CardDescription>
                      These questions are being used to guide the research
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {questions.length > 0 ? (
                      <ol className="list-decimal pl-5 space-y-2">
                        {questions.map((q, i) => (
                          <li key={i} className="text-base">{q}</li>
                        ))}
                      </ol>
                    ) : (
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          <Skeleton className="h-4 w-4 rounded-full" />
                          <Skeleton className="h-4 w-full" />
                        </div>
                        <div className="flex items-center space-x-2">
                          <Skeleton className="h-4 w-4 rounded-full" />
                          <Skeleton className="h-4 w-full" />
                        </div>
                        <div className="flex items-center space-x-2">
                          <Skeleton className="h-4 w-4 rounded-full" />
                          <Skeleton className="h-4 w-full" />
                        </div>
                      </div>
                    )}
                  </CardContent>
                  <CardFooter className="text-sm text-muted-foreground">
                    Status: {status === "questions_ready" ? "Researching answers..." : status}
                  </CardFooter>
                </Card>
              </TabsContent>
              
              <TabsContent value="result">
                <Card>
                  <CardHeader>
                    <CardTitle>Research Results</CardTitle>
                    <CardDescription>
                      Comprehensive answer based on multiple sources
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {status === "completed" ? (
                      <MarkdownRenderer content={result} />
                    ) : (
                      <div className="space-y-4">
                        <Skeleton className="h-8 w-3/4" />
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-full" />
                        
                        <div className="py-2">
                          <Skeleton className="h-6 w-1/2 mb-2" />
                          <div className="pl-4 space-y-2">
                            <Skeleton className="h-4 w-full" />
                            <Skeleton className="h-4 w-full" />
                            <Skeleton className="h-4 w-3/4" />
                          </div>
                        </div>
                        
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-full" />
                        
                        <div className="py-2">
                          <Skeleton className="h-6 w-1/3 mb-2" />
                          <div className="pl-4 space-y-2">
                            <Skeleton className="h-4 w-full" />
                            <Skeleton className="h-4 w-full" />
                          </div>
                        </div>
                      </div>
                    )}
                  </CardContent>
                  <CardFooter className="text-sm text-muted-foreground">
                    {status === "completed" ? "Research completed" : "Researching..."}
                  </CardFooter>
                </Card>
              </TabsContent>
            </Tabs>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

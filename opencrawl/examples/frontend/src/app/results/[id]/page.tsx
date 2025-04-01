"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { MarkdownRenderer } from "@/components/markdown-renderer";
import { ChevronLeft, Download, FileText, BookOpen, Link as LinkIcon, List } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Skeleton } from "@/components/ui/skeleton";

export default function ResultDetailPage() {
  const params = useParams();
  const id = params.id as string;
  
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");
  
  useEffect(() => {
    async function fetchResult() {
      try {
        // In a real implementation, this would fetch from your backend API
        // For now, we'll simulate loading markdown content based on the ID
        
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Format the title for display
        const formattedTitle = id.replace(/_/g, " ")
          .split(" ")
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join(" ");
        
        setTitle(formattedTitle);
        
        // For demo purposes, we'll use the sample markdown content
        // In reality, you would fetch this from your API
        setContent(`# ${formattedTitle}

Autoregressive (AR) models are a type of statistical model used for time series analysis and forecasting. They predict future values based on a linear combination of past values, using the weighted sum of one or more prior values to forecast future trends (Source 5). The order of an AR model is characterized by the parameter p, which represents the number of lagged values used to predict future values (Source 2).

In an AR model, the future value of a variable is predicted based on its own past values, by regressing the variable on its own lagged values (Source 11). The model assumes that the future value of a time series is a function of past values, and that the relationship between past and future values is linear (Source 1).

The key points of autoregressive models can be summarized as follows:

* AR models predict future values based on a linear combination of past values (Source 1, Source 5, Source 9).
* The order of an AR model is crucial for accurate predictions, and it represents the number of lagged values used to predict future values (Source 2, Source 8, Source 9).
* AR models require the data to be stationary, meaning that the statistical properties of the data, such as the mean and variance, remain constant over time (Source 5, Source 6, Source 10).
* If the data is non-stationary, transformations such as differencing or logarithmic transformations can be applied to make the data stationary (Source 6, Source 10).

The mathematical formulation of an AR model can be represented as:

yt = β0 + β1yt-1 + β2yt-2 + … + βptyt-p + εt

where yt is the current value, yt-1, yt-2, …, yt-p are the past values, β0, β1, β2, …, βp are the coefficients, and εt is the error term (Source 2).

AR models have various applications in fields such as economics, finance, and weather forecasting, where they are used to predict future values based on historical data (Source 5, Source 11, Source 12). However, they also have limitations, such as the assumption that past values indicate future behavior, which may not always be accurate (Source 13).

To implement an AR model, the order of the model must be identified, and the coefficients must be estimated using methods such as the least squares method (Source 4, Source 8). The performance of the model can be evaluated using statistical measures such as mean squared error or mean absolute error (Source 8).

In conclusion, autoregressive models are a type of statistical model used for time series analysis and forecasting, which predict future values based on a linear combination of past values. They require the data to be stationary, and the order of the model must be identified to ensure accurate predictions. AR models have various applications in fields such as economics, finance, and weather forecasting, but also have limitations, such as the assumption that past values indicate future behavior.

## References

Source 1: [Autoregressive (AR) and Moving Average (MA) Models](https://www.datasciencebase.com/intermediate/statistics-probability/autoregressive-ar-and-moving-average-ma-models/)
Source 2: [Autoregressive moving-average model](https://en.wikipedia.org/wiki/Autoregressive_moving-average_model)
Source 5: [Understanding Autoregressive Models](https://www.ibm.com/think/topics/autoregressive-model)
Source 6: [Understanding Stationarity in Time Series Analysis](https://hex.tech/blog/stationarity-in-time-series/)
Source 8: [Time Series Analysis: Autoregressive Models](https://prof-frenzel.medium.com/kb-time-series-analysis-part-4-autoregressive-models-ed824838bd4c)
Source 9: [Autoregressive (AR) Model for Time Series Forecasting](https://www.geeksforgeeks.org/autoregressive-ar-model-for-time-series-forecasting/)
Source 10: [Forecasting: Principles and Practice - Stationarity](https://otexts.com/fpp2/stationarity.html)
Source 11: [Autoregressive Models](https://aws.amazon.com/what-is/autoregressive-models/)
Source 12: [Understanding Autoregressive (AR) Models](https://spotintelligence.com/2023/10/25/autoregressive-ar-models/)
Source 13: [Autoregressive Models - Investopedia](https://www.investopedia.com/terms/a/autoregressive.asp)
`);
        
        setLoading(false);
      } catch (err: any) {
        console.error("Error fetching research result:", err);
        setError(err.message || "Failed to load research result");
        setLoading(false);
      }
    }
    
    fetchResult();
  }, [id]);
  
  const handleDownload = () => {
    // Create a blob with the content
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    
    // Create a link and trigger download
    const a = document.createElement('a');
    a.href = url;
    a.download = `${id}.md`;
    document.body.appendChild(a);
    a.click();
    
    // Clean up
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  
  return (
    <div className="container mx-auto py-10">
      <div className="flex justify-between items-center mb-6">
        <Link href="/results">
          <Button variant="outline" size="sm">
            <ChevronLeft className="mr-2 h-4 w-4" />
            Back to Results
          </Button>
        </Link>
        
        <Button variant="outline" size="sm" onClick={handleDownload} disabled={loading}>
          <Download className="mr-2 h-4 w-4" />
          Download Markdown
        </Button>
      </div>
      
      {loading ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <FileText className="mr-2 h-5 w-5" />
              <Skeleton className="h-8 w-64" />
            </CardTitle>
            <CardDescription>
              <Skeleton className="h-4 w-40" />
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-card rounded-md p-6 space-y-6">
              {/* Title skeleton */}
              <div className="space-y-2">
                <Skeleton className="h-8 w-3/4" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
              </div>
              
              {/* Paragraph skeleton */}
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-4/5" />
              </div>
              
              {/* List skeleton */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <List className="h-5 w-5 text-muted-foreground" />
                  <Skeleton className="h-6 w-40" />
                </div>
                <div className="pl-5 space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-muted-foreground" />
                    <Skeleton className="h-4 w-full" />
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-muted-foreground" />
                    <Skeleton className="h-4 w-full" />
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-muted-foreground" />
                    <Skeleton className="h-4 w-5/6" />
                  </div>
                </div>
              </div>
              
              {/* Another paragraph skeleton */}
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
              
              {/* References skeleton */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-muted-foreground" />
                  <Skeleton className="h-6 w-32" />
                </div>
                <div className="pl-5 space-y-3">
                  <div className="flex items-center gap-2">
                    <LinkIcon className="h-4 w-4 text-muted-foreground" />
                    <Skeleton className="h-4 w-5/6" />
                  </div>
                  <div className="flex items-center gap-2">
                    <LinkIcon className="h-4 w-4 text-muted-foreground" />
                    <Skeleton className="h-4 w-4/6" />
                  </div>
                  <div className="flex items-center gap-2">
                    <LinkIcon className="h-4 w-4 text-muted-foreground" />
                    <Skeleton className="h-4 w-5/6" />
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex justify-between">
            <Skeleton className="h-4 w-64" />
          </CardFooter>
        </Card>
      ) : error ? (
        <Card>
          <CardContent className="py-8">
            <p className="text-center text-destructive">{error}</p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <FileText className="mr-2 h-5 w-5" />
              {title}
            </CardTitle>
            <CardDescription>
              OpenCrawl Research Results
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-card rounded-md p-6">
              <MarkdownRenderer content={content} />
            </div>
          </CardContent>
          <CardFooter className="flex justify-between">
            <p className="text-sm text-muted-foreground">
              This research was generated using OpenCrawl's AI-powered analysis of multiple sources.
            </p>
          </CardFooter>
        </Card>
      )}
    </div>
  );
} 
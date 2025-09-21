/*import { useState } from "react";
import Header from "@/components/Header";
import InputSection from "@/components/InputSection";
import ResultsSection from "@/components/ResultsSection";
import { useToast } from "@/hooks/use-toast";

const Index = () => {
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleAnalyze = async (type: string, data: string) => {
    setIsLoading(true);
    setResults(null);

    try {
      // Simulate API call with mock data
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const mockResult = {
        prediction: Math.random() > 0.5 ? "real" : "fake",
        confidence: Math.floor(Math.random() * 40) + 60, // 60-100%
        reasoning: `Based on our analysis of the ${type}, we found several indicators that suggest this content is ${Math.random() > 0.5 ? 'authentic' : 'potentially misleading'}. The language patterns, source credibility, and cross-reference checks have been evaluated.`,
        sources: [
          "Reuters Fact Check",
          "Associated Press",
          "Snopes.com",
          "PolitiFact"
        ]
      };

      setResults(mockResult);
      
      toast({
        title: "Analysis Complete",
        description: `Content analyzed successfully with ${mockResult.confidence}% confidence.`,
      });
    } catch (error) {
      toast({
        title: "Analysis Failed",
        description: "Unable to analyze the content. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-4 py-12 space-y-8">
        <div className="text-center mb-12">
          <h2 className="text-2xl font-semibold text-foreground mb-2">
            Combat Misinformation with AI
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Our advanced AI system analyzes content across multiple dimensions to help 
            identify potential misinformation and provide confidence ratings for your peace of mind.
          </p>
        </div>

        <InputSection onAnalyze={handleAnalyze} isLoading={isLoading} />
        
        <ResultsSection results={results} />
      </main>
    </div>
  );
};

export default Index;
*/

/*
import { useState } from "react";
import Header from "@/components/Header";
import InputSection from "@/components/InputSection";
import ResultsSection from "@/components/ResultsSection";
import { useToast } from "@/hooks/use-toast";
import { text } from "stream/consumers";

// Align with ResultsSection expected types
interface Result {
  prediction: "real" | "fake" | "uncertain";
  confidence: number;
  reasoning: string;
  sources: string[];
}

// Map backend verdict to frontend literal types
const mapVerdict = (verdict: string): "real" | "fake" | "uncertain" => {
  switch (verdict.toLowerCase()) {
    case "real":
      return "real";
    case "fake":
      return "fake";
    default:
      return "uncertain";
  }
};

const Index = () => {
  const [results, setResults] = useState<Result | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleAnalyze = async (type: string, data: string) => {
    setIsLoading(true);
    setResults(null);

    try {
      // Replace with deployed backend URL when live
      const response = await fetch("http://127.0.0.1:8000/verify_text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: data }),
      });

      if (!response.ok) throw new Error("Failed to fetch analysis");

      const backendResult = await response.json();

      const formattedResult: Result = {
        prediction: mapVerdict(backendResult.verdict),
        confidence: Math.floor((backendResult.confidence || 0) * 100),
        reasoning: "Verified using our AI-powered fact-checker",
        sources: Array.isArray(backendResult.evidence_links)
          ? backendResult.evidence_links.map(
              (link: any) => link.source || link.url || "Unknown"
            )
          : [],
      };

      setResults(formattedResult);

      toast({
        title: "Analysis Complete",
        description: `Content analyzed successfully with ${formattedResult.confidence}% confidence.`,
      });
    } catch (error) {
      console.error(error);
      toast({
        title: "Analysis Failed",
        description: "Unable to analyze the content. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 py-12 space-y-8">
        <div className="text-center mb-12">
          <h2 className="text-2xl font-semibold text-foreground mb-2">
            Combat Misinformation with AI
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Our advanced AI system analyzes content across multiple dimensions to help 
            identify potential misinformation and provide confidence ratings for your peace of mind.
          </p>
        </div>

        <InputSection onAnalyze={handleAnalyze} isLoading={isLoading} />
        <ResultsSection results={results} />
      </main>
    </div>
  );
};

export default Index;
*/
import { useState } from "react";
import Header from "@/components/Header";
import InputSection from "@/components/InputSection";
import ResultsSection from "@/components/ResultsSection";
import { useToast } from "@/hooks/use-toast";

// Updated types to include evidence links
interface EvidenceItem {
  source?: string;
  url?: string;
  verdict?: string;
}

interface Result {
  prediction: "real" | "fake" | "uncertain";
  confidence: number;
  reasoning: string;
  evidence_links: EvidenceItem[];
}

// Map backend verdict string to frontend literal types
const mapVerdict = (verdict: string): "real" | "fake" | "uncertain" => {
  switch (verdict.toLowerCase()) {
    case "real":
      return "real";
    case "fake":
      return "fake";
    default:
      return "uncertain";
  }
};

const Index = () => {
  const [results, setResults] = useState<Result | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleAnalyze = async (type: string, data: string) => {
    setIsLoading(true);
    setResults(null);

    try {
      // Backend endpoint
      const response = await fetch("http://127.0.0.1:8000/verify_text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: data }), // match backend model field
      });

      if (!response.ok) throw new Error("Failed to fetch analysis");

      const backendResult = await response.json();

      const formattedResult: Result = {
        prediction: mapVerdict(backendResult.verdict),
        confidence: Math.floor((backendResult.confidence || 0) * 100),
        reasoning: "Verified using our AI-powered fact-checker",
        evidence_links: Array.isArray(backendResult.evidence_links)
          ? backendResult.evidence_links.map((link: any) => ({
              source: link.source || "Unknown",
              url: link.url || "",
              verdict: link.verdict || "uncertain",
            }))
          : [],
      };

      setResults(formattedResult);

      toast({
        title: "Analysis Complete",
        description: `Content analyzed successfully with ${formattedResult.confidence}% confidence.`,
      });
    } catch (error) {
      console.error(error);
      toast({
        title: "Analysis Failed",
        description: "Unable to analyze the content. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 py-12 space-y-8">
        <div className="text-center mb-12">
          <h2 className="text-2xl font-semibold text-foreground mb-2">
            Combat Misinformation with AI
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Our advanced AI system analyzes content across multiple dimensions to help 
            identify potential misinformation and provide confidence ratings for your peace of mind.
          </p>
        </div>

        <InputSection onAnalyze={handleAnalyze} isLoading={isLoading} />

        {results && (
          <ResultsSection results={results} />
        )}

        {/* Optional: Display evidence links below */}
        {results?.evidence_links.length ? (
          <div className="mt-8 border-t pt-4">
            <h3 className="text-lg font-semibold mb-2">Evidence Links:</h3>
            <ul className="list-disc pl-5 space-y-1">
              {results.evidence_links.map((link, idx) => (
                <li key={idx}>
                  <strong>{link.source}</strong>{" "}
                  {link.url && (
                    <a href={link.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">
                      [Link]
                    </a>
                  )} - Verdict: {link.verdict}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </main>
    </div>
  );
};

export default Index;

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CheckCircle, AlertTriangle, XCircle, Info } from "lucide-react";

interface ResultData {
  prediction: "real" | "fake" | "uncertain";
  confidence: number;
  reasoning: string;
  sources?: string[];
}

interface ResultsSectionProps {
  results: ResultData | null;
}

const ResultsSection = ({ results }: ResultsSectionProps) => {
  if (!results) return null;

  const getResultIcon = () => {
    switch (results.prediction) {
      case "real":
        return <CheckCircle className="w-6 h-6 text-accent" />;
      case "fake":
        return <XCircle className="w-6 h-6 text-destructive" />;
      case "uncertain":
        return <AlertTriangle className="w-6 h-6 text-yellow-500" />;
    }
  };

  const getResultColor = () => {
    switch (results.prediction) {
      case "real":
        return "bg-accent/10 text-accent border-accent/20";
      case "fake":
        return "bg-destructive/10 text-destructive border-destructive/20";
      case "uncertain":
        return "bg-yellow-50 text-yellow-700 border-yellow-200";
    }
  };

  const getResultTitle = () => {
    switch (results.prediction) {
      case "real":
        return "Likely Authentic";
      case "fake":
        return "Potentially Fake News";
      case "uncertain":
        return "Uncertain - Requires Review";
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto shadow-lg mt-8">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {getResultIcon()}
            <div>
              <CardTitle className="text-xl">{getResultTitle()}</CardTitle>
              <CardDescription>Analysis Results</CardDescription>
            </div>
          </div>
          <Badge variant="outline" className={getResultColor()}>
            {Math.round(results.confidence)}% confidence
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Confidence Level</span>
            <span>{Math.round(results.confidence)}%</span>
          </div>
          <Progress 
            value={results.confidence} 
            className="h-2"
          />
        </div>

        <div className="space-y-2">
          <h4 className="font-semibold flex items-center gap-2">
            <Info className="w-4 h-4" />
            Analysis Summary
          </h4>
          <p className="text-muted-foreground text-sm leading-relaxed">
            {results.reasoning}
          </p>
        </div>

        {results.sources && results.sources.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-semibold">Sources Checked</h4>
            <ul className="space-y-1">
              {results.sources.map((source, index) => (
                <li key={index} className="text-sm text-muted-foreground">
                  • {source}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="bg-muted/50 p-4 rounded-lg">
          <p className="text-xs text-muted-foreground">
            <strong>Disclaimer:</strong> This analysis is AI-generated and should not be considered 
            as definitive fact-checking. Always verify important information through multiple reliable sources.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default ResultsSection;
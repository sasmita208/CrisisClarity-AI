import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { FileText, Search } from "lucide-react";

interface InputSectionProps {
  onAnalyze: (type: string, data: string) => void;
  isLoading: boolean;
}

const InputSection = ({ onAnalyze, isLoading }: InputSectionProps) => {
  const [text, setText] = useState("");

  const handleAnalyze = () => {
    if (text.trim()) {
      onAnalyze("text", text.trim());
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto shadow-lg">
      <CardHeader className="text-center">
        <CardTitle className="text-xl">Analyze Content for Misinformation</CardTitle>
        <CardDescription>
          Paste text content you want to fact-check
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="text-input">Text Content</Label>
          <Textarea
            id="text-input"
            placeholder="Paste the text you want to fact-check here..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="min-h-32 resize-none"
          />
        </div>
        <Button 
          onClick={handleAnalyze}
          disabled={!text.trim() || isLoading}
          variant="hero"
          size="lg"
          className="w-full"
        >
          <Search className="w-4 h-4 mr-2" />
          {isLoading ? "Analyzing..." : "Analyze Text"}
        </Button>
      </CardContent>
    </Card>
  );
};

export default InputSection;
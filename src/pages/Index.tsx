import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { FileText, Sparkles, ArrowRight } from "lucide-react";

const Index = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-subtle flex items-center justify-center p-4">
      <div className="text-center max-w-3xl">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-primary rounded-3xl mb-6">
          <FileText className="w-10 h-10 text-primary-foreground" />
        </div>
        <h1 className="text-5xl font-bold text-foreground mb-4">DocuMate AI</h1>
        <p className="text-xl text-muted-foreground mb-8">
          Generate professional documents and presentations with AI assistance
        </p>
        <div className="flex gap-4 justify-center">
          <Button size="lg" onClick={() => navigate("/auth")}>
            Get Started
            <ArrowRight className="w-5 h-5 ml-2" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Index;

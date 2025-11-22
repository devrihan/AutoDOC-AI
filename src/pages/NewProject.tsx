import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  FileText,
  Presentation,
  ArrowLeft,
  Loader2,
  Plus,
  Trash2,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";

type DocumentType = "word" | "powerpoint";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const API_URL = import.meta.env.VITE_API_URL;

const NewProject = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [generatingOutline, setGeneratingOutline] = useState(false);
  const [documentType, setDocumentType] = useState<DocumentType>("word");
  const [title, setTitle] = useState("");
  const [topic, setTopic] = useState("");
  const [sections, setSections] = useState<string[]>(["Introduction"]);
  const [pptTemplate, setPptTemplate] = useState("default");

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) {
        navigate("/auth");
      }
    });
  }, [navigate]);

  const handleAddSection = () => setSections([...sections, ""]);

  const handleRemoveSection = (index: number) =>
    setSections(sections.filter((_, i) => i !== index));

  const handleSectionChange = (index: number, value: string) => {
    const newSections = [...sections];
    newSections[index] = value;
    setSections(newSections);
  };

  const handleGenerateOutline = async () => {
    if (!topic.trim()) {
      toast.error("Please enter a topic first");
      return;
    }

    setGeneratingOutline(true);

    try {
      const token = (await supabase.auth.getSession()).data.session
        ?.access_token;
      if (!token) throw new Error("Not authenticated");

      const res = await fetch(`${API_URL}/api/generate-outline`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ topic, documentType }),
      });

      const json = await res.json();

      if (!res.ok) throw new Error(json.detail || "Failed to generate outline");

      if (json.outline && Array.isArray(json.outline)) {
        const titles = json.outline.map((item: any) => item.title);
        setSections(titles);
        toast.success("Outline generated successfully!");
      }
    } catch (error: any) {
      toast.error(error.message || "Failed to generate outline");
    } finally {
      setGeneratingOutline(false);
    }
  };

  const handleCreateProject = async () => {
    if (!title.trim()) return toast.error("Please enter a project title");
    if (!topic.trim()) return toast.error("Please enter a topic");
    if (sections.some((s) => !s.trim()))
      return toast.error("Please fill all section titles");

    setLoading(true);

    try {
      const token = (await supabase.auth.getSession()).data.session
        ?.access_token;
      if (!token) throw new Error("Not authenticated");

      const resProject = await fetch(`${API_URL}/api/projects/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          title,
          document_type: documentType,
          topic,
          ppt_template: pptTemplate,
        }),
      });

      const projectJson = await resProject.json();
      if (!resProject.ok) throw new Error(projectJson.detail);

      const project = projectJson.project;

      const sectionsToInsert = sections.map((sectionTitle, index) => ({
        project_id: project.id,
        title: sectionTitle,
        content: "",
        order_index: index,
      }));

      const resSections = await fetch(`${API_URL}/api/sections/add`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ sections: sectionsToInsert }),
      });

      const sectionJson = await resSections.json();
      if (!resSections.ok) throw new Error(sectionJson.detail);

      toast.success("Project created successfully!");

      navigate(`/project/${project.id}`);
    } catch (error: any) {
      toast.error(error.message || "Failed to create project");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-4">
          <Button variant="ghost" onClick={() => navigate("/dashboard")}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-3xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Create New Project
          </h1>
          <p className="text-muted-foreground">
            Configure your document and let AI generate the content
          </p>
        </div>

        <div className="space-y-6">
          {/* Project Details */}
          <Card>
            <CardHeader>
              <CardTitle>Project Details</CardTitle>
              <CardDescription>
                Basic information about your document
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Project Title</Label>
                <Input
                  id="title"
                  placeholder="e.g., Market Analysis Report"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="topic">Topic / Main Prompt</Label>
                <Textarea
                  id="topic"
                  placeholder="e.g., A comprehensive market analysis of the Electric Vehicle industry in 2025"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label>Document Type</Label>
                <RadioGroup
                  value={documentType}
                  onValueChange={(value) =>
                    setDocumentType(value as DocumentType)
                  }
                  className="flex gap-4"
                >
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="word" id="word" />
                    <Label
                      htmlFor="word"
                      className="flex items-center gap-2 cursor-pointer"
                    >
                      <FileText className="w-4 h-4" /> Word Document
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="powerpoint" id="powerpoint" />
                    <Label
                      htmlFor="powerpoint"
                      className="flex items-center gap-2 cursor-pointer"
                    >
                      <Presentation className="w-4 h-4" /> PowerPoint
                    </Label>
                  </div>
                </RadioGroup>
              </div>
              {/* TEMPLATE SELECTION */}
              {documentType === "powerpoint" && (
                <div className="space-y-2 pt-2 animate-in fade-in slide-in-from-top-2">
                  <Label>Presentation Template</Label>
                  <Select value={pptTemplate} onValueChange={setPptTemplate}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select a template" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="default">Default (Blank)</SelectItem>

                      <SelectItem value="basic">Minimalistic</SelectItem>
                      <SelectItem value="Product">
                        Product pitch deck
                      </SelectItem>
                      <SelectItem value="Geometric">
                        Geometric Colour block
                      </SelectItem>
                      <SelectItem value="Scientific">
                        Scientific Discovery
                      </SelectItem>
                      <SelectItem value="basic">Minimalistic</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Sections / Slides */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>
                    {documentType === "word"
                      ? "Document Outline"
                      : "Slide Titles"}
                  </CardTitle>
                  <CardDescription>
                    Define the structure of your{" "}
                    {documentType === "word" ? "document" : "presentation"}
                  </CardDescription>
                </div>
                <Button
                  variant="outline"
                  onClick={handleGenerateOutline}
                  disabled={generatingOutline || !topic.trim()}
                >
                  {generatingOutline ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Sparkles className="w-4 h-4 mr-2" />
                  )}
                  AI Suggest
                </Button>
              </div>
            </CardHeader>

            <CardContent className="space-y-3">
              {sections.map((section, index) => (
                <div key={index} className="flex gap-2">
                  <Input
                    placeholder={
                      documentType === "word"
                        ? `Section ${index + 1} title`
                        : `Slide ${index + 1} title`
                    }
                    value={section}
                    onChange={(e) => handleSectionChange(index, e.target.value)}
                  />
                  {sections.length > 1 && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleRemoveSection(index)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              ))}
              <Button
                variant="outline"
                onClick={handleAddSection}
                className="w-full"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add {documentType === "word" ? "Section" : "Slide"}
              </Button>
            </CardContent>
          </Card>

          {/* Footer Buttons */}
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => navigate("/dashboard")}
              className="flex-1"
            >
              Cancel
            </Button>

            <Button
              onClick={handleCreateProject}
              disabled={loading}
              className="flex-1"
            >
              {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Create & Generate Content
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default NewProject;

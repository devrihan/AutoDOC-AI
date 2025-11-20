import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft,
  Loader2,
  ThumbsUp,
  ThumbsDown,
  Download,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";

type Project = {
  id: string;
  title: string;
  document_type: "word" | "powerpoint";
  topic: string;
  status: string;
};

type Section = {
  id: string;
  title: string;
  content: string | null;
  order_index: number;
  project_id: string;
};

type Feedback = {
  id?: string;
  section_id: string;
  is_liked?: boolean | null;
  comment?: string | null;
};

const API_URL = import.meta.env.VITE_API_URL;

const ProjectEditor = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [project, setProject] = useState<Project | null>(null);
  const [sections, setSections] = useState<Section[]>([]);
  const [feedback, setFeedback] = useState<Map<string, Feedback>>(new Map());
  const [refinementPrompts, setRefinementPrompts] = useState<
    Map<string, string>
  >(new Map());
  const [refining, setRefining] = useState<Set<string>>(new Set());
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    loadProject();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // -------------------------
  // Helper: get token
  // -------------------------
  const getToken = async () => {
    const session = await supabase.auth.getSession();
    return (
      session.data.session?.access_token ||
      localStorage.getItem("token") ||
      null
    );
  };

  // -------------------------
  // Load project + sections + feedback from backend
  // -------------------------
  const loadProject = async () => {
    setLoading(true);
    try {
      if (!id) throw new Error("Invalid project id");

      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      const res = await fetch(`${API_URL}/api/projects/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const json = await res.json();
      if (!res.ok) {
        throw new Error(json.detail || "Failed to load project");
      }

      const proj = json.project;
      setProject(proj);

      // sections should come as proj.sections (backend: select("*, sections(*)"))
      const secs: Section[] = proj.sections || [];
      setSections(secs);

      // build feedback map if provided by backend; otherwise fetch separately
      const fbMap = new Map<string, Feedback>();
      if (json.feedback && Array.isArray(json.feedback)) {
        json.feedback.forEach((f: Feedback) => fbMap.set(f.section_id, f));
      }
      setFeedback(fbMap);
    } catch (error: any) {
      toast.error(error.message || "Failed to load project");
      console.error(error);
      navigate("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // Generate content for all sections
  // -------------------------
  const handleGenerateContent = async () => {
    if (!project) return;
    setGenerating(true);

    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      for (const section of sections) {
        // Call FastAPI generate-content endpoint
        const genRes = await fetch(`${API_URL}/api/generate-content`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            sectionTitle: section.title,
            topic: project.topic,
            documentType: project.document_type,
          }),
        });

        const genJson = await genRes.json();
        if (!genRes.ok) {
          throw new Error(
            genJson.detail ||
              "Failed generating content for section: " + section.title
          );
        }

        const newContent = genJson.content;

        // Update section content via backend
        const updRes = await fetch(`${API_URL}/api/sections/update`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            section_id: section.id,
            content: newContent,
          }),
        });

        const updJson = await updRes.json();
        if (!updRes.ok) {
          throw new Error(updJson.detail || "Failed to update section content");
        }
      }

      await loadProject();
      toast.success("Content generated successfully!");
    } catch (error: any) {
      toast.error(error.message || "Failed to generate content");
      console.error(error);
    } finally {
      setGenerating(false);
    }
  };

  // -------------------------
  // Refine a single section
  // -------------------------
  const handleRefineSection = async (sectionId: string) => {
    const prompt = refinementPrompts.get(sectionId);
    if (!prompt?.trim()) {
      toast.error("Please enter a refinement prompt");
      return;
    }

    const section = sections.find((s) => s.id === sectionId);
    if (!section) return;

    setRefining((prev) => new Set(prev).add(sectionId));

    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      // Call refine endpoint
      const res = await fetch(`${API_URL}/api/refine-content`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          currentContent: section.content || "",
          prompt,
          documentType: project?.document_type || "word",
        }),
      });

      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "Refinement failed");

      const refined = json.content;

      // Update section content
      const updRes = await fetch(`${API_URL}/api/sections/update`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          section_id: sectionId,
          content: refined,
        }),
      });
      const updJson = await updRes.json();
      if (!updRes.ok)
        throw new Error(updJson.detail || "Failed to update refined content");

      // Record refinement (backend should save this)
      const refRecord = await fetch(`${API_URL}/api/refinements/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          section_id: sectionId,
          prompt,
          result: refined,
        }),
      });
      if (!refRecord.ok) {
        const err = await refRecord.json();
        console.warn("Failed to record refinement:", err);
      }

      await loadProject();
      // clear prompt for this section
      setRefinementPrompts((prev) => {
        const copy = new Map(prev);
        copy.set(sectionId, "");
        return copy;
      });

      toast.success("Content refined successfully!");
    } catch (error: any) {
      toast.error(error.message || "Failed to refine content");
      console.error(error);
    } finally {
      setRefining((prev) => {
        const copy = new Set(prev);
        copy.delete(sectionId);
        return copy;
      });
    }
  };

  // -------------------------
  // Feedback (like/dislike)
  // -------------------------
  const handleFeedback = async (sectionId: string, isLiked: boolean) => {
    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      const existing = feedback.get(sectionId);

      const res = await fetch(`${API_URL}/api/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          section_id: sectionId,
          is_liked: isLiked,
          // if you want to include comment use comment field
        }),
      });

      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "Failed to save feedback");

      // reload feedback/project
      await loadProject();
    } catch (error: any) {
      toast.error(error.message || "Failed to save feedback");
      console.error(error);
    }
  };

  // -------------------------
  // Comment save on blur
  // -------------------------
  const handleCommentChange = async (sectionId: string, comment: string) => {
    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      const res = await fetch(`${API_URL}/api/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          section_id: sectionId,
          comment,
        }),
      });

      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "Failed to save comment");

      toast.success("Comment saved");
      await loadProject();
    } catch (error: any) {
      toast.error(error.message || "Failed to save comment");
      console.error(error);
    }
  };

  // -------------------------
  // Export document (download blob)
  // -------------------------
  const handleExport = async () => {
    if (!project) return;

    setExporting(true);
    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      // backend should return application/octet-stream or proper file type
      const response = await fetch(`${API_URL}/api/export-document`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ projectId: project.id }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to export document");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const ext = project.document_type === "word" ? "docx" : "pptx";
      a.download = `${project.title || "document"}.${ext}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      toast.success("Document exported successfully!");
    } catch (error: any) {
      toast.error(error.message || "Failed to export document");
      console.error(error);
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate("/dashboard")}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-xl font-bold text-foreground">
                {project?.title}
              </h1>
              <p className="text-sm text-muted-foreground">{project?.topic}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handleExport}
              disabled={exporting || sections.some((s) => !s.content)}
            >
              {exporting ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Download className="w-4 h-4 mr-2" />
              )}
              Export {project?.document_type === "word" ? "Word" : "PowerPoint"}
            </Button>

            {sections.some((s) => !s.content) && (
              <Button onClick={handleGenerateContent} disabled={generating}>
                {generating ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Sparkles className="w-4 h-4 mr-2" />
                )}
                Generate Content
              </Button>
            )}
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-5xl">
        <div className="space-y-6">
          {sections.map((section, index) => (
            <Card key={section.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>{section.title}</CardTitle>
                    <CardDescription>
                      {project?.document_type === "word" ? "Section" : "Slide"}{" "}
                      {index + 1}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant={
                        feedback.get(section.id)?.is_liked === true
                          ? "default"
                          : "outline"
                      }
                      size="sm"
                      onClick={() => handleFeedback(section.id, true)}
                    >
                      <ThumbsUp className="w-4 h-4" />
                    </Button>
                    <Button
                      variant={
                        feedback.get(section.id)?.is_liked === false
                          ? "default"
                          : "outline"
                      }
                      size="sm"
                      onClick={() => handleFeedback(section.id, false)}
                    >
                      <ThumbsDown className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                <Textarea
                  value={section.content || "Content will be generated..."}
                  readOnly
                  rows={8}
                  className="resize-none"
                />

                <div className="space-y-2">
                  <div className="flex gap-2">
                    <Input
                      placeholder="Refinement prompt (e.g., Make it more formal, Add bullet points...)"
                      value={refinementPrompts.get(section.id) || ""}
                      onChange={(e) => {
                        const newMap = new Map(refinementPrompts);
                        newMap.set(section.id, e.target.value);
                        setRefinementPrompts(newMap);
                      }}
                      disabled={!section.content}
                    />
                    <Button
                      onClick={() => handleRefineSection(section.id)}
                      disabled={refining.has(section.id) || !section.content}
                    >
                      {refining.has(section.id) ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Sparkles className="w-4 h-4" />
                      )}
                    </Button>
                  </div>

                  <Input
                    placeholder="Add a comment..."
                    defaultValue={feedback.get(section.id)?.comment || ""}
                    onBlur={(e) =>
                      handleCommentChange(section.id, e.target.value)
                    }
                  />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </main>
    </div>
  );
};

export default ProjectEditor;

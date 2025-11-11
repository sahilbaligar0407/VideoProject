import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { ClipCard, Clip } from "@/components/ClipCard";
import { Button } from "@/components/ui/button";
import { Info, Loader2, Bookmark, BookmarkCheck, Flag } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { useAuth } from "@/hooks/useAuth";

interface ClipWithMetadata extends Clip {
  file_path?: string;
  thumbnail_path?: string;
  transcript_paths?: string[];
}

const Results = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [clips, setClips] = useState<ClipWithMetadata[]>([]);
  const [savedClipIds, setSavedClipIds] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingClipId, setSavingClipId] = useState<string | null>(null);
  const [savedClipsCount, setSavedClipsCount] = useState(0);
  const [reportClipId, setReportClipId] = useState<string | null>(null);
  const [reportComment, setReportComment] = useState("");
  const [isReporting, setIsReporting] = useState(false);
  const [showReportDialog, setShowReportDialog] = useState(false);

  useEffect(() => {
    if (!jobId) {
      toast.error("No job ID provided");
      navigate("/");
      return;
    }

    const fetchResults = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(`/api/v1/status/${jobId}`);
        
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error("Job not found");
          }
          throw new Error(`HTTP ${response.status}`);
        }

        const status = await response.json();
        
        if (status.status === "failed") {
          throw new Error(status.error || "Processing failed");
        }
        
        if (status.status !== "completed") {
          // If not completed, redirect to process page
          navigate(`/process/${jobId}`);
          return;
        }
        
        if (!status.clips || status.clips.length === 0) {
          throw new Error("No clips generated");
        }

        // Convert backend clip format to frontend Clip format
        // Sort clips by viral score (highest first) if ranking is available
        const sortedClips = [...status.clips].sort((a: any, b: any) => {
          const scoreA = a.ranking?.viral_score || 0;
          const scoreB = b.ranking?.viral_score || 0;
          return scoreB - scoreA;
        });
        
        const convertedClips: ClipWithMetadata[] = sortedClips.map((clip: any, index: number) => ({
          rank: index + 1,
          score: clip.ranking?.viral_score ? clip.ranking.viral_score / 5.0 : 0.5, // Convert 0-5 scale to 0-1 for display
          clip_id: clip.clip_id,
          thumbnail_url: clip.thumbnail_url || `/api/v1/thumbnail/${clip.clip_id}`, // Use thumbnail URL if available
          preview_url: clip.preview_url || `/api/v1/preview/${clip.clip_id}`, // Use preview URL (no auth required)
          download_url: clip.download_url || `/api/v1/download/${clip.clip_id}`, // Download URL (auth required)
          duration_sec: clip.duration || (clip.end_time - clip.start_time),
          transcript_snippet: clip.caption_text || "",
          start_sec: clip.start_time,
          end_sec: clip.end_time,
          file_path: clip.file_path,
          thumbnail_path: clip.thumbnail_path,
          transcript_paths: clip.transcript_paths || [], // Use transcript_paths from backend
        }));

        setClips(convertedClips);
        
        // Fetch saved clips to check which ones are saved
        if (isAuthenticated) {
          fetchSavedClips();
        }
        
        setIsLoading(false);
      } catch (error: any) {
        console.error("Error fetching results:", error);
        setError(error.message || "Failed to fetch results");
        setIsLoading(false);
        toast.error(error.message || "Failed to fetch results");
      }
    };

    fetchResults();
  }, [jobId, navigate, isAuthenticated]);

  const fetchSavedClips = async () => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) return;

      const response = await fetch("/api/v1/saved-clips", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const savedClips = await response.json();
        const savedIds = new Set(savedClips.map((clip: any) => clip.clip_id));
        setSavedClipIds(savedIds);
        setSavedClipsCount(savedClips.length);
      }
    } catch (error) {
      console.error("Error fetching saved clips:", error);
    }
  };

  const handleSaveClip = async (clip: ClipWithMetadata) => {
    if (!isAuthenticated) {
      toast.error("Please sign in to save clips");
      navigate("/login");
      return;
    }

    if (savedClipsCount >= 3) {
      toast.error("You have reached the maximum limit of 3 saved clips. Please remove a clip before saving a new one.");
      return;
    }

    try {
      setSavingClipId(clip.clip_id);
      const token = localStorage.getItem("access_token");
      if (!token) {
        throw new Error("Not authenticated");
      }

      // Use transcript_paths from clip if available, otherwise try to infer from file_path
      let transcriptPaths: string[] = clip.transcript_paths || [];
      if (!transcriptPaths.length && clip.file_path) {
        const basePath = clip.file_path.replace(/\.mp4$/, "");
        const extensions = [".vtt", ".srt", ".ass", ".json"];
        extensions.forEach((ext) => {
          const transcriptPath = basePath + ext;
          transcriptPaths.push(transcriptPath);
        });
      }

      const response = await fetch("/api/v1/saved-clips", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          clip_id: clip.clip_id,
          file_path: clip.file_path || "",
          thumbnail_path: clip.thumbnail_path,
          transcript_paths: transcriptPaths,
          clip_metadata: {
            start_time: clip.start_sec,
            end_time: clip.end_sec,
            duration: clip.duration_sec,
            caption_text: clip.transcript_snippet,
            ranking: clip.score ? { viral_score: clip.score * 5 } : undefined,
          },
        }),
      });

      if (response.status === 401) {
        toast.error("Please sign in to save clips");
        navigate("/login");
        return;
      }

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Failed to save clip" }));
        throw new Error(error.detail || "Failed to save clip");
      }

      toast.success("Clip saved to library!");
      setSavedClipIds((prev) => new Set([...prev, clip.clip_id]));
      setSavedClipsCount((prev) => prev + 1);
    } catch (error: any) {
      console.error("Error saving clip:", error);
      toast.error(error.message || "Failed to save clip");
    } finally {
      setSavingClipId(null);
    }
  };

  const handleUnsaveClip = async (clipId: string) => {
    try {
      setSavingClipId(clipId);
      const token = localStorage.getItem("access_token");
      if (!token) {
        throw new Error("Not authenticated");
      }

      const response = await fetch(`/api/v1/saved-clips/${clipId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to remove clip");
      }

      toast.success("Clip removed from library");
      setSavedClipIds((prev) => {
        const newSet = new Set(prev);
        newSet.delete(clipId);
        return newSet;
      });
      setSavedClipsCount((prev) => Math.max(0, prev - 1));
    } catch (error: any) {
      console.error("Error removing clip:", error);
      toast.error(error.message || "Failed to remove clip");
    } finally {
      setSavingClipId(null);
    }
  };

  const handleReportClip = (clipId: string) => {
    setReportClipId(clipId);
    setReportComment("");
    setShowReportDialog(true);
  };

  const handleSubmitReport = async () => {
    if (!reportClipId) return;

    if (!isAuthenticated) {
      toast.error("Please sign in to report clips");
      navigate("/login");
      return;
    }

    setIsReporting(true);
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        throw new Error("Not authenticated");
      }

      const formData = new FormData();
      formData.append("clip_id", reportClipId);
      if (reportComment.trim()) {
        formData.append("comment", reportComment.trim());
      }

      const response = await fetch("/api/v1/reports/clip", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.status === 401) {
        toast.error("Please sign in to report clips");
        navigate("/login");
        return;
      }

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Failed to submit report" }));
        throw new Error(error.detail || "Failed to submit report");
      }

      toast.success("Report submitted successfully. Thank you for your feedback!");
      setShowReportDialog(false);
      setReportClipId(null);
      setReportComment("");
    } catch (error: any) {
      console.error("Error reporting clip:", error);
      toast.error(error.message || "Failed to submit report");
    } finally {
      setIsReporting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 py-12 sm:py-20 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
            <p className="text-muted-foreground">Loading results...</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 py-12 sm:py-20 flex items-center justify-center">
          <div className="text-center max-w-md">
            <h2 className="text-2xl font-bold mb-4">Error Loading Results</h2>
            <p className="text-muted-foreground mb-6">{error}</p>
            <Button onClick={() => navigate("/")}>Go Home</Button>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 py-12 sm:py-20">
        <div className="container px-4 sm:px-6 lg:px-8">
          <div className="max-w-5xl mx-auto">
            {/* Header */}
            <div className="text-center mb-12">
              <h1 className="text-3xl sm:text-4xl font-bold mb-4">
                Your Highlights
              </h1>
              <div className="flex items-center justify-center gap-2 text-muted-foreground">
                <span>Top {clips.length} clips ranked by viral score</span>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button className="inline-flex">
                        <Info className="h-4 w-4" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent className="max-w-xs">
                      <p className="text-sm">
                        Similarity to a curated viral vector using embeddings + cosine similarity
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <p className="text-sm text-muted-foreground mt-2">
                Job ID: <code className="text-xs font-mono bg-muted px-2 py-1 rounded">{jobId}</code>
              </p>
            </div>

            {/* Clips Grid */}
            {clips.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
                {clips.map((clip) => {
                  const isSaved = savedClipIds.has(clip.clip_id);
                  const isSaving = savingClipId === clip.clip_id;
                  
                  return (
                    <div key={clip.clip_id} className="relative">
                      <ClipCard clip={clip} />
                      {isAuthenticated && (
                        <div className="absolute top-2 right-2 z-10 flex flex-col gap-2">
                          <Button
                            variant={isSaved ? "default" : "secondary"}
                            size="sm"
                            onClick={() =>
                              isSaved
                                ? handleUnsaveClip(clip.clip_id)
                                : handleSaveClip(clip)
                            }
                            disabled={isSaving || (!isSaved && savedClipsCount >= 3)}
                            className="shadow-sm"
                          >
                            {isSaving ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : isSaved ? (
                              <>
                                <BookmarkCheck className="h-4 w-4 mr-1" />
                                Saved
                              </>
                            ) : (
                              <>
                                <Bookmark className="h-4 w-4 mr-1" />
                                Save
                              </>
                            )}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleReportClip(clip.clip_id)}
                            className="shadow-sm"
                          >
                            <Flag className="h-4 w-4 mr-1" />
                            Report
                          </Button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-muted-foreground">No clips found</p>
              </div>
            )}
            
            {isAuthenticated && savedClipsCount >= 3 && (
              <div className="mb-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  ⚠️ You have reached the maximum limit of 3 saved clips. Remove a clip to save a new one.
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="text-center space-y-4">
              <Button size="lg" onClick={() => navigate("/")}>
                Create Another
              </Button>
              <p className="text-sm text-muted-foreground">
                Want to adjust settings?{" "}
                <a href="#" className="text-primary hover:underline">
                  Contact support
                </a>
              </p>
            </div>
          </div>
        </div>
      </main>

      <Footer />

      {/* Report Dialog */}
      <Dialog open={showReportDialog} onOpenChange={setShowReportDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Report Clip</DialogTitle>
            <DialogDescription>
              Report this clip for not being viral enough. Your feedback helps us improve our algorithm.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="comment">Additional Comments (Optional)</Label>
              <Textarea
                id="comment"
                placeholder="Tell us why this clip isn't viral enough..."
                value={reportComment}
                onChange={(e) => setReportComment(e.target.value)}
                rows={4}
                disabled={isReporting}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowReportDialog(false);
                setReportClipId(null);
                setReportComment("");
              }}
              disabled={isReporting}
            >
              Cancel
            </Button>
            <Button onClick={handleSubmitReport} disabled={isReporting}>
              {isReporting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                "Submit Report"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Results;

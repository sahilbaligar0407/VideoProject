import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { ClipCard, Clip } from "@/components/ClipCard";
import { Button } from "@/components/ui/button";
import { Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/hooks/useAuth";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface SavedClip {
  id: number;
  clip_id: string;
  file_path: string;
  thumbnail_path?: string;
  thumbnail_url?: string;
  preview_url: string;
  download_url: string;
  transcript_paths: string[];
  clip_metadata: {
    start_time?: number;
    end_time?: number;
    duration?: number;
    caption_text?: string;
    ranking?: {
      viral_score?: number;
    };
  };
  created_at: string;
}

const SavedClips = () => {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [clips, setClips] = useState<Clip[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteClipId, setDeleteClipId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (authLoading) return;

    if (!isAuthenticated) {
      toast.error("Please sign in to view saved clips");
      navigate("/login");
      return;
    }

    fetchSavedClips();
  }, [isAuthenticated, authLoading, navigate]);

  const fetchSavedClips = async () => {
    try {
      setIsLoading(true);
      setError(null); // Clear any previous errors
      const token = localStorage.getItem("access_token");
      if (!token) {
        console.error("No token found in localStorage");
        throw new Error("Not authenticated");
      }

      console.log("Fetching saved clips with token:", token.substring(0, 20) + "...");

      const response = await fetch("/api/v1/saved-clips", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      console.log("Saved clips response status:", response.status);

      if (response.status === 401) {
        console.error("Unauthorized - token might be invalid");
        // Clear invalid token
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        toast.error("Session expired. Please sign in again.");
        navigate("/login");
        return;
      }

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Failed to fetch saved clips:", response.status, errorText);
        throw new Error(`Failed to fetch saved clips: ${response.status} ${errorText}`);
      }

      const savedClips: SavedClip[] = await response.json();
      console.log("Fetched saved clips:", savedClips.length);

      // Convert to Clip format (even if empty array)
      const convertedClips: Clip[] = savedClips.map((savedClip, index) => ({
        rank: index + 1,
        score: savedClip.clip_metadata?.ranking?.viral_score
          ? savedClip.clip_metadata.ranking.viral_score / 5.0
          : 0.5,
        clip_id: savedClip.clip_id,
        thumbnail_url: savedClip.thumbnail_url || `/api/v1/thumbnail/${savedClip.clip_id}`,
        preview_url: savedClip.preview_url,
        download_url: savedClip.download_url,
        duration_sec: savedClip.clip_metadata?.duration || 0,
        transcript_snippet: savedClip.clip_metadata?.caption_text || "",
        start_sec: savedClip.clip_metadata?.start_time || 0,
        end_sec: savedClip.clip_metadata?.end_time || 0,
      }));

      setClips(convertedClips);
      setIsLoading(false);
    } catch (error: any) {
      console.error("Error fetching saved clips:", error);
      // Only set error if it's not a navigation (login redirect)
      if (!error.message?.includes("login")) {
        setError(error.message || "Failed to fetch saved clips");
        toast.error(error.message || "Failed to fetch saved clips");
      }
      setIsLoading(false);
    }
  };

  const handleDelete = async (clipId: string) => {
    try {
      setIsDeleting(true);
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
        throw new Error("Failed to delete clip");
      }

      toast.success("Clip removed from library");
      setDeleteClipId(null);
      // Refresh the list
      fetchSavedClips();
    } catch (error: any) {
      console.error("Error deleting clip:", error);
      toast.error(error.message || "Failed to delete clip");
    } finally {
      setIsDeleting(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 py-12 sm:py-20 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
            <p className="text-muted-foreground">Verifying authentication...</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (isLoading && !error) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 py-12 sm:py-20 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
            <p className="text-muted-foreground">Loading saved clips...</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  // Only show error page if there's an actual error (not just empty state)
  if (error && !isLoading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 py-12 sm:py-20 flex items-center justify-center">
          <div className="text-center max-w-md">
            <h2 className="text-2xl font-bold mb-4">Error Loading Saved Clips</h2>
            <p className="text-muted-foreground mb-6">{error}</p>
            <div className="flex gap-2 justify-center">
              <Button onClick={() => fetchSavedClips()}>Retry</Button>
              <Button variant="outline" onClick={() => navigate("/")}>Go Home</Button>
            </div>
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
                Saved Clips Library
              </h1>
              <p className="text-muted-foreground">
                {clips.length === 0
                  ? "You haven't saved any clips yet"
                  : `You have ${clips.length} saved clip${clips.length === 1 ? "" : "s"} (max 3)`}
              </p>
            </div>

            {/* Clips Grid */}
            {clips.length > 0 ? (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
                  {clips.map((clip) => (
                    <div key={clip.clip_id} className="relative">
                      <ClipCard clip={clip} />
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => setDeleteClipId(clip.clip_id)}
                        className="absolute top-2 right-2 z-10"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
                {/* Actions - Only show when there are clips */}
                <div className="text-center space-y-4">
                  <Button size="lg" onClick={() => navigate("/")}>
                    Create More Clips
                  </Button>
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <p className="text-muted-foreground mb-6">
                  No saved clips yet. Generate clips and save them to your library!
                </p>
                <Button size="lg" onClick={() => navigate("/")}>
                  Create Clips
                </Button>
              </div>
            )}
          </div>
        </div>
      </main>

      <Footer />

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteClipId} onOpenChange={(open) => !open && setDeleteClipId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove Clip from Library?</AlertDialogTitle>
            <AlertDialogDescription>
              This will remove the clip from your saved clips library. You can save it again later if you want.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteClipId && handleDelete(deleteClipId)}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Removing...
                </>
              ) : (
                "Remove"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default SavedClips;


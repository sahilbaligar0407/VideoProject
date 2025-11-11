import { Download, Copy, Play, Award, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useNavigate } from "react-router-dom";

export type Clip = {
  rank: number;
  score: number;
  clip_id: string;
  thumbnail_url: string;
  preview_url?: string;  // Optional preview URL (no auth required)
  download_url: string;  // Download URL (auth required)
  duration_sec: number;
  transcript_snippet?: string;
  start_sec: number;
  end_sec: number;
};

interface ClipCardProps {
  clip: Clip;
}

export const ClipCard = ({ clip }: ClipCardProps) => {
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [thumbnailError, setThumbnailError] = useState(false);
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(clip.preview_url);
    toast.success("Link copied to clipboard!");
  };

  const handlePreviewClick = () => {
    setIsPreviewOpen(true);
  };

  const handleDownload = async () => {
    // Check if user is authenticated
    if (!isAuthenticated) {
      toast.error("Please sign in to download videos");
      navigate("/login");
      return;
    }

    try {
      // Get auth token from localStorage
      const token = localStorage.getItem("access_token");
      if (!token) {
        toast.error("Please sign in to download videos");
        navigate("/login");
        return;
      }

      // Use the download_url which should be /api/v1/download/{clip_id}
      const downloadUrl = clip.download_url.startsWith('http') 
        ? clip.download_url 
        : clip.download_url; // Vite proxy will handle it
      
      toast.loading("Starting download...");
      
      const response = await fetch(downloadUrl, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.status === 401) {
        // Authentication required
        toast.dismiss();
        toast.error("Please sign in to download videos");
        navigate("/login");
        return;
      }
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Download failed" }));
        throw new Error(errorData.detail || `Download failed: ${response.statusText}`);
      }
      
      const blob = await response.blob();
      
      if (blob.size === 0) {
        throw new Error("Downloaded file is empty");
      }
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `clip_${clip.clip_id}.mp4`;
      document.body.appendChild(a);
      a.click();
      
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }, 100);
      
      toast.dismiss();
      toast.success("Download started!");
    } catch (error: any) {
      console.error("Download error:", error);
      toast.dismiss();
      
      if (error.message.includes("sign in") || error.message.includes("Authentication")) {
        navigate("/login");
      } else {
        toast.error(error.message || "Download failed");
      }
    }
  };

  return (
    <div
      className={cn(
        "group relative bg-card border rounded-2xl overflow-hidden transition-all duration-300 hover:shadow-lg",
        clip.rank === 1 && "border-primary/50 shadow-glow"
      )}
    >
      {/* Rank Badge */}
      <div className="absolute top-4 left-4 z-10">
        <Badge
          variant={clip.rank === 1 ? "default" : "secondary"}
          className={cn(
            "text-sm font-bold px-3 py-1",
            clip.rank === 1 && "shadow-glow"
          )}
        >
          {clip.rank === 1 && <Award className="h-3 w-3 mr-1" />}
          #{clip.rank}
        </Badge>
      </div>

      {/* Score Badge */}
      <div className="absolute top-4 right-4 z-10">
        <Badge
          variant="outline"
          className="bg-background/80 backdrop-blur text-sm font-mono"
        >
          {clip.score.toFixed(2)}
        </Badge>
      </div>

      {/* Thumbnail/Preview */}
      <div 
        className="relative aspect-[9/16] bg-muted flex items-center justify-center overflow-hidden cursor-pointer group/thumb"
        onClick={handlePreviewClick}
      >
        {clip.thumbnail_url && !thumbnailError ? (
          <>
            <img 
              src={clip.thumbnail_url} 
              alt={`Clip ${clip.rank} thumbnail`}
              className="w-full h-full object-cover"
              onError={() => setThumbnailError(true)}
            />
            <div className="absolute inset-0 bg-black/0 group-hover/thumb:bg-black/30 transition-colors flex items-center justify-center">
              <div className="opacity-0 group-hover/thumb:opacity-100 transition-opacity">
                <div className="inline-flex p-4 rounded-full bg-primary/80 backdrop-blur-sm">
                  <Play className="h-8 w-8 text-white fill-white" />
                </div>
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="absolute inset-0 bg-gradient-to-t from-background/80 to-transparent" />
            <div className="relative z-10 text-center">
              <div className="inline-flex p-4 rounded-full bg-primary/20 mb-3 group-hover:scale-110 transition-transform">
                <Play className="h-8 w-8 text-primary" />
              </div>
              <p className="text-sm text-muted-foreground">Click to preview</p>
            </div>
          </>
        )}
      </div>

      {/* Video Preview Dialog */}
      <Dialog open={isPreviewOpen} onOpenChange={setIsPreviewOpen}>
        <DialogContent className="max-w-4xl w-full p-0">
          <DialogHeader className="px-6 pt-6">
            <DialogTitle>Clip #{clip.rank} Preview</DialogTitle>
          </DialogHeader>
          <div className="relative aspect-[9/16] max-h-[80vh] bg-black flex items-center justify-center">
            <video
              src={clip.preview_url || clip.download_url}
              controls
              className="w-full h-full object-contain"
              autoPlay
              playsInline
            >
              Your browser does not support the video tag.
            </video>
          </div>
        </DialogContent>
      </Dialog>

      {/* Content */}
      <div className="p-5 space-y-4">
        {/* Duration */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Duration</span>
          <code className="font-mono bg-muted px-2 py-1 rounded">
            {formatDuration(clip.duration_sec)}
          </code>
        </div>

        {/* Transcript Snippet */}
        {clip.transcript_snippet && (
          <div className="space-y-1">
            <span className="text-sm text-muted-foreground">Best moment</span>
            <p className="text-sm font-medium italic">
              "{clip.transcript_snippet}"
            </p>
          </div>
        )}

        {/* Time Range */}
        <div className="text-xs text-muted-foreground">
          {formatDuration(clip.start_sec)} – {formatDuration(clip.end_sec)}
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <Button
            onClick={handleDownload}
            className="flex-1 shadow-sm"
            size="sm"
          >
            <Download className="h-4 w-4 mr-2" />
            Download
          </Button>
          <Button
            onClick={handleCopyLink}
            variant="outline"
            size="sm"
          >
            <Copy className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

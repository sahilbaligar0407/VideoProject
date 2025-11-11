import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, Link as LinkIcon, Loader2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { useAuth } from "@/hooks/useAuth";
// Caption style will be configured on a separate page after video submission

export const HeroInput = () => {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [pendingYoutubeUrl, setPendingYoutubeUrl] = useState("");

  const validateYoutubeUrl = (url: string) => {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
    return youtubeRegex.test(url);
  };

  const handleYoutubeSubmit = () => {
    // Wait for auth to finish loading
    if (authLoading) {
      toast.error("Please wait while we verify your authentication...");
      return;
    }

    // Check authentication first
    if (!isAuthenticated) {
      console.log("User not authenticated for YouTube submit");
      toast.error("Please sign in to generate clips");
      navigate("/login");
      return;
    }

    if (!youtubeUrl) {
      toast.error("Please enter a YouTube URL");
      return;
    }

    if (!validateYoutubeUrl(youtubeUrl)) {
      toast.error("Please enter a valid YouTube URL");
      return;
    }

    // Show confirmation dialog
    setPendingYoutubeUrl(youtubeUrl);
    setShowConfirmDialog(true);
  };

  const handleConfirmYoutubeSubmit = async () => {
    setShowConfirmDialog(false);
    setIsLoading(true);
    
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        console.error("No token found in localStorage");
        toast.error("Please sign in to generate clips");
        navigate("/login");
        return;
      }

      console.log("Submitting YouTube URL with token:", token.substring(0, 20) + "...");

      const formData = new FormData();
      formData.append("youtube_url", pendingYoutubeUrl);
      formData.append("vertical", "true");
      
      const response = await fetch("/api/v1/process-video", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
        body: formData,
      });
      
      console.log("Process video response status:", response.status);
      
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
        console.error("Process video error:", response.status, errorText);
        let errorDetail = "Failed to start processing";
        try {
          const errorJson = JSON.parse(errorText);
          errorDetail = errorJson.detail || errorDetail;
        } catch {
          errorDetail = errorText || errorDetail;
        }
        throw new Error(errorDetail);
      }
      
      const data = await response.json();
      const requestId = data.request_id;
      console.log("Processing started with request ID:", requestId);
      
      toast.success("Video submitted!");
      navigate(`/caption-config/${requestId}`);
    } catch (error: any) {
      console.error("Error starting processing:", error);
      toast.error(error.message || "Failed to start processing");
      setIsLoading(false);
    }
  };

  const handleCancelYoutubeSubmit = () => {
    setShowConfirmDialog(false);
    setPendingYoutubeUrl("");
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      // Check file size (e.g., 500MB limit)
      if (selectedFile.size > 500 * 1024 * 1024) {
        toast.error("File size must be less than 500MB");
        return;
      }
      setFile(selectedFile);
      toast.success(`Selected: ${selectedFile.name}`);
    }
  };

  const handleFileUpload = async () => {
    // Wait for auth to finish loading
    if (authLoading) {
      toast.error("Please wait while we verify your authentication...");
      return;
    }

    // Check authentication first
    if (!isAuthenticated) {
      console.log("User not authenticated for file upload");
      toast.error("Please sign in to generate clips");
      navigate("/login");
      return;
    }

    if (!file) {
      toast.error("Please select a file");
      return;
    }

    setIsLoading(true);
    setUploadProgress(0);
    
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        console.error("No token found in localStorage");
        toast.error("Please sign in to generate clips");
        navigate("/login");
        return;
      }

      console.log("Uploading file with token:", token.substring(0, 20) + "...");

      const formData = new FormData();
      formData.append("video_file", file);
      formData.append("vertical", "true");
      
      // Use XMLHttpRequest for upload progress tracking
      const xhr = new XMLHttpRequest();
      let hasError = false;
      
      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable && !hasError) {
          const percentComplete = Math.min((e.loaded / e.total) * 100, 99.9); // Cap at 99.9% until complete
          setUploadProgress(percentComplete);
          console.log(`Upload progress: ${percentComplete.toFixed(2)}% (${e.loaded} / ${e.total} bytes)`);
        }
      });
      
      xhr.addEventListener("load", () => {
        if (hasError) return;
        
        console.log("Upload response status:", xhr.status);
        
        if (xhr.status === 200) {
          try {
            const data = JSON.parse(xhr.responseText);
            const requestId = data.request_id;
            console.log("Upload successful, request ID:", requestId);
            setUploadProgress(100);
            toast.success("Upload complete!");
            navigate(`/caption-config/${requestId}`);
          } catch (error) {
            console.error("Failed to parse response:", error, xhr.responseText);
            hasError = true;
            setIsLoading(false);
            setUploadProgress(0);
            toast.error("Failed to parse server response");
          }
        } else if (xhr.status === 401) {
          hasError = true;
          console.error("Unauthorized - token might be invalid");
          // Clear invalid token
          localStorage.removeItem("access_token");
          localStorage.removeItem("user");
          setIsLoading(false);
          setUploadProgress(0);
          toast.error("Session expired. Please sign in again.");
          navigate("/login");
        } else {
          hasError = true;
          console.error("Upload failed:", xhr.status, xhr.statusText, xhr.responseText);
          setIsLoading(false);
          setUploadProgress(0);
          try {
            const errorData = JSON.parse(xhr.responseText);
            toast.error(errorData.detail || `Upload failed: ${xhr.statusText}`);
          } catch {
            toast.error(`Upload failed: ${xhr.status} ${xhr.statusText}`);
          }
        }
      });
      
      xhr.addEventListener("error", (e) => {
        if (hasError) return;
        hasError = true;
        console.error("Upload network error:", e);
        setIsLoading(false);
        setUploadProgress(0);
        toast.error("Network error during upload. Please check your connection and try again.");
      });
      
      xhr.addEventListener("abort", () => {
        if (hasError) return;
        hasError = true;
        console.error("Upload aborted");
        setIsLoading(false);
        setUploadProgress(0);
        toast.error("Upload was cancelled");
      });
      
      xhr.addEventListener("timeout", () => {
        if (hasError) return;
        hasError = true;
        console.error("Upload timeout");
        setIsLoading(false);
        setUploadProgress(0);
        toast.error("Upload timed out. The file may be too large. Please try a smaller file or check your connection.");
      });
      
      // Set timeout to 10 minutes for large files
      xhr.timeout = 10 * 60 * 1000; // 10 minutes
      
      xhr.open("POST", "/api/v1/process-video");
      xhr.setRequestHeader("Accept", "application/json");
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      xhr.send(formData);
    } catch (error: any) {
      console.error("Error uploading file:", error);
      toast.error(error.message || "Failed to upload file");
      setIsLoading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <Tabs defaultValue="youtube" className="w-full">
        <TabsList className="grid w-full grid-cols-2 mb-6">
          <TabsTrigger value="youtube" className="gap-2">
            <LinkIcon className="h-4 w-4" />
            YouTube URL
          </TabsTrigger>
          <TabsTrigger value="upload" className="gap-2">
            <Upload className="h-4 w-4" />
            Upload File
          </TabsTrigger>
        </TabsList>

        <TabsContent value="youtube" className="space-y-4">
          <div className="flex gap-2">
            <Input
              type="url"
              placeholder="https://www.youtube.com/watch?v=..."
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              className="h-12 text-base"
              disabled={isLoading}
            />
            <Button 
              onClick={handleYoutubeSubmit} 
              disabled={isLoading || !isAuthenticated || authLoading}
              size="lg"
              className="shadow-glow min-w-[140px]"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : !isAuthenticated ? (
                "Sign In to Generate"
              ) : (
                "Generate"
              )}
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">
            Paste any YouTube video URL to get started
          </p>
        </TabsContent>

        {/* YouTube URL Confirmation Dialog */}
        <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-500" />
                Confirm Video Rights
              </DialogTitle>
              <DialogDescription asChild>
                <div className="pt-4 space-y-3">
                  <p className="font-medium">Before proceeding, please confirm that you have:</p>
                  <ul className="list-disc list-inside space-y-2 text-sm text-muted-foreground ml-2">
                    <li>The legal right to download this video</li>
                    <li>The legal right to distribute this video</li>
                    <li>The legal right to edit and modify this video</li>
                    <li>Authorization to use this video content</li>
                  </ul>
                  <p className="text-sm text-muted-foreground pt-2">
                    By clicking "I Confirm", you acknowledge that you have all necessary rights and permissions 
                    to download, distribute, and edit the video at the following URL:
                  </p>
                  <p className="text-xs bg-muted p-2 rounded break-all font-mono">
                    {pendingYoutubeUrl}
                  </p>
                  <p className="text-xs text-red-500 font-medium">
                    ⚠️ Downloading copyrighted content without permission may violate terms of service and copyright laws.
                  </p>
                </div>
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={handleCancelYoutubeSubmit}>
                Cancel
              </Button>
              <Button onClick={handleConfirmYoutubeSubmit} className="shadow-glow">
                I Confirm
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <TabsContent value="upload" className="space-y-4">
          <div className="border-2 border-dashed border-border rounded-2xl p-8 text-center hover:border-primary/50 transition-colors">
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept="video/*"
              onChange={handleFileSelect}
              disabled={isLoading}
            />
            <label 
              htmlFor="file-upload" 
              className="cursor-pointer flex flex-col items-center gap-3"
            >
              <div className="p-4 rounded-full bg-primary/10">
                <Upload className="h-8 w-8 text-primary" />
              </div>
              <div>
                <p className="font-medium">
                  {file ? file.name : "Click to browse or drag and drop"}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  MP4, MOV, AVI up to 500MB
                </p>
              </div>
            </label>
          </div>
          
          {file && (
            <>
              {isLoading && uploadProgress < 100 && (
                <div className="space-y-2">
                  <div className="h-2 rounded-full bg-secondary overflow-hidden">
                    <div 
                      className="h-full bg-gradient-primary transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <p className="text-sm text-center text-muted-foreground">
                    Uploading... {uploadProgress}%
                  </p>
                </div>
              )}
              
              <Button 
                onClick={handleFileUpload} 
                disabled={isLoading || !isAuthenticated || authLoading}
                size="lg"
                className="w-full shadow-glow"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : !isAuthenticated ? (
                  "Sign In to Generate"
                ) : (
                  "Upload & Generate"
                )}
              </Button>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

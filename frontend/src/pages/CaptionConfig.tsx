import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { SkipForward, Sparkles } from "lucide-react";
import { toast } from "sonner";

const CaptionConfig = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [enabled, setEnabled] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!jobId) {
      toast.error("No job ID provided");
      navigate("/");
      return;
    }
  }, [jobId, navigate]);

  const handleSkip = async () => {
    // Skip captioning - set enabled to false and proceed to processing
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        toast.error("Please sign in");
        navigate("/login");
        return;
      }

      // Save config with enabled=false (use default styles for backend)
      await fetch(`/api/v1/jobs/${jobId}/captions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          enabled: false,
          position: "bottom",
          regular_words: { font_family: "Arial", font_size: 32, color: "yellow", bold: false, italic: false },
          wow_words: { font_family: "Impact", font_size: 36, color: "yellow", bold: true, italic: false },
          like_words: { font_family: "Arial", font_size: 32, color: "green", bold: false, italic: true },
        }),
      });

      navigate(`/process/${jobId}`);
    } catch (error: any) {
      console.error("Error skipping captions:", error);
      // Still navigate even if save fails
      navigate(`/process/${jobId}`);
    }
  };

  const handleContinue = async () => {
    setIsSubmitting(true);
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        toast.error("Please sign in");
        navigate("/login");
        return;
      }

      // Save config with enabled flag (backend will use hard-coded AutoCaptions styling)
      const response = await fetch(`/api/v1/jobs/${jobId}/captions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          enabled: enabled,
          position: "bottom",
          regular_words: { font_family: "Arial", font_size: 32, color: "yellow", bold: false, italic: false },
          wow_words: { font_family: "Impact", font_size: 36, color: "yellow", bold: true, italic: false },
          like_words: { font_family: "Arial", font_size: 32, color: "green", bold: false, italic: true },
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to update caption configuration");
      }

      toast.success(enabled ? "Captions enabled! Processing will begin..." : "Processing will begin without captions...");
      navigate(`/process/${jobId}`);
    } catch (error: any) {
      console.error("Error saving caption config:", error);
      toast.error(error.message || "Failed to save configuration");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 py-12 sm:py-20">
        <div className="container px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-3xl sm:text-4xl font-bold mb-4">
                Auto-Captions
              </h1>
              <p className="text-muted-foreground">
                Add professional captions to your video clips
              </p>
            </div>

            <div className="bg-card border border-border rounded-lg p-8 space-y-6">
              {/* Enable/Disable */}
              <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <Label className="text-lg font-semibold">Enable Auto-Captions</Label>
                    {enabled && <Sparkles className="h-5 w-5 text-yellow-500" />}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {enabled 
                      ? "Captions will be automatically added to all generated clips with professional styling"
                      : "Clips will be generated without captions"}
                  </p>
                </div>
                <Switch
                  checked={enabled}
                  onCheckedChange={setEnabled}
                  className="ml-4"
                />
              </div>

              {/* Coming Soon Notice */}
              {enabled && (
                <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                  <div className="flex items-start gap-3">
                    <Sparkles className="h-5 w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-blue-500 mb-1">
                        Using AutoCaptions Styling
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Captions use our professional hard-coded styling:
                      </p>
                      <ul className="text-sm text-muted-foreground mt-2 ml-4 list-disc space-y-1">
                        <li><strong>Wow words</strong> (wow, amazing, incredible): ExtraBold font, yellow color</li>
                        <li><strong>Italic words</strong> (like, feel, think): Italic font, white color</li>
                        <li><strong>Regular words</strong>: Black font, white color</li>
                      </ul>
                      <p className="text-xs text-muted-foreground mt-3 italic">
                        Custom styling options coming soon!
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Info Box */}
              <div className="p-4 bg-muted/30 rounded-lg">
                <p className="text-sm text-muted-foreground">
                  {enabled 
                    ? "✅ Captions will be generated automatically using the transcript files from your video. The styling is optimized for vertical short-form content."
                    : "ℹ️ You can always add captions manually later, or re-process the video with captions enabled."}
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="mt-8 flex gap-4 justify-center">
              <Button
                variant="outline"
                size="lg"
                onClick={handleSkip}
                disabled={isSubmitting}
              >
                <SkipForward className="mr-2 h-4 w-4" />
                Skip Captions
              </Button>
              <Button
                size="lg"
                onClick={handleContinue}
                disabled={isSubmitting}
                className="shadow-glow"
              >
                {isSubmitting ? "Starting..." : enabled ? "Continue with Captions" : "Continue without Captions"}
              </Button>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default CaptionConfig;


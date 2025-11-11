import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { ProgressTimeline, Step } from "@/components/ProgressTimeline";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

const Process = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [steps, setSteps] = useState<Step[]>([
    { key: "upload", label: "Upload / Fetch", status: "pending" },
    { key: "transcribe", label: "Transcription (Whisper)", status: "pending" },
    { key: "detect", label: "Highlight Detection", status: "pending" },
    { key: "score", label: "Viral Similarity Scoring", status: "pending" },
    { key: "generate", label: "Generating Clips & Transcripts", status: "pending" },
    { key: "captioning", label: "Adding Captions", status: "pending" },
    { key: "finalize", label: "Finalizing", status: "pending" },
  ]);
  const [progressPct, setProgressPct] = useState(0);

  // Map backend status steps to frontend steps
  const mapBackendStepToFrontendStep = (backendStep: string): string => {
    const stepMap: Record<string, string> = {
      "saving_file": "upload",
      "uploading": "upload",
      "downloading_youtube": "upload",
      "extracting_audio": "transcribe",
      "transcribing": "transcribe",
      "transcribing_complete": "transcribe",
      "detecting_highlights": "detect",
      "highlights_detected": "detect",
      "scoring": "score",
      "scoring_complete": "score",
      "generating_clips": "generate",  // This step includes transcript file generation
      "clips_generated": "generate",
      "generating_transcripts": "generate",  // Transcripts are generated during clip generation
      "generating_transcript_files": "generate",  // Same - transcripts are part of clip generation
      "captioning": "captioning",  // Adding captions to clips
      "processing_video": "transcribe",
      "completed": "finalize",
    };
    return stepMap[backendStep] || "upload";
  };

  useEffect(() => {
    if (!jobId) {
      toast.error("No job ID provided");
      navigate("/");
      return;
    }

    let pollInterval: NodeJS.Timeout;
    let isPolling = true;

    const pollStatus = async () => {
      try {
        const response = await fetch(`/api/v1/status/${jobId}`);
        
        if (!response.ok) {
          if (response.status === 404) {
            toast.error("Job not found");
            navigate("/");
            return;
          }
          throw new Error(`HTTP ${response.status}`);
        }

        const status = await response.json();
        
        // Update progress percentage
        setProgressPct(status.progress || 0);
        
        // Map backend current_step to frontend steps
        const currentStepKey = mapBackendStepToFrontendStep(status.current_step || "upload");
        
        // Update steps based on status
        setSteps((prevSteps) => {
          const newSteps = prevSteps.map((step, index) => {
            const stepIndex = prevSteps.findIndex((s) => s.key === currentStepKey);
            
            if (index < stepIndex) {
              return { ...step, status: "done" as const };
            } else if (index === stepIndex) {
              return { 
                ...step, 
                status: status.status === "failed" ? "error" as const : "running" as const,
                ts: Date.now()
              };
            } else {
              return { ...step, status: "pending" as const };
            }
          });
          
          return newSteps;
        });

        // Handle completion
        if (status.status === "completed") {
          isPolling = false;
          clearInterval(pollInterval);
          toast.success("Processing complete!");
          setTimeout(() => {
            navigate(`/results/${jobId}`);
          }, 1000);
        }
        
        // Handle failure
        if (status.status === "failed") {
          isPolling = false;
          clearInterval(pollInterval);
          toast.error(status.error || "Processing failed");
        }
      } catch (error: any) {
        console.error("Error polling status:", error);
        if (isPolling) {
          toast.error("Failed to fetch status. Retrying...");
        }
      }
    };

    // Poll immediately, then every 2 seconds
    pollStatus();
    if (isPolling) {
      pollInterval = setInterval(() => {
        if (isPolling) {
          pollStatus();
        }
      }, 2000);
    }

    return () => {
      isPolling = false;
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [jobId, navigate]);

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      <main className="flex-1 py-12 sm:py-20">
        <div className="container px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-12">
              <h1 className="text-3xl sm:text-4xl font-bold mb-4">
                Working on Your Highlights...
              </h1>
              <p className="text-muted-foreground">
                Job ID: <code className="text-xs font-mono bg-muted px-2 py-1 rounded">{jobId}</code>
              </p>
            </div>

            <div className="bg-card border border-border rounded-2xl p-6 sm:p-8 shadow-lg">
              <ProgressTimeline steps={steps} progressPct={progressPct} />
            </div>

            <div className="mt-8 text-center">
              <p className="text-sm text-muted-foreground mb-4">
                This usually takes 2-10 minutes depending on video length
              </p>
              <Button variant="outline" size="sm" onClick={() => navigate("/")}>
                Cancel
              </Button>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default Process;

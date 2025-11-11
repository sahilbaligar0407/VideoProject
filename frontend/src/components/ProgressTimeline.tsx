import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export type Step = {
  key: string;
  label: string;
  status: "pending" | "running" | "done" | "error";
  ts?: number;
};

interface ProgressTimelineProps {
  steps: Step[];
  progressPct?: number;
}

export const ProgressTimeline = ({ steps, progressPct }: ProgressTimelineProps) => {
  const formatTimestamp = (ts?: number) => {
    if (!ts) return "";
    return new Date(ts).toLocaleTimeString();
  };

  const getStatusIcon = (status: Step["status"]) => {
    switch (status) {
      case "done":
        return <CheckCircle2 className="h-5 w-5 text-primary" />;
      case "running":
        return <Loader2 className="h-5 w-5 text-primary animate-spin" />;
      case "error":
        return <XCircle className="h-5 w-5 text-destructive" />;
      default:
        return <Circle className="h-5 w-5 text-muted-foreground" />;
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      {/* Progress Bar */}
      {progressPct !== undefined && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="font-medium">Overall Progress</span>
            <span className="text-muted-foreground">{progressPct}%</span>
          </div>
          <div className="h-3 rounded-full bg-secondary overflow-hidden">
            <div
              className="h-full bg-gradient-primary transition-all duration-500 ease-out"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      )}

      {/* Timeline */}
      <div className="relative space-y-4">
        {/* Connecting line */}
        <div className="absolute left-[11px] top-3 bottom-3 w-0.5 bg-border" />

        {steps.map((step, index) => (
          <div key={step.key} className="relative flex gap-4 items-start">
            {/* Icon */}
            <div className="relative z-10 flex-shrink-0 bg-background">
              {getStatusIcon(step.status)}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0 pt-0.5">
              <div className="flex items-center justify-between gap-2">
                <p
                  className={cn(
                    "font-medium",
                    step.status === "pending" && "text-muted-foreground",
                    step.status === "running" && "text-foreground",
                    step.status === "done" && "text-foreground",
                    step.status === "error" && "text-destructive"
                  )}
                >
                  {step.label}
                </p>
                {step.ts && (
                  <span className="text-xs text-muted-foreground">
                    {formatTimestamp(step.ts)}
                  </span>
                )}
              </div>
              
              {step.status === "running" && (
                <p className="text-sm text-muted-foreground mt-1">
                  Processing...
                </p>
              )}
              
              {step.status === "error" && (
                <p className="text-sm text-destructive mt-1">
                  Failed to complete this step
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

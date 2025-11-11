import { Mic, Sparkles, Scissors, Type, Upload, Download } from "lucide-react";

const features = [
  {
    icon: Mic,
    title: "AI Transcription (Whisper)",
    description: "Accurate speech-to-text for clean, searchable captions.",
    tech: "OpenAI Whisper API",
  },
  {
    icon: Sparkles,
    title: "Viral Similarity Engine",
    description: "Embeddings + cosine similarity to surface the 'whoa' moments.",
    tech: "text-embedding-3-small",
  },
  {
    icon: Scissors,
    title: "Auto Highlight Clips",
    description: "2–3 clips, 20–40 seconds each, ranked by impact.",
    tech: "FFmpeg + Scoring Algorithm",
  },
  {
    icon: Type,
    title: "Transcript Files",
    description: "Generate multiple transcript formats (.srt, .vtt, .ass, .json) for your clips.",
    tech: "Multi-Format Export",
  },
  {
    icon: Upload,
    title: "Simple Inputs",
    description: "Paste a YouTube link or upload a file—done.",
    tech: "YouTube API + Direct Upload",
  },
  {
    icon: Download,
    title: "Download & Share",
    description: "Download clips and transcript files. Ready for your caption workflow.",
    tech: "MP4 + Transcript Files",
  },
];

export const FeatureGrid = () => {
  return (
    <section id="features" className="py-24 bg-gradient-hero">
      <div className="container px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            Powered by AI, Built for Creators
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Everything you need to turn long-form content into viral-ready clips
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              className="group relative p-6 rounded-2xl bg-card border border-border hover:border-primary/50 transition-all duration-300 hover:shadow-lg"
            >
              <div className="mb-4">
                <div className="inline-flex p-3 rounded-xl bg-primary/10 text-primary group-hover:scale-110 transition-transform">
                  <feature.icon className="h-6 w-6" />
                </div>
              </div>
              
              <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
              <p className="text-muted-foreground mb-3">{feature.description}</p>
              
              <div className="inline-flex items-center gap-1 text-xs font-mono text-muted-foreground bg-muted px-2 py-1 rounded">
                <code>{feature.tech}</code>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

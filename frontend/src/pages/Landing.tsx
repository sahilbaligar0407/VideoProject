import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { HeroInput } from "@/components/HeroInput";
import { FeatureGrid } from "@/components/FeatureGrid";
import { Button } from "@/components/ui/button";
import { Zap, Shield, TrendingUp } from "lucide-react";
import heroBg from "@/assets/hero-bg.jpg";

const Landing = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div 
          className="absolute inset-0 opacity-10 bg-cover bg-center"
          style={{ backgroundImage: `url(${heroBg})` }}
        />
        <div className="absolute inset-0 bg-gradient-hero" />
        
        <div className="relative container px-4 sm:px-6 lg:px-8 py-20 sm:py-32">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-6">
              Turn Long Videos into{" "}
              <span className="bg-gradient-primary bg-clip-text text-transparent">
                Viral-Ready Highlights
              </span>
              —Automatically
            </h1>
            
            <p className="text-xl text-muted-foreground mb-12 max-w-2xl mx-auto">
              AI transcription, viral moment detection, and auto-captions—done for you.
            </p>

            <HeroInput />

            <button
              onClick={() => {
                document.getElementById("features")?.scrollIntoView({ 
                  behavior: "smooth" 
                });
              }}
              className="mt-6 text-sm text-muted-foreground hover:text-foreground transition-colors underline"
            >
              See how it works
            </button>
          </div>
        </div>
      </section>

      {/* Trust Badges */}
      <section className="border-y border-border/40 bg-muted/30">
        <div className="container px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-wrap justify-center items-center gap-8 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-primary" />
              <span>AI-Powered</span>
            </div>
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-primary" />
              <span>Whisper Transcription</span>
            </div>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              <span>OpenAI Embeddings</span>
            </div>
            <div className="flex items-center gap-2">
              <code className="text-xs font-mono px-2 py-1 rounded bg-primary/10 text-primary">
                FFmpeg
              </code>
              <span>Rendering</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <FeatureGrid />

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-b from-background to-muted/30">
        <div className="container px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl sm:text-4xl font-bold mb-6">
              Ready to Create Viral Clips?
            </h2>
            <p className="text-muted-foreground text-lg mb-8">
              Start turning your long-form content into share-worthy highlights in minutes.
            </p>
            <Button size="lg" className="shadow-glow" asChild>
              <a href="#hero">Get Started Free</a>
            </Button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Landing;

import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { Sparkles, Target, Zap, Users, Mail, Code, Brain, Video } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const About = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 py-12 sm:py-20">
        <div className="container px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto">
            {/* Header */}
            <div className="text-center mb-16">
              <div className="inline-flex items-center gap-2 font-bold text-4xl mb-4">
                <Sparkles className="h-10 w-10 text-primary" />
                <span className="bg-gradient-primary bg-clip-text text-transparent">
                  ClipGenius
                </span>
              </div>
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                AI-powered video highlights for creators. Turn long-form content into viral-ready clips automatically.
              </p>
            </div>

            {/* Mission Card */}
            <Card className="mb-8">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Target className="h-6 w-6 text-primary" />
                  <CardTitle className="text-2xl">Our Mission</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground text-lg leading-relaxed">
                  ClipGenius was built to solve a simple problem: creating engaging short-form content
                  from long videos is time-consuming and requires expertise. We believe every creator
                  should have access to professional-quality tools that help them reach wider audiences
                  without the manual work.
                </p>
              </CardContent>
            </Card>

            {/* How It Works */}
            <Card className="mb-8">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Zap className="h-6 w-6 text-primary" />
                  <CardTitle className="text-2xl">How It Works</CardTitle>
                </div>
                <CardDescription>Powered by cutting-edge AI technology</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-6">
                  Our AI-powered platform combines multiple cutting-edge technologies to deliver
                  professional results:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-start gap-3 p-4 rounded-lg bg-muted/50">
                    <Brain className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold mb-1">OpenAI Whisper</p>
                      <p className="text-sm text-muted-foreground">
                        Accurate speech-to-text transcription with multilingual support
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-4 rounded-lg bg-muted/50">
                    <Sparkles className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold mb-1">Viral Similarity Engine</p>
                      <p className="text-sm text-muted-foreground">
                        Embeddings + cosine similarity to identify viral moments
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-4 rounded-lg bg-muted/50">
                    <Video className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold mb-1">FFmpeg</p>
                      <p className="text-sm text-muted-foreground">
                        Professional video processing and clip extraction
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-4 rounded-lg bg-muted/50">
                    <Code className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold mb-1">Transcript Generation</p>
                      <p className="text-sm text-muted-foreground">
                        Multiple formats (.srt, .vtt, .ass, .json) for your workflow
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Why ClipGenius */}
            <Card className="mb-8">
              <CardHeader>
                <CardTitle className="text-2xl">Why ClipGenius?</CardTitle>
                <CardDescription>What makes us different</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4 text-lg leading-relaxed">
                  We're not just another video editor. Our Viral Similarity Engine analyzes your content
                  against patterns from successful viral videos, helping you identify the moments most
                  likely to engage your audience. Combined with automatic transcript generation in multiple
                  formats, you can go from long-form content to share-ready clips in minutes.
                </p>
                <div className="flex flex-wrap gap-2 mt-4">
                  <Badge variant="secondary">AI-Powered</Badge>
                  <Badge variant="secondary">Fast Processing</Badge>
                  <Badge variant="secondary">Multiple Formats</Badge>
                  <Badge variant="secondary">Viral Scoring</Badge>
                  <Badge variant="secondary">Easy to Use</Badge>
                </div>
              </CardContent>
            </Card>

            {/* For Creators */}
            <Card className="mb-8">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Users className="h-6 w-6 text-primary" />
                  <CardTitle className="text-2xl">For Creators, By Creators</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground text-lg leading-relaxed">
                  Built by a team that understands the creator economy, ClipGenius is designed to
                  save you time while maximizing the impact of your content. Whether you're a YouTuber,
                  podcaster, educator, or brand, we help you get more value from every video you create.
                </p>
              </CardContent>
            </Card>

            {/* Get in Touch */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Mail className="h-6 w-6 text-primary" />
                  <CardTitle className="text-2xl">Get in Touch</CardTitle>
                </div>
                <CardDescription>We'd love to hear from you</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  Have questions or feedback? We're here to help!
                </p>
                <a 
                  href="mailto:support@clipgenius.app"
                  className="inline-flex items-center gap-2 text-primary hover:underline font-medium"
                >
                  <Mail className="h-4 w-4" />
                  support@clipgenius.app
                </a>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default About;

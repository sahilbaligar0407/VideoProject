import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { Shield, Lock, Eye, FileText, Users, Mail } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const Privacy = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 py-12 sm:py-20">
        <div className="container px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto">
            {/* Header */}
            <div className="text-center mb-12">
              <div className="inline-flex items-center justify-center p-3 rounded-full bg-primary/10 mb-4">
                <Shield className="h-8 w-8 text-primary" />
              </div>
              <h1 className="text-4xl sm:text-5xl font-bold mb-4">
                Privacy Policy
              </h1>
              <p className="text-lg text-muted-foreground">
                Last updated: {new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}
              </p>
            </div>

            {/* Introduction Card */}
            <Card className="mb-8">
              <CardHeader>
                <CardTitle>Introduction</CardTitle>
                <CardDescription>How we protect your privacy</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  At ClipGenius, we take your privacy seriously. This Privacy Policy explains how we
                  collect, use, and protect your information when you use our service to transform
                  long-form videos into viral-ready highlights.
                </p>
              </CardContent>
            </Card>

            {/* Information We Collect */}
            <Card className="mb-8">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary" />
                  <CardTitle>Information We Collect</CardTitle>
                </div>
                <CardDescription>What data we gather and why</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  We collect information that you provide directly to us, including:
                </p>
                <ul className="space-y-2 list-disc list-inside text-muted-foreground">
                  <li>Video content you upload or link to (YouTube URLs)</li>
                  <li>Processing preferences and settings</li>
                  <li>Usage data and analytics to improve our service</li>
                  <li>Error logs and diagnostic information</li>
                </ul>
              </CardContent>
            </Card>

            {/* How We Use Your Information */}
            <Card className="mb-8">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Eye className="h-5 w-5 text-primary" />
                  <CardTitle>How We Use Your Information</CardTitle>
                </div>
                <CardDescription>How your data is processed</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  We use the information we collect to:
                </p>
                <ul className="space-y-2 list-disc list-inside text-muted-foreground">
                  <li>Process your video content and generate highlight clips</li>
                  <li>Generate transcript files in multiple formats</li>
                  <li>Improve our AI models and service quality</li>
                  <li>Ensure security and prevent abuse</li>
                  <li>Analyze usage patterns to enhance user experience</li>
                </ul>
              </CardContent>
            </Card>

            {/* Data Security */}
            <Card className="mb-8">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Lock className="h-5 w-5 text-primary" />
                  <CardTitle>Data Security</CardTitle>
                </div>
                <CardDescription>How we protect your data</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  We implement appropriate technical and organizational measures to protect your
                  personal information against unauthorized access, alteration, disclosure, or
                  destruction. Your video files are processed securely and are not stored permanently
                  after processing completes.
                </p>
              </CardContent>
            </Card>

            {/* Third-Party Services */}
            <Card className="mb-8">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-primary" />
                  <CardTitle>Third-Party Services</CardTitle>
                </div>
                <CardDescription>Services we use to power ClipGenius</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  We use third-party services for video processing, including:
                </p>
                <ul className="space-y-2 list-disc list-inside text-muted-foreground">
                  <li><strong>OpenAI Whisper API:</strong> For accurate speech-to-text transcription</li>
                  <li><strong>OpenAI Embeddings API:</strong> For viral similarity scoring</li>
                  <li><strong>yt-dlp:</strong> For downloading YouTube videos (when you provide a URL)</li>
                </ul>
                <p className="text-muted-foreground mt-4">
                  These services have their own privacy policies governing their use of your information.
                  We recommend reviewing their privacy policies for more information.
                </p>
              </CardContent>
            </Card>

            {/* Your Rights */}
            <Card className="mb-8">
              <CardHeader>
                <CardTitle>Your Rights</CardTitle>
                <CardDescription>Control over your data</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">You have the right to:</p>
                <ul className="space-y-2 list-disc list-inside text-muted-foreground">
                  <li>Access your personal information</li>
                  <li>Correct inaccurate data</li>
                  <li>Request deletion of your data</li>
                  <li>Object to processing of your data</li>
                  <li>Export your data in a portable format</li>
                </ul>
              </CardContent>
            </Card>

            {/* Contact Us */}
            <Card className="mb-8">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Mail className="h-5 w-5 text-primary" />
                  <CardTitle>Contact Us</CardTitle>
                </div>
                <CardDescription>Have questions about privacy?</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  If you have any questions about this Privacy Policy, please contact us at{" "}
                  <a 
                    href="mailto:privacy@clipgenius.app" 
                    className="text-primary hover:underline font-medium"
                  >
                    privacy@clipgenius.app
                  </a>
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default Privacy;

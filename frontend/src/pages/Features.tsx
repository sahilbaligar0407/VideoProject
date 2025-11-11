import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { FeatureGrid } from "@/components/FeatureGrid";

const Features = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="py-20 sm:py-32 bg-gradient-hero">
          <div className="container px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl mx-auto text-center">
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-6">
                Powerful Features for
                <span className="bg-gradient-primary bg-clip-text text-transparent block mt-2">
                  Viral Content Creation
                </span>
              </h1>
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                Everything you need to transform long-form videos into engaging, shareable highlights
              </p>
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
                Ready to Get Started?
              </h2>
              <p className="text-muted-foreground text-lg mb-8">
                Start creating viral-ready clips from your long-form content in minutes.
              </p>
              <a 
                href="/"
                className="inline-flex items-center justify-center px-8 py-3 text-base font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-glow"
              >
                Try It Now
              </a>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default Features;


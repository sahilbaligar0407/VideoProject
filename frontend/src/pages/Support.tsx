import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { Construction, Mail, Clock } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const Support = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 py-12 sm:py-20">
        <div className="container px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl mx-auto">
            {/* Coming Soon Card */}
            <Card className="text-center">
              <CardHeader className="pb-4">
                <div className="mx-auto mb-4 w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
                  <Construction className="h-10 w-10 text-primary animate-pulse" />
                </div>
                <CardTitle className="text-3xl sm:text-4xl mb-2">Coming Soon</CardTitle>
                <CardDescription className="text-lg">
                  We're building something amazing for you
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <p className="text-muted-foreground text-lg">
                  Our support center is currently under construction. We're working hard to bring you
                  a comprehensive help center with FAQs, tutorials, and direct support options.
                </p>

                {/* Contact Option */}
                <div className="pt-6 border-t border-border">
                  <div className="flex items-center justify-center gap-3 mb-4">
                    <Mail className="h-5 w-5 text-primary" />
                    <h3 className="text-xl font-semibold">Need Help Now?</h3>
                  </div>
                  <p className="text-muted-foreground mb-4">
                    Feel free to reach out to us directly via email:
                  </p>
                  <a 
                    href="mailto:support@clipgenius.app"
                    className="inline-flex items-center gap-2 text-primary hover:underline font-medium text-lg"
                  >
                    <Mail className="h-5 w-5" />
                    support@clipgenius.app
                  </a>
                </div>

                {/* Coming Features */}
                <div className="pt-6 border-t border-border">
                  <div className="flex items-center justify-center gap-3 mb-4">
                    <Clock className="h-5 w-5 text-primary" />
                    <h3 className="text-xl font-semibold">What's Coming</h3>
                  </div>
                  <ul className="text-left space-y-2 text-muted-foreground max-w-md mx-auto">
                    <li>• Comprehensive FAQ section</li>
                    <li>• Video tutorials and guides</li>
                    <li>• Live chat support</li>
                    <li>• Knowledge base articles</li>
                    <li>• Community forum</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default Support;


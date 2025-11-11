import { Link } from "react-router-dom";
import { Sparkles } from "lucide-react";

export const Footer = () => {
  return (
    <footer className="border-t border-border/40 bg-muted/30">
      <div className="container px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="md:col-span-2">
            <Link to="/" className="flex items-center gap-2 font-bold text-xl mb-4">
              <Sparkles className="h-6 w-6 text-primary" />
              <span className="bg-gradient-primary bg-clip-text text-transparent">
                ClipGenius
              </span>
            </Link>
            <p className="text-sm text-muted-foreground max-w-md">
              Turn long videos into viral-ready highlights automatically with AI-powered 
              transcription, viral moment detection, and multi-format transcript files.
            </p>
          </div>

          <div>
            <h3 className="font-semibold mb-4">Product</h3>
            <ul className="space-y-3">
              <li>
                <Link 
                  to="/about" 
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  About Us
                </Link>
              </li>
              <li>
                <Link 
                  to="/features" 
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Features
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold mb-4">Support</h3>
            <ul className="space-y-3">
              <li>
                <Link 
                  to="/support" 
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Support
                </Link>
              </li>
              <li>
                <Link 
                  to="/privacy" 
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Privacy Policy
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-border/40">
          <p className="text-sm text-muted-foreground text-center">
            © {new Date().getFullYear()} ClipGenius. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

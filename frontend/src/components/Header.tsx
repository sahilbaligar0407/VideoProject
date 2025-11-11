import { Link } from "react-router-dom";
import { Moon, Sun, Sparkles, Library, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/hooks/useAuth";
import { MobileMenu } from "@/components/MobileMenu";

export const Header = () => {
  const { theme, setTheme } = useTheme();
  const { user, logout, isAuthenticated } = useAuth();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-2 font-bold text-xl">
          <Sparkles className="h-6 w-6 text-primary" />
          <span className="bg-gradient-primary bg-clip-text text-transparent">
            ClipGenius
          </span>
        </Link>

        <div className="flex items-center gap-4">
          {/* Mobile Menu (hamburger) - only show when authenticated */}
          {isAuthenticated && <MobileMenu />}

          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="rounded-full"
          >
            {theme === "dark" ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
            <span className="sr-only">Toggle theme</span>
          </Button>

          {isAuthenticated && user ? (
            <div className="hidden md:flex items-center gap-3">
              {(user.id === -1 || user.is_admin) && (
                <Button variant="ghost" size="sm" asChild>
                  <Link to="/admin" className="flex items-center gap-2">
                    <Shield className="h-4 w-4" />
                    <span>Admin Portal</span>
                  </Link>
                </Button>
              )}
              {user.id !== -1 && !user.is_admin && (
                <Button variant="ghost" size="sm" asChild>
                  <Link to="/saved-clips" className="flex items-center gap-2">
                    <Library className="h-4 w-4" />
                    <span>Saved Clips</span>
                  </Link>
                </Button>
              )}
              <span className="text-sm text-muted-foreground">
                {user.email}
              </span>
              <Button variant="outline" size="sm" onClick={logout}>
                Logout
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" asChild>
                <Link to="/login">Login</Link>
              </Button>
              <Button size="sm" asChild className="shadow-glow">
                <Link to="/signup">Sign up</Link>
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

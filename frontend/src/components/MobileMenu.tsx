import { Link } from "react-router-dom";
import { Menu, X, Library, Home, LogOut, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { useAuth } from "@/hooks/useAuth";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

export const MobileMenu = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const handleLogout = () => {
    logout();
    setOpen(false);
    navigate("/");
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="md:hidden">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-[300px] sm:w-[400px]">
        <SheetHeader>
          <SheetTitle>Menu</SheetTitle>
        </SheetHeader>
        <div className="flex flex-col gap-4 mt-8">
          <div className="px-3 py-2 text-sm text-muted-foreground">
            {user?.email}
          </div>
          <Link
            to="/"
            onClick={() => setOpen(false)}
            className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-accent transition-colors"
          >
            <Home className="h-5 w-5" />
            <span>Home</span>
          </Link>
                  {(user?.id === -1 || user?.is_admin) ? (
                    <Link
                      to="/admin"
                      onClick={() => setOpen(false)}
                      className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-accent transition-colors"
                    >
                      <Shield className="h-5 w-5" />
                      <span>Admin Portal</span>
                    </Link>
                  ) : (
                    <Link
                      to="/saved-clips"
                      onClick={() => setOpen(false)}
                      className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-accent transition-colors"
                    >
                      <Library className="h-5 w-5" />
                      <span>Saved Clips Library</span>
                    </Link>
                  )}
                  <Button
                    variant="ghost"
                    onClick={handleLogout}
                    className="flex items-center gap-3 justify-start px-3 py-2"
                  >
                    <LogOut className="h-5 w-5" />
                    <span>Logout</span>
                  </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
};


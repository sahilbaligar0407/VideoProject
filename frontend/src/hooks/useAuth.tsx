import { useState, useEffect, createContext, useContext, ReactNode } from "react";

interface User {
  id: number;
  email: string;
  created_at: string;
  is_admin?: boolean;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for stored token and user info
    const token = localStorage.getItem("access_token");
    const userStr = localStorage.getItem("user");
    
    if (token && userStr) {
      try {
        const cachedUserData = JSON.parse(userStr);
        // Set user immediately from cache for faster UI
        setUser(cachedUserData);
        
        // Verify token is still valid by fetching user info
        fetch("/api/v1/auth/me", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
          .then((res) => {
            if (res.ok) {
              return res.json();
            }
            // If token is invalid, clear storage
            if (res.status === 401) {
              localStorage.removeItem("access_token");
              localStorage.removeItem("user");
              setUser(null);
              throw new Error("Invalid token");
            }
            throw new Error(`Token verification failed: ${res.status}`);
          })
          .then((userData) => {
            // Update user data from server
            setUser(userData);
            // Update cached user data
            localStorage.setItem("user", JSON.stringify(userData));
          })
          .catch((error) => {
            console.error("Auth verification error:", error);
            // Only clear if it's a 401, otherwise keep cached user
            if (error.message?.includes("401") || error.message?.includes("Invalid token")) {
              localStorage.removeItem("access_token");
              localStorage.removeItem("user");
              setUser(null);
            }
          })
          .finally(() => {
            setIsLoading(false);
          });
      } catch (error) {
        console.error("Auth initialization error:", error);
        // Don't clear on parse errors, just set loading to false
        setIsLoading(false);
      }
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = (token: string, userData: User) => {
    localStorage.setItem("access_token", token);
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};


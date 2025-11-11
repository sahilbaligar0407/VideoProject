import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2, Ban, CheckCircle, AlertTriangle, FileText, User, Shield, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/hooks/useAuth";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface User {
  id: number;
  email: string;
  password_hash: string;
  created_at: string;
  banned: boolean;
}

interface Report {
  id: number;
  user_id: number;
  report_type: string;
  clip_id?: string;
  error_code?: string;
  error_message?: string;
  error_logs?: string;
  comment?: string;
  created_at: string;
}

const AdminPortal = () => {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [banUserId, setBanUserId] = useState<number | null>(null);
  const [unbanUserId, setUnbanUserId] = useState<number | null>(null);
  const [deleteUserId, setDeleteUserId] = useState<number | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    if (authLoading) return;

    // Check if user is admin
    if (!isAuthenticated || !user || (user.id !== -1 && !user.is_admin)) {
      toast.error("Admin access required");
      navigate("/");
      return;
    }

    fetchData();
  }, [isAuthenticated, authLoading, user, navigate]);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        throw new Error("Not authenticated");
      }

      // Fetch users and reports in parallel
      const [usersResponse, reportsResponse] = await Promise.all([
        fetch("/api/v1/admin/users", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }),
        fetch("/api/v1/admin/reports", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }),
      ]);

      if (usersResponse.status === 401 || reportsResponse.status === 401) {
        toast.error("Session expired. Please sign in again.");
        navigate("/login");
        return;
      }

      if (!usersResponse.ok) {
        throw new Error(`Failed to fetch users: ${usersResponse.statusText}`);
      }

      if (!reportsResponse.ok) {
        throw new Error(`Failed to fetch reports: ${reportsResponse.statusText}`);
      }

      const usersData = await usersResponse.json();
      const reportsData = await reportsResponse.json();

      setUsers(usersData.users || []);
      setReports(reportsData.reports || []);
    } catch (err: any) {
      console.error("Error fetching admin data:", err);
      setError(err.message || "Failed to load admin data");
      toast.error(err.message || "Failed to load admin data");
    } finally {
      setIsLoading(false);
    }
  };

  const handleBanUser = async () => {
    if (!banUserId) return;

    setIsProcessing(true);
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        throw new Error("Not authenticated");
      }

      const response = await fetch(`/api/v1/admin/users/${banUserId}/ban`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        toast.error("Session expired. Please sign in again.");
        navigate("/login");
        return;
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Failed to ban user" }));
        throw new Error(errorData.detail || "Failed to ban user");
      }

      toast.success("User banned successfully");
      setBanUserId(null);
      fetchData(); // Refresh data
    } catch (err: any) {
      console.error("Error banning user:", err);
      toast.error(err.message || "Failed to ban user");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleUnbanUser = async () => {
    if (!unbanUserId) return;

    setIsProcessing(true);
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        throw new Error("Not authenticated");
      }

      const response = await fetch(`/api/v1/admin/users/${unbanUserId}/unban`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        toast.error("Session expired. Please sign in again.");
        navigate("/login");
        return;
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Failed to unban user" }));
        throw new Error(errorData.detail || "Failed to unban user");
      }

      toast.success("User unbanned successfully");
      setUnbanUserId(null);
      fetchData(); // Refresh data
    } catch (err: any) {
      console.error("Error unbanning user:", err);
      toast.error(err.message || "Failed to unban user");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDeleteUser = async () => {
    if (!deleteUserId) return;

    setIsProcessing(true);
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        throw new Error("Not authenticated");
      }

      const response = await fetch(`/api/v1/admin/users/${deleteUserId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        toast.error("Session expired. Please sign in again.");
        navigate("/login");
        return;
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Failed to delete user" }));
        throw new Error(errorData.detail || "Failed to delete user");
      }

      toast.success("User deleted successfully");
      setDeleteUserId(null);
      fetchData(); // Refresh data
    } catch (err: any) {
      console.error("Error deleting user:", err);
      toast.error(err.message || "Failed to delete user");
    } finally {
      setIsProcessing(false);
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 py-12 sm:py-20 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
            <p className="text-muted-foreground">Loading admin portal...</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 py-12 sm:py-20 flex items-center justify-center">
          <div className="text-center max-w-md">
            <h2 className="text-2xl font-bold mb-4">Error Loading Admin Portal</h2>
            <p className="text-muted-foreground mb-6">{error}</p>
            <Button onClick={() => navigate("/")}>Go Home</Button>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 py-12 sm:py-20">
        <div className="container px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="text-center mb-12">
              <div className="flex items-center justify-center gap-3 mb-4">
                <Shield className="h-8 w-8 text-primary" />
                <h1 className="text-3xl sm:text-4xl font-bold">Admin Portal</h1>
              </div>
              <p className="text-muted-foreground">
                Manage users, view reports, and monitor the system
              </p>
            </div>

            {/* Tabs */}
            <Tabs defaultValue="users" className="space-y-6">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="users" className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Users ({users.length})
                </TabsTrigger>
                <TabsTrigger value="reports" className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Reports ({reports.length})
                </TabsTrigger>
              </TabsList>

              {/* Users Tab */}
              <TabsContent value="users">
                <Card>
                  <CardHeader>
                    <CardTitle>All Users</CardTitle>
                    <CardDescription>
                      View and manage all registered users. Ban, unban, or delete users who violate TOS.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {users.length > 0 ? (
                      <div className="overflow-x-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>ID</TableHead>
                              <TableHead>Email</TableHead>
                              <TableHead>Password Hash</TableHead>
                              <TableHead>Created At</TableHead>
                              <TableHead>Status</TableHead>
                              <TableHead>Actions</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {users.map((user) => (
                              <TableRow key={user.id}>
                                <TableCell>{user.id}</TableCell>
                                <TableCell className="font-medium">{user.email}</TableCell>
                                <TableCell className="font-mono text-xs">
                                  {user.password_hash.substring(0, 20)}...
                                </TableCell>
                                <TableCell>
                                  {new Date(user.created_at).toLocaleDateString()}
                                </TableCell>
                                <TableCell>
                                  {user.banned ? (
                                    <span className="flex items-center gap-1 text-red-500">
                                      <Ban className="h-4 w-4" />
                                      Banned
                                    </span>
                                  ) : (
                                    <span className="flex items-center gap-1 text-green-500">
                                      <CheckCircle className="h-4 w-4" />
                                      Active
                                    </span>
                                  )}
                                </TableCell>
                                <TableCell>
                                  {user.id !== -1 && (
                                    <div className="flex flex-wrap gap-2">
                                      {user.banned ? (
                                        <Button
                                          variant="outline"
                                          size="sm"
                                          onClick={() => setUnbanUserId(user.id)}
                                          disabled={isProcessing}
                                        >
                                          <CheckCircle className="h-4 w-4 mr-1" />
                                          Unban
                                        </Button>
                                      ) : (
                                        <Button
                                          variant="destructive"
                                          size="sm"
                                          onClick={() => setBanUserId(user.id)}
                                          disabled={isProcessing}
                                        >
                                          <Ban className="h-4 w-4 mr-1" />
                                          Ban
                                        </Button>
                                      )}
                                      <Button
                                        variant="destructive"
                                        size="sm"
                                        onClick={() => setDeleteUserId(user.id)}
                                        disabled={isProcessing}
                                      >
                                        <Trash2 className="h-4 w-4 mr-1" />
                                        Delete
                                      </Button>
                                    </div>
                                  )}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    ) : (
                      <div className="text-center py-12">
                        <p className="text-muted-foreground">No users found</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Reports Tab */}
              <TabsContent value="reports">
                <Card>
                  <CardHeader>
                    <CardTitle>All Reports</CardTitle>
                    <CardDescription>
                      View user reports for clip issues and generation errors.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {reports.length > 0 ? (
                      <div className="space-y-4">
                        {reports.map((report) => (
                          <Card key={report.id}>
                            <CardHeader>
                              <div className="flex items-center justify-between">
                                <CardTitle className="text-lg">
                                  {report.report_type === "clip_not_viral"
                                    ? "Clip Not Viral Enough"
                                    : "Generation Error"}
                                </CardTitle>
                                <span className="text-sm text-muted-foreground">
                                  {new Date(report.created_at).toLocaleString()}
                                </span>
                              </div>
                              <CardDescription>
                                User ID: {report.user_id}
                                {report.clip_id && ` • Clip ID: ${report.clip_id}`}
                              </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-3">
                              {report.comment && (
                                <div>
                                  <p className="text-sm font-medium mb-1">Comment:</p>
                                  <p className="text-sm text-muted-foreground">{report.comment}</p>
                                </div>
                              )}
                              {report.error_code && (
                                <div>
                                  <p className="text-sm font-medium mb-1">Error Code:</p>
                                  <p className="text-sm font-mono text-red-500">
                                    {report.error_code}
                                  </p>
                                </div>
                              )}
                              {report.error_message && (
                                <div>
                                  <p className="text-sm font-medium mb-1">Error Message:</p>
                                  <p className="text-sm text-muted-foreground">
                                    {report.error_message}
                                  </p>
                                </div>
                              )}
                              {report.error_logs && (
                                <div>
                                  <p className="text-sm font-medium mb-1">Error Logs:</p>
                                  <pre className="text-xs bg-muted p-3 rounded overflow-auto max-h-40">
                                    {report.error_logs}
                                  </pre>
                                </div>
                              )}
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-12">
                        <p className="text-muted-foreground">No reports found</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </main>
      <Footer />

      {/* Ban User Confirmation Dialog */}
      <AlertDialog open={!!banUserId} onOpenChange={(open) => !open && setBanUserId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Ban User</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to ban this user? They will not be able to login or use any
              features until they are unbanned.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isProcessing}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleBanUser} disabled={isProcessing}>
              {isProcessing ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Ban User
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Unban User Confirmation Dialog */}
      <AlertDialog open={!!unbanUserId} onOpenChange={(open) => !open && setUnbanUserId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Unban User</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to unban this user? They will be able to login and use all
              features again.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isProcessing}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleUnbanUser} disabled={isProcessing}>
              {isProcessing ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Unban User
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete User Confirmation Dialog */}
      <AlertDialog open={!!deleteUserId} onOpenChange={(open) => !open && setDeleteUserId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete User</AlertDialogTitle>
            <AlertDialogDescription>
              Are you absolutely sure you want to delete this user? This action cannot be undone.
              This will permanently delete the user account and all associated data, including saved clips.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isProcessing}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteUser} disabled={isProcessing} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              {isProcessing ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Delete User
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default AdminPortal;


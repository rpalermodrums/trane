import { useAuth } from '@/hooks/useAuth';
import { Navigate, Outlet } from '@tanstack/react-router';

export const ProtectedRoute = () => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return <Outlet />;
}; 
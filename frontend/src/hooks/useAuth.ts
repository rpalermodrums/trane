import { useAuthStore } from '@/store/auth';
import { useNavigate } from '@tanstack/react-router';

interface LoginCredentials {
  username: string;
  password: string;
}

interface AuthResponse {
  access: string;
  refresh: string;
}

export function useAuth() {
  const { accessToken, refreshToken, setTokens, logout } = useAuthStore();
  const navigate = useNavigate();

  const login = async ({ username, password }: LoginCredentials) => {
    try {
      const response = await fetch('/api/auth/token/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data: AuthResponse = await response.json();
      setTokens(data.access, data.refresh);
      navigate({ to: '/' });
      return true;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const refreshAccessToken = async () => {
    if (!refreshToken) return false;

    try {
      const response = await fetch('/api/auth/token/refresh/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: refreshToken }),
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data: AuthResponse = await response.json();
      setTokens(data.access, data.refresh);
      return true;
    } catch (error) {
      console.error('Token refresh error:', error);
      return false;
    }
  };

  const handleLogout = () => {
    logout();
    navigate({ to: '/login' });
  };

  return {
    isAuthenticated: !!accessToken,
    login,
    logout: handleLogout,
    refreshAccessToken,
  };
} 
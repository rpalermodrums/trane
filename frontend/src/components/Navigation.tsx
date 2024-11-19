import { Link } from '@tanstack/react-router';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import {
  Home,
  Settings,
  LogOut,
  User,
  Music
} from 'lucide-react';

export const Navigation = () => {
  const { isAuthenticated, logout } = useAuth();

  return (
    <nav className="bg-background border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <Music className="h-8 w-8 text-primary" />
              <span className="ml-2 text-xl font-bold">Transcribe</span>
            </div>
            
            {isAuthenticated && (
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <Link
                  to="/"
                  className="inline-flex items-center px-1 pt-1 text-sm font-medium"
                  activeProps={{ className: 'border-b-2 border-primary' }}
                >
                  <Home className="mr-2 h-4 w-4" />
                  Dashboard
                </Link>
                
                <Link
                  to="/settings"
                  className="inline-flex items-center px-1 pt-1 text-sm font-medium"
                  activeProps={{ className: 'border-b-2 border-primary' }}
                >
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </Link>
              </div>
            )}
          </div>
          
          <div className="flex items-center">
            {isAuthenticated ? (
              <div className="flex items-center space-x-4">
                <Link
                  to="/settings"
                  className="p-2 rounded-full hover:bg-accent"
                >
                  <User className="h-5 w-5" />
                </Link>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={logout}
                  className="flex items-center"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  Logout
                </Button>
              </div>
            ) : (
              <Link
                to="/login"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary hover:bg-primary/90"
              >
                Login
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}; 
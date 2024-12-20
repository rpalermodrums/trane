import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { fetchAPI } from '@/api';
import { useToast } from '@/components/ui/use-toast';

interface UserSettings {
  email: string;
  defaultModel: string;
  emailNotifications: boolean;
}

export function Settings() {
  const { logout } = useAuth();
  const { toast } = useToast();
  const [settings, setSettings] = useState<UserSettings>({
    email: '',
    defaultModel: 'htdemucs',
    emailNotifications: true,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetchAPI('/settings/', {
        method: 'PUT',
        body: JSON.stringify(settings),
      });
      toast({
        title: 'Settings Updated',
        description: 'Your settings have been saved successfully.',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update settings.',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="container py-8 mx-auto">
      <h1 className="mb-6 text-2xl font-bold">Settings</h1>
      
      <form onSubmit={handleSubmit} className="max-w-md space-y-6">
        <div className="space-y-2">
          <label className="text-sm font-medium" htmlFor="email">Email</label>
          <Input
            type="email"
            id="email"
            value={settings.email}
            onChange={(e) => setSettings({ ...settings, email: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium" htmlFor="defaultModel">Default Model</label>
          <select
            id="defaultModel"
            value={settings.defaultModel}
            onChange={(e) => setSettings({ ...settings, defaultModel: e.target.value })}
            className="w-full p-2 border rounded"
          >
            <option value="htdemucs">HTDemucs</option>
            <option value="mdx">MDX</option>
            <option value="htdemucs_6s">HTDemucs 6-stem</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="emailNotifications"
            checked={settings.emailNotifications}
            onChange={(e) => setSettings({ 
              ...settings, 
              emailNotifications: e.target.checked 
            })}
          />
          <label htmlFor="emailNotifications" className="text-sm font-medium">
            Receive email notifications
          </label>
        </div>

        <div className="flex justify-between">
          <Button type="submit">Save Settings</Button>
          <Button variant="destructive" onClick={logout}>
            Logout
          </Button>
        </div>
      </form>
    </div>
  );
} 
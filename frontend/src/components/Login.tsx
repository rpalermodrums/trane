import React, { useState } from 'react';
import { useAuthStore } from '../store/auth';
import { useNavigate } from '@tanstack/react-router';
import { Button } from './ui/button';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const setTokens = useAuthStore((state: { setTokens: any }) => state.setTokens);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const response = await fetch('/api/auth/token/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (response.ok) {
      const data = await response.json();
      setTokens(data.access, data.refresh);
      navigate({ to: '/' });
    } else {
      const errorData = await response.json();
      alert(errorData.detail || 'Login failed. Please try again.');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <Button type="submit">Login</Button>
    </form>
  );
};

export default Login;

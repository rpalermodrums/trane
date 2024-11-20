import { useState, useEffect } from 'react';
import type { ToastActionElement, ToastProps } from '@/components/ui/toast';

interface ToastOptions {
  title?: string;
  description?: string;
  action?: ToastActionElement;
  variant?: 'default' | 'destructive';
  duration?: number;
}

let toastCount = 0;

export function useToast() {
  const [toasts, setToasts] = useState<ToastProps[]>([]);

  useEffect(() => {
    const timeouts = toasts.map((toast) => {
      if (toast.duration !== Number.POSITIVE_INFINITY) {
        return setTimeout(() => {
          setToasts((prevToasts) =>
            prevToasts.filter((t) => t.id !== toast.id)
          );
        }, toast.duration || 5000);
      }
    });

    return () => {
      for (const timeout of timeouts) {
        timeout && clearTimeout(timeout);
      }
    };
  }, [toasts]);

  function toast(options: ToastOptions) {
    const id = `toast-${toastCount++}`;
    const newToast: ToastProps = {
      id,
      ...options,
      duration: options.duration || 5000,
    };

    setToasts((prevToasts) => [...prevToasts, newToast]);
    return id;
  }

  return {
    toast,
    toasts,
    dismiss: (toastId: string) => {
      setToasts((prevToasts) =>
        prevToasts.filter((t) => t.id !== toastId)
      );
    },
  };
}

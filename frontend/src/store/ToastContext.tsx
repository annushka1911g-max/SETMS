// SETMS — Toast notification context
import React, { createContext, useCallback, useContext, useState } from 'react';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';

type ToastType = 'success' | 'error' | 'info' | 'warning';

interface Toast {
  id: string;
  type: ToastType;
  message: string;
}

interface ToastContextValue {
  addToast: (message: string, type?: ToastType) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
  warning: (message: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const ICON_MAP = {
  success: <CheckCircle size={16} className="text-green-400" />,
  error: <AlertCircle size={16} className="text-red-400" />,
  info: <Info size={16} className="text-blue-400" />,
  warning: <AlertTriangle size={16} className="text-yellow-400" />,
};

const COLOR_MAP = {
  success: 'border-l-green-500 bg-green-950/60',
  error: 'border-l-red-500 bg-red-950/60',
  info: 'border-l-blue-500 bg-blue-950/60',
  warning: 'border-l-yellow-500 bg-yellow-950/60',
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = crypto.randomUUID();
    setToasts(t => [...t, { id, type, message }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 5000);
  }, []);

  const success = useCallback((m: string) => addToast(m, 'success'), [addToast]);
  const error = useCallback((m: string) => addToast(m, 'error'), [addToast]);
  const info = useCallback((m: string) => addToast(m, 'info'), [addToast]);
  const warning = useCallback((m: string) => addToast(m, 'warning'), [addToast]);

  return (
    <ToastContext.Provider value={{ addToast, success, error, info, warning }}>
      {children}
      {/* Toast container */}
      <div className="fixed bottom-5 right-5 z-[9999] flex flex-col gap-2 w-80" aria-live="polite">
        {toasts.map(t => (
          <div
            key={t.id}
            className={`animate-fade-in flex items-start gap-3 rounded-lg border-l-4 p-3 shadow-xl backdrop-blur-sm ${COLOR_MAP[t.type]}`}
            style={{ border: '1px solid rgba(255,255,255,0.08)' }}
          >
            <span className="mt-0.5 shrink-0">{ICON_MAP[t.type]}</span>
            <p className="flex-1 text-sm text-slate-200 leading-snug">{t.message}</p>
            <button
              onClick={() => setToasts(ts => ts.filter(x => x.id !== t.id))}
              className="text-slate-500 hover:text-slate-300 transition-colors"
              aria-label="Dismiss notification"
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}

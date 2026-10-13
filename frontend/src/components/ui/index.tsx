// SETMS — Shared UI primitives
import React from 'react';
import { Loader2 } from 'lucide-react';

// ---- StatCard ----
interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  accent?: 'blue' | 'green' | 'red' | 'yellow' | 'purple';
  loading?: boolean;
}

const ACCENT_STYLES = {
  blue: 'border-blue-500/30 bg-blue-500/5',
  green: 'border-green-500/30 bg-green-500/5',
  red: 'border-red-500/30 bg-red-500/5',
  yellow: 'border-yellow-500/30 bg-yellow-500/5',
  purple: 'border-purple-500/30 bg-purple-500/5',
};
const ICON_ACCENT = {
  blue: 'text-blue-400',
  green: 'text-green-400',
  red: 'text-red-400',
  yellow: 'text-yellow-400',
  purple: 'text-purple-400',
};

export function StatCard({ label, value, sub, icon, accent = 'blue', loading }: StatCardProps) {
  return (
    <div
      className={`rounded-xl border p-4 transition-all hover:scale-[1.01] ${ACCENT_STYLES[accent]}`}
      style={{ background: 'rgba(15,23,42,0.8)' }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">{label}</p>
          {loading ? (
            <div className="skeleton h-8 w-20 rounded" />
          ) : (
            <p className="text-3xl font-bold text-white">{value}</p>
          )}
          {sub && !loading && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
        </div>
        {icon && (
          <div className={`shrink-0 ${ICON_ACCENT[accent]} opacity-80`}>{icon}</div>
        )}
      </div>
    </div>
  );
}

// ---- Badge ----
interface BadgeProps {
  label: string;
  variant?: 'critical' | 'high' | 'normal' | 'active' | 'pending' | 'completed' | 'cancelled';
  className?: string;
}
export function Badge({ label, variant = 'pending', className = '' }: BadgeProps) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold badge-${variant} ${className}`}>
      {label}
    </span>
  );
}

// ---- SeverityBadge ----
export function SeverityBadge({ severity }: { severity: string }) {
  const v = severity?.toLowerCase() as 'critical' | 'high' | 'normal';
  return <Badge label={severity} variant={v} />;
}

// ---- StatusBadge ----
export function StatusBadge({ status }: { status: string }) {
  const v = status?.toLowerCase() as 'active' | 'pending' | 'completed' | 'cancelled';
  return <Badge label={status} variant={v} />;
}

// ---- PageHeader ----
export function PageHeader({ title, subtitle, actions }: {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4 mb-6">
      <div>
        <h1 className="text-xl font-bold text-white">{title}</h1>
        {subtitle && <p className="text-sm text-slate-400 mt-0.5">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </div>
  );
}

// ---- EmptyState ----
export function EmptyState({ message, icon }: { message: string; icon?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-slate-500 gap-3">
      {icon && <div className="opacity-40">{icon}</div>}
      <p className="text-sm">{message}</p>
    </div>
  );
}

// ---- LoadingSpinner ----
export function LoadingSpinner({ label = 'Loading...' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-12 text-slate-400">
      <Loader2 size={20} className="animate-spin" />
      <span className="text-sm">{label}</span>
    </div>
  );
}

// ---- ErrorAlert ----
export function ErrorAlert({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex items-center gap-3 p-4 rounded-xl bg-red-950/40 border border-red-800/40 text-red-300">
      <span className="text-sm flex-1">{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-xs font-medium text-red-400 hover:text-red-300 underline"
        >
          Retry
        </button>
      )}
    </div>
  );
}

// ---- Button ----
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md';
  loading?: boolean;
  children: React.ReactNode;
}
const BTN_VARIANTS = {
  primary: 'bg-blue-600 hover:bg-blue-500 text-white border border-blue-500',
  secondary: 'bg-slate-700 hover:bg-slate-600 text-slate-200 border border-slate-600',
  danger: 'bg-red-700 hover:bg-red-600 text-white border border-red-600',
  ghost: 'bg-transparent hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-transparent',
};
const BTN_SIZES = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
};
export function Button({ variant = 'primary', size = 'md', loading, children, disabled, className = '', ...rest }: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center gap-2 font-medium rounded-lg transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed ${BTN_VARIANTS[variant]} ${BTN_SIZES[size]} ${className}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && <Loader2 size={14} className="animate-spin" />}
      {children}
    </button>
  );
}

// ---- Table ----
export function Table({ headers, children, loading }: {
  headers: string[];
  children: React.ReactNode;
  loading?: boolean;
}) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800" style={{ background: 'rgba(15,23,42,0.6)' }}>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-800">
            {headers.map(h => (
              <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            [...Array(5)].map((_, i) => (
              <tr key={i} className="border-b border-slate-800/40">
                {headers.map((_, j) => (
                  <td key={j} className="px-4 py-3">
                    <div className="skeleton h-4 rounded" style={{ width: `${60 + (i * j) % 30}%` }} />
                  </td>
                ))}
              </tr>
            ))
          ) : children}
        </tbody>
      </table>
    </div>
  );
}

// ---- Signal Indicator ----
export function SignalLight({ phase }: { phase: string }) {
  const cls = phase === 'GREEN' ? 'signal-green' : phase === 'YELLOW' ? 'signal-yellow' : 'signal-red';
  return (
    <span className={`inline-block w-3 h-3 rounded-full ${cls}`} title={`Signal: ${phase}`} />
  );
}

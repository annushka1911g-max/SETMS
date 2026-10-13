// SETMS — Traffic Signal Control Page
import { useEffect, useState, useCallback } from 'react';
import { TrafficCone, RefreshCw } from 'lucide-react';
import { signalApi, getErrorMessage } from '../api/client';
import {
  PageHeader, Table, Badge, ErrorAlert, LoadingSpinner, EmptyState, SignalLight, Button,
} from '../components/ui';
import { useToast } from '../store/ToastContext';
import type { TrafficSignal } from '../types';
import { useAuth } from '../store/AuthContext';

export function SignalsPage() {
  const { user } = useAuth();
  const { success, error: showError } = useToast();
  const [signals, setSignals] = useState<TrafficSignal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionId, setActionId] = useState<string | null>(null);

  const canControl = user?.role === 'ADMIN' || user?.role === 'TRAFFIC_OPERATOR';

  const fetchSignals = useCallback(async () => {
    try {
      setError(null);
      const data = await signalApi.list();
      setSignals(data.items);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, 10_000);
    return () => clearInterval(interval);
  }, [fetchSignals]);

  const setMode = async (id: string, mode: string) => {
    setActionId(id);
    try {
      await signalApi.setMode(id, mode, `Manual override by ${user?.full_name}`);
      success(`Signal mode set to ${mode}.`);
      fetchSignals();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setActionId(null);
    }
  };

  const statusColor: Record<string, string> = {
    OPERATIONAL: 'active',
    EMERGENCY_OVERRIDE: 'high',
    FAULT: 'critical',
    OFFLINE: 'cancelled',
    MAINTENANCE: 'normal',
  };

  return (
    <div className="p-6 animate-fade-in">
      <PageHeader
        title="Traffic Signal Control"
        subtitle="Monitor and control simulated signal states — 10s auto-refresh"
        actions={
          <Button size="sm" variant="secondary" onClick={fetchSignals}>
            <RefreshCw size={12} /> Refresh
          </Button>
        }
      />

      <div className="mb-4 p-3 rounded-lg bg-yellow-950/30 border border-yellow-800/40 text-xs text-yellow-400">
        ⚠️ <strong>Simulation Notice:</strong> All signal commands are simulated and do not connect to real traffic infrastructure.
      </div>

      {error && <ErrorAlert message={error} onRetry={fetchSignals} />}

      {loading ? (
        <LoadingSpinner />
      ) : signals.length === 0 ? (
        <EmptyState message="No signals registered." icon={<TrafficCone size={40} />} />
      ) : (
        <Table headers={['Signal', 'Intersection', 'Phase', 'Mode', 'Status', 'Actions']}>
          {signals.map(sig => (
            <tr key={sig.id} className="border-b border-slate-800/40 hover:bg-slate-800/20 transition-colors">
              <td className="px-4 py-3 text-sm font-mono font-semibold text-slate-200">{sig.name}</td>
              <td className="px-4 py-3 text-sm text-slate-400">{sig.intersection_name}</td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <SignalLight phase={sig.current_phase} />
                  <span className="text-sm text-slate-300">{sig.current_phase}</span>
                </div>
              </td>
              <td className="px-4 py-3">
                <Badge
                  label={sig.current_mode}
                  variant={sig.current_mode === 'EMERGENCY' ? 'critical' : 'pending'}
                />
              </td>
              <td className="px-4 py-3">
                <Badge label={sig.status} variant={(statusColor[sig.status] as any) ?? 'pending'} />
              </td>
              <td className="px-4 py-3">
                {canControl ? (
                  <div className="flex gap-1">
                    <button
                      disabled={sig.current_mode === 'NORMAL' || actionId === sig.id}
                      onClick={() => setMode(sig.id, 'NORMAL')}
                      className="px-2 py-1 rounded text-xs text-slate-400 hover:text-green-400 hover:bg-green-950/30 disabled:opacity-40 transition-all"
                    >
                      Normal
                    </button>
                    <button
                      disabled={sig.current_mode === 'EMERGENCY' || actionId === sig.id}
                      onClick={() => setMode(sig.id, 'EMERGENCY')}
                      className="px-2 py-1 rounded text-xs text-slate-400 hover:text-red-400 hover:bg-red-950/30 disabled:opacity-40 transition-all"
                    >
                      Emergency
                    </button>
                  </div>
                ) : (
                  <span className="text-xs text-slate-600">View only</span>
                )}
              </td>
            </tr>
          ))}
        </Table>
      )}
    </div>
  );
}

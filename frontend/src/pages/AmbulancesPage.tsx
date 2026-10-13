// SETMS — Ambulance Management Page
import { useEffect, useState, useCallback } from 'react';
import { Truck, MapPin, Clock } from 'lucide-react';
import { ambulanceApi, getErrorMessage } from '../api/client';
import {
  PageHeader, Table, Badge, EmptyState, ErrorAlert, LoadingSpinner, Button,
} from '../components/ui';
import type { Ambulance, AmbulanceStatus } from '../types';

const STATUS_COLORS: Record<AmbulanceStatus, string> = {
  AVAILABLE: 'active',
  EN_ROUTE: 'pending',
  AT_SCENE: 'high',
  TRANSPORTING: 'high',
  OUT_OF_SERVICE: 'cancelled',
};

function isStale(updatedAt: string | null): boolean {
  if (!updatedAt) return true;
  const diff = Date.now() - new Date(updatedAt).getTime();
  return diff > 5 * 60 * 1000; // >5 minutes = stale
}

export function AmbulancesPage() {
  const [ambulances, setAmbulances] = useState<Ambulance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const fetchAmbulances = useCallback(async () => {
    try {
      setError(null);
      const data = await ambulanceApi.list({ limit: 100 });
      setAmbulances(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAmbulances();
    const interval = setInterval(fetchAmbulances, 15_000);
    return () => clearInterval(interval);
  }, [fetchAmbulances]);

  return (
    <div className="p-6 animate-fade-in">
      <PageHeader
        title="Ambulance Management"
        subtitle={`${total} registered ambulances`}
        actions={
          <Button size="sm" onClick={fetchAmbulances}>
            <Truck size={14} /> Refresh
          </Button>
        }
      />

      {error && <ErrorAlert message={error} onRetry={fetchAmbulances} />}

      {loading ? (
        <LoadingSpinner />
      ) : ambulances.length === 0 ? (
        <EmptyState message="No ambulances registered yet." icon={<Truck size={40} />} />
      ) : (
        <Table
          headers={['Call Sign', 'Registration', 'Type', 'Status', 'Location', 'Last Update']}
        >
          {ambulances.map(amb => (
            <tr key={amb.id} className="border-b border-slate-800/40 hover:bg-slate-800/20 transition-colors">
              <td className="px-4 py-3 font-mono text-sm font-semibold text-slate-200">
                {amb.call_sign}
              </td>
              <td className="px-4 py-3 text-sm text-slate-300 font-mono">{amb.registration_number}</td>
              <td className="px-4 py-3 text-sm text-slate-400">{amb.vehicle_type}</td>
              <td className="px-4 py-3">
                <Badge
                  label={amb.status.replace('_', ' ')}
                  variant={(STATUS_COLORS[amb.status] as any) ?? 'pending'}
                />
              </td>
              <td className="px-4 py-3">
                {amb.current_lat != null ? (
                  <span className="flex items-center gap-1 text-xs text-slate-400">
                    <MapPin size={11} className="text-blue-400" />
                    {amb.current_lat.toFixed(4)}, {amb.current_lng?.toFixed(4)}
                  </span>
                ) : (
                  <span className="text-xs text-slate-600">No location</span>
                )}
              </td>
              <td className="px-4 py-3">
                {amb.location_updated_at ? (
                  <span className={`flex items-center gap-1 text-xs ${
                    isStale(amb.location_updated_at) ? 'text-yellow-500' : 'text-slate-400'
                  }`}>
                    <Clock size={11} />
                    {isStale(amb.location_updated_at) ? '⚠️ ' : ''}
                    {new Date(amb.location_updated_at).toLocaleTimeString()}
                  </span>
                ) : (
                  <span className="text-xs text-slate-600">Never</span>
                )}
              </td>
            </tr>
          ))}
        </Table>
      )}

      <p className="text-xs text-slate-600 mt-4">
        ⚠️ Location data may be simulated. Auto-refreshes every 15 seconds.
      </p>
    </div>
  );
}

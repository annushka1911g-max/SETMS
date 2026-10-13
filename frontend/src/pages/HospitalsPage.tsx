// SETMS — Hospitals Page
import { useEffect, useState, useCallback } from 'react';
import { Hospital as HospitalIcon, Activity } from 'lucide-react';
import { hospitalApi, getErrorMessage } from '../api/client';
import {
  PageHeader, Table, Badge, ErrorAlert, LoadingSpinner, EmptyState,
} from '../components/ui';
import { useToast } from '../store/ToastContext';
import type { Hospital } from '../types';

export function HospitalsPage() {
  const { success, error: showError } = useToast();
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [incoming, setIncoming] = useState<any[]>([]);

  const fetchAll = useCallback(async () => {
    try {
      setError(null);
      const [hospData, incomingData] = await Promise.all([
        hospitalApi.list(),
        hospitalApi.incoming(),
      ]);
      setHospitals(hospData.items);
      setIncoming(incomingData.items ?? []);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const toggleReadiness = async (hospital: Hospital) => {
    try {
      await hospitalApi.updateReadiness(hospital.id, { is_ready: !hospital.is_ready });
      success(`${hospital.name} readiness updated.`);
      fetchAll();
    } catch (err) { showError(getErrorMessage(err)); }
  };

  return (
    <div className="p-6 animate-fade-in">
      <PageHeader title="Hospital Coordination" subtitle="Monitor hospital readiness and incoming ambulances" />

      {error && <ErrorAlert message={error} onRetry={fetchAll} />}

      {/* Incoming ambulances panel */}
      {incoming.length > 0 && (
        <div className="mb-5 p-4 rounded-xl border border-red-800/40 bg-red-950/20">
          <div className="flex items-center gap-2 mb-3">
            <Activity size={16} className="text-red-400 animate-pulse-dot" />
            <h3 className="text-sm font-semibold text-red-300">Incoming Ambulances ({incoming.length})</h3>
          </div>
          <div className="space-y-2">
            {incoming.map((item: any, i: number) => (
              <div key={i} className="flex items-center justify-between px-3 py-2 rounded-lg bg-red-950/30 text-sm">
                <span className="text-slate-200">{item.hospital.name}</span>
                <Badge label={item.severity} variant={item.severity.toLowerCase() as any} />
                <span className="font-mono text-xs text-slate-400">{item.reference_code}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : hospitals.length === 0 ? (
        <EmptyState message="No hospitals registered." icon={<HospitalIcon size={40} />} />
      ) : (
        <Table headers={['Hospital', 'Address', 'Emergency Bays', 'Readiness', 'Actions']}>
          {hospitals.map(h => (
            <tr key={h.id} className="border-b border-slate-800/40 hover:bg-slate-800/20 transition-colors">
              <td className="px-4 py-3 text-sm font-semibold text-slate-200">{h.name}</td>
              <td className="px-4 py-3 text-xs text-slate-400">{h.address}</td>
              <td className="px-4 py-3 text-sm text-slate-300">
                {h.emergency_bays_available}/{h.emergency_bays_total}
                <span className="text-xs text-slate-500 ml-1">available</span>
              </td>
              <td className="px-4 py-3">
                <Badge label={h.is_ready ? 'READY' : 'NOT READY'} variant={h.is_ready ? 'active' : 'cancelled'} />
              </td>
              <td className="px-4 py-3">
                <button
                  onClick={() => toggleReadiness(h)}
                  className={`px-2 py-1 rounded text-xs font-medium transition-all ${
                    h.is_ready
                      ? 'text-yellow-400 hover:bg-yellow-950/30'
                      : 'text-green-400 hover:bg-green-950/30'
                  }`}
                >
                  Mark {h.is_ready ? 'Not Ready' : 'Ready'}
                </button>
              </td>
            </tr>
          ))}
        </Table>
      )}
    </div>
  );
}

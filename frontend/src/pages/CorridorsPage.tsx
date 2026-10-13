// SETMS — Green Corridor Planner Page
import { useEffect, useState, useCallback, type FormEvent } from 'react';
import { Route, CheckCircle, XCircle, Plus } from 'lucide-react';
import { corridorApi, emergencyApi, getErrorMessage } from '../api/client';
import {
  PageHeader, Table, Badge, ErrorAlert, LoadingSpinner, EmptyState, Button,
} from '../components/ui';
import { useToast } from '../store/ToastContext';
import type { Corridor, Emergency } from '../types';
import { useAuth } from '../store/AuthContext';

export function CorridorsPage() {
  const { user } = useAuth();
  const { success, error: showError } = useToast();
  const [corridors, setCorridors] = useState<Corridor[]>([]);
  const [emergencies, setEmergencies] = useState<Emergency[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showPlan, setShowPlan] = useState(false);
  const [selectedEmergency, setSelectedEmergency] = useState('');
  const [planning, setPlanning] = useState(false);

  const canApprove = user?.role === 'ADMIN' || user?.role === 'TRAFFIC_OPERATOR';

  const fetchAll = useCallback(async () => {
    try {
      setError(null);
      const [corrData, emgData] = await Promise.all([
        corridorApi.list(),
        emergencyApi.list({ status: 'ACTIVE', limit: 50 }),
      ]);
      setCorridors(corrData.items);
      setEmergencies(emgData.items);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handlePlan = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedEmergency) return;
    setPlanning(true);
    try {
      await corridorApi.plan(selectedEmergency);
      success('Corridor proposed. Awaiting operator approval.');
      setShowPlan(false);
      fetchAll();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setPlanning(false);
    }
  };

  const handleApprove = async (id: string) => {
    try {
      await corridorApi.approve(id);
      success('Corridor approved and activated.');
      fetchAll();
    } catch (err) { showError(getErrorMessage(err)); }
  };

  const handleCancel = async (id: string) => {
    if (!confirm('Cancel this corridor?')) return;
    try {
      await corridorApi.cancel(id);
      success('Corridor cancelled.');
      fetchAll();
    } catch (err) { showError(getErrorMessage(err)); }
  };

  const statusVariant: Record<string, string> = {
    PROPOSED: 'pending', APPROVED: 'normal', ACTIVE: 'active',
    SUSPENDED: 'high', COMPLETED: 'completed', CANCELLED: 'cancelled', EXPIRED: 'cancelled',
  };

  return (
    <div className="p-6 animate-fade-in">
      <PageHeader
        title="Green Corridor Planner"
        subtitle="Propose, approve, and monitor emergency green corridors"
        actions={
          <Button size="sm" onClick={() => setShowPlan(s => !s)}>
            <Plus size={14} /> Plan Corridor
          </Button>
        }
      />

      {error && <ErrorAlert message={error} onRetry={fetchAll} />}

      {showPlan && (
        <form onSubmit={handlePlan} className="card-glass p-5 mb-5 animate-fade-in">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">Propose New Corridor</h3>
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <label className="block text-xs text-slate-400 mb-1">Active Emergency</label>
              <select
                required value={selectedEmergency}
                onChange={e => setSelectedEmergency(e.target.value)}
                className="w-full px-3 py-2 rounded-lg text-sm text-slate-200 outline-none"
                style={{ background: '#0f172a', border: '1px solid #334155' }}
              >
                <option value="">Select active emergency...</option>
                {emergencies.map(em => (
                  <option key={em.id} value={em.id}>
                    {em.reference_code} — {em.severity}
                  </option>
                ))}
              </select>
            </div>
            <Button type="submit" loading={planning}>Propose</Button>
            <Button type="button" variant="ghost" onClick={() => setShowPlan(false)}>Cancel</Button>
          </div>
          <p className="text-xs text-slate-600 mt-2">
            Full route optimization (Milestone 5/6) will auto-select intersections based on the ambulance position.
          </p>
        </form>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : corridors.length === 0 ? (
        <EmptyState message="No corridors planned yet." icon={<Route size={40} />} />
      ) : (
        <Table headers={['Emergency ID', 'Status', 'Created', 'Approved', 'Actions']}>
          {corridors.map(c => (
            <tr key={c.id} className="border-b border-slate-800/40 hover:bg-slate-800/20 transition-colors">
              <td className="px-4 py-3 font-mono text-xs text-slate-400">{c.emergency_id.slice(0, 12)}…</td>
              <td className="px-4 py-3">
                <Badge label={c.status} variant={(statusVariant[c.status] as any) ?? 'pending'} />
              </td>
              <td className="px-4 py-3 text-xs text-slate-500">
                {new Date(c.created_at).toLocaleString()}
              </td>
              <td className="px-4 py-3 text-xs text-slate-500">
                {c.approved_at ? new Date(c.approved_at).toLocaleTimeString() : '—'}
              </td>
              <td className="px-4 py-3">
                <div className="flex gap-1">
                  {c.status === 'PROPOSED' && canApprove && (
                    <button
                      onClick={() => handleApprove(c.id)}
                      className="flex items-center gap-1 px-2 py-1 rounded text-xs text-green-400 hover:bg-green-950/30 transition-all"
                    >
                      <CheckCircle size={11} /> Approve
                    </button>
                  )}
                  {['PROPOSED', 'APPROVED', 'ACTIVE'].includes(c.status) && (
                    <button
                      onClick={() => handleCancel(c.id)}
                      className="flex items-center gap-1 px-2 py-1 rounded text-xs text-red-400 hover:bg-red-950/30 transition-all"
                    >
                      <XCircle size={11} /> Cancel
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </Table>
      )}
    </div>
  );
}

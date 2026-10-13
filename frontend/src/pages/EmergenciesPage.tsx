// SETMS — Emergency Requests Page
import { useEffect, useState, useCallback, type FormEvent } from 'react';
import { AlertTriangle, Plus, CheckCircle, XCircle, Zap } from 'lucide-react';
import { emergencyApi, ambulanceApi, hospitalApi, getErrorMessage } from '../api/client';
import {
  PageHeader, Table, SeverityBadge, StatusBadge, ErrorAlert,
  LoadingSpinner, EmptyState, Button,
} from '../components/ui';
import { useToast } from '../store/ToastContext';
import type { Emergency, Ambulance, Hospital } from '../types';

export function EmergenciesPage() {
  const { success, error: showError } = useToast();
  const [emergencies, setEmergencies] = useState<Emergency[]>([]);
  const [ambulances, setAmbulances] = useState<Ambulance[]>([]);
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    ambulance_id: '', destination_hospital_id: '', severity: 'HIGH', description: '',
  });

  const fetchAll = useCallback(async () => {
    try {
      setError(null);
      const [emgData, ambData, hospData] = await Promise.all([
        emergencyApi.list({ limit: 100 }),
        ambulanceApi.list({ limit: 100 }),
        hospitalApi.list(),
      ]);
      setEmergencies(emgData.items);
      setAmbulances(ambData.items);
      setHospitals(hospData.items);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.ambulance_id) return;
    setCreating(true);
    try {
      await emergencyApi.create({
        ambulance_id: form.ambulance_id,
        destination_hospital_id: form.destination_hospital_id || undefined,
        severity: form.severity,
        description: form.description || undefined,
      });
      success('Emergency created successfully.');
      setShowCreate(false);
      setForm({ ambulance_id: '', destination_hospital_id: '', severity: 'HIGH', description: '' });
      fetchAll();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setCreating(false);
    }
  };

  const handleActivate = async (id: string) => {
    try {
      await emergencyApi.activate(id);
      success('Emergency activated.');
      fetchAll();
    } catch (err) { showError(getErrorMessage(err)); }
  };

  const handleComplete = async (id: string) => {
    try {
      await emergencyApi.complete(id);
      success('Emergency completed.');
      fetchAll();
    } catch (err) { showError(getErrorMessage(err)); }
  };

  const handleCancel = async (id: string) => {
    if (!confirm('Cancel this emergency?')) return;
    try {
      await emergencyApi.cancel(id);
      success('Emergency cancelled.');
      fetchAll();
    } catch (err) { showError(getErrorMessage(err)); }
  };

  const inputCls = "w-full px-3 py-2 rounded-lg text-sm text-slate-200 outline-none transition-all";
  const inputStyle = { background: '#0f172a', border: '1px solid #334155' };

  return (
    <div className="p-6 animate-fade-in">
      <PageHeader
        title="Emergency Requests"
        subtitle="Manage emergency lifecycle — create, activate, complete"
        actions={
          <Button size="sm" onClick={() => setShowCreate(s => !s)}>
            <Plus size={14} /> New Emergency
          </Button>
        }
      />

      {error && <ErrorAlert message={error} onRetry={fetchAll} />}

      {/* Create Form */}
      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="card-glass p-5 mb-5 animate-fade-in"
        >
          <h3 className="text-sm font-semibold text-slate-200 mb-4">Create Emergency Request</h3>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Ambulance *</label>
              <select
                required value={form.ambulance_id}
                onChange={e => setForm(f => ({ ...f, ambulance_id: e.target.value }))}
                className={inputCls} style={inputStyle}
              >
                <option value="">Select ambulance</option>
                {ambulances.filter(a => a.status === 'AVAILABLE').map(a => (
                  <option key={a.id} value={a.id}>{a.call_sign} ({a.registration_number})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Destination Hospital</label>
              <select
                value={form.destination_hospital_id}
                onChange={e => setForm(f => ({ ...f, destination_hospital_id: e.target.value }))}
                className={inputCls} style={inputStyle}
              >
                <option value="">Select hospital (optional)</option>
                {hospitals.map(h => (
                  <option key={h.id} value={h.id}>{h.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Severity *</label>
              <select
                value={form.severity}
                onChange={e => setForm(f => ({ ...f, severity: e.target.value }))}
                className={inputCls} style={inputStyle}
              >
                <option value="CRITICAL">CRITICAL</option>
                <option value="HIGH">HIGH</option>
                <option value="NORMAL">NORMAL</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Description</label>
              <input
                value={form.description}
                onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                className={inputCls} style={inputStyle}
                placeholder="Optional notes..."
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button type="submit" loading={creating}>Create Emergency</Button>
            <Button type="button" variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
          </div>
        </form>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : emergencies.length === 0 ? (
        <EmptyState message="No emergencies found." icon={<AlertTriangle size={40} />} />
      ) : (
        <Table headers={['Reference', 'Severity', 'Status', 'Ambulance', 'Created', 'Actions']}>
          {emergencies.map(e => {
            const amb = ambulances.find(a => a.id === e.ambulance_id);
            return (
              <tr key={e.id} className="border-b border-slate-800/40 hover:bg-slate-800/20 transition-colors">
                <td className="px-4 py-3 font-mono text-sm font-bold text-slate-200">{e.reference_code}</td>
                <td className="px-4 py-3"><SeverityBadge severity={e.severity} /></td>
                <td className="px-4 py-3"><StatusBadge status={e.status} /></td>
                <td className="px-4 py-3 text-sm text-slate-400">{amb?.call_sign ?? e.ambulance_id.slice(0, 8)}</td>
                <td className="px-4 py-3 text-xs text-slate-500">
                  {new Date(e.created_at).toLocaleString()}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1">
                    {e.status === 'PENDING' && (
                      <button onClick={() => handleActivate(e.id)}
                        className="flex items-center gap-1 text-xs text-green-400 hover:text-green-300 px-2 py-1 rounded hover:bg-green-950/30 transition-all">
                        <Zap size={11} /> Activate
                      </button>
                    )}
                    {e.status === 'ACTIVE' && (
                      <button onClick={() => handleComplete(e.id)}
                        className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 px-2 py-1 rounded hover:bg-blue-950/30 transition-all">
                        <CheckCircle size={11} /> Complete
                      </button>
                    )}
                    {(e.status === 'PENDING' || e.status === 'ACTIVE') && (
                      <button onClick={() => handleCancel(e.id)}
                        className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300 px-2 py-1 rounded hover:bg-red-950/30 transition-all">
                        <XCircle size={11} /> Cancel
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </Table>
      )}
    </div>
  );
}

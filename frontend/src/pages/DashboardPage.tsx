// SETMS — Overview Dashboard Page
import { useCallback, useEffect, useState } from 'react';
import {
  Truck, AlertTriangle, Route, TrafficCone, Hospital,
  Clock, TrendingUp, Activity, RefreshCw,
} from 'lucide-react';
import { dashboardApi } from '../api/client';
import {
  StatCard, PageHeader, ErrorAlert, Badge, SeverityBadge, StatusBadge,
} from '../components/ui';
import type { DashboardSummary } from '../types';
import { getErrorMessage } from '../api/client';

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString([], {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [activity, setActivity] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const [sumData, actData] = await Promise.all([
        dashboardApi.summary(),
        dashboardApi.activity(20),
      ]);
      setSummary(sumData);
      setActivity(actData.activities ?? []);
      setLastRefresh(new Date());
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30_000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return (
    <div className="p-6 animate-fade-in">
      <PageHeader
        title="Operations Overview"
        subtitle={`Last updated: ${lastRefresh.toLocaleTimeString()}`}
        actions={
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-200 border border-slate-700 hover:bg-slate-800 transition-all disabled:opacity-50"
          >
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        }
      />

      {error && <ErrorAlert message={error} onRetry={fetchData} />}

      {/* Stat Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          label="Active Emergencies"
          value={summary?.emergencies.active ?? 0}
          sub={`${summary?.emergencies.today ?? 0} today`}
          icon={<AlertTriangle size={24} />}
          accent="red"
          loading={loading}
        />
        <StatCard
          label="Active Ambulances"
          value={summary?.ambulances.active ?? 0}
          sub={`${summary?.ambulances.available ?? 0} available`}
          icon={<Truck size={24} />}
          accent="blue"
          loading={loading}
        />
        <StatCard
          label="Active Corridors"
          value={summary?.corridors.active ?? 0}
          icon={<Route size={24} />}
          accent="green"
          loading={loading}
        />
        <StatCard
          label="Signals Overridden"
          value={summary?.signals.in_emergency_override ?? 0}
          sub={`of ${summary?.signals.total ?? 0} total`}
          icon={<TrafficCone size={24} />}
          accent="yellow"
          loading={loading}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <StatCard
          label="Hospitals Ready"
          value={`${summary?.hospitals.ready ?? 0} / ${summary?.hospitals.total ?? 0}`}
          icon={<Hospital size={24} />}
          accent="green"
          loading={loading}
        />
        <StatCard
          label="Avg Journey (7d)"
          value={summary?.analytics.avg_journey_duration_minutes_7d != null
            ? `${summary.analytics.avg_journey_duration_minutes_7d} min`
            : '—'}
          icon={<Clock size={24} />}
          accent="blue"
          loading={loading}
        />
        <StatCard
          label="Est. Time Saved (total)"
          value={summary ? `${summary.analytics.estimated_time_saved_minutes_total} min` : '—'}
          sub="⚠️ Simulated estimate"
          icon={<TrendingUp size={24} />}
          accent="purple"
          loading={loading}
        />
      </div>

      {/* Activity Feed */}
      <div className="rounded-xl border border-slate-800 overflow-hidden" style={{ background: 'rgba(15,23,42,0.6)' }}>
        <div className="flex items-center gap-2 px-5 py-4 border-b border-slate-800">
          <Activity size={16} className="text-blue-400" />
          <h2 className="text-sm font-semibold text-slate-200">Recent Activity</h2>
          <span className="ml-auto text-xs text-slate-500">Auto-refreshes every 30s</span>
        </div>

        {loading ? (
          <div className="p-4 space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex gap-3">
                <div className="skeleton w-2 h-2 rounded-full mt-1.5 shrink-0" />
                <div className="flex-1 space-y-1.5">
                  <div className="skeleton h-3 rounded w-3/4" />
                  <div className="skeleton h-2.5 rounded w-1/3" />
                </div>
              </div>
            ))}
          </div>
        ) : activity.length === 0 ? (
          <p className="text-center text-sm text-slate-500 py-10">No recent activity</p>
        ) : (
          <ul className="divide-y divide-slate-800/60">
            {activity.map((item, idx) => (
              <li key={`${item.id}-${idx}`} className="flex items-start gap-3 px-5 py-3 hover:bg-slate-800/30 transition-colors">
                <span className={`shrink-0 mt-1.5 w-2 h-2 rounded-full ${
                  item.type === 'emergency' ? 'bg-red-400' : 'bg-blue-400'
                }`} />
                <div className="flex-1 min-w-0">
                  {item.type === 'emergency' ? (
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium text-slate-200">
                        Emergency {item.reference_code}
                      </span>
                      <SeverityBadge severity={item.severity} />
                      <StatusBadge status={item.status} />
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm text-slate-300">
                        Signal phase → <strong>{item.to_phase}</strong>
                      </span>
                      <Badge label={item.trigger} variant="pending" />
                    </div>
                  )}
                  <p className="text-xs text-slate-500 mt-0.5">{formatDateTime(item.timestamp)}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

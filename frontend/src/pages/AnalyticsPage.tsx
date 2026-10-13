// SETMS — Analytics & Reports Page
import { useEffect, useState } from 'react';
import { TrendingUp, AlertTriangle } from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip,
  PieChart, Pie, Cell, Legend,
} from 'recharts';
import { analyticsApi, getErrorMessage } from '../api/client';
import { PageHeader, ErrorAlert, LoadingSpinner, StatCard } from '../components/ui';

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  NORMAL: '#eab308',
};

export function AnalyticsPage() {
  const [summary, setSummary] = useState<any>(null);
  const [emergencyData, setEmergencyData] = useState<any[]>([]);
  const [perfData, setPerfData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      analyticsApi.summary(),
      analyticsApi.emergencies(30),
      analyticsApi.performance(),
    ])
      .then(([sum, emg, perf]) => {
        setSummary(sum);
        // Group by date for bar chart
        const byDate: Record<string, number> = {};
        for (const row of emg.data) {
          byDate[row.date] = (byDate[row.date] ?? 0) + row.count;
        }
        setEmergencyData(Object.entries(byDate).slice(-14).map(([date, count]) => ({ date, count })));
        setPerfData(perf);
      })
      .catch(err => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  const pieData = perfData?.severity_distribution?.map((r: any) => ({
    name: r.severity, value: r.count, color: SEVERITY_COLORS[r.severity] ?? '#64748b',
  })) ?? [];

  return (
    <div className="p-6 animate-fade-in">
      <PageHeader title="Analytics & Reports" subtitle="Emergency performance metrics — clearly labeled by data source" />

      {error && <ErrorAlert message={error} />}

      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <StatCard
              label="Total Emergencies"
              value={summary?.total_emergencies ?? 0}
              icon={<AlertTriangle size={24} />}
              accent="red"
            />
            <StatCard
              label="Avg Journey Duration"
              value={summary?.avg_journey_duration_minutes != null
                ? `${summary.avg_journey_duration_minutes} min` : '—'}
              icon={<TrendingUp size={24} />}
              accent="blue"
            />
            <StatCard
              label="Est. Time Saved (total)"
              value={`${summary?.estimated_time_saved_minutes?.value ?? 0} min`}
              sub="⚠️ Simulated estimate — not empirically validated"
              icon={<TrendingUp size={24} />}
              accent="green"
            />
          </div>

          {/* Metric definition notice */}
          <div className="mb-5 p-3 rounded-lg bg-blue-950/30 border border-blue-800/40 text-xs text-blue-300">
            <strong>Metric Definition:</strong> {summary?.estimated_time_saved_minutes?.definition}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Bar Chart */}
            <div className="rounded-xl border border-slate-800 p-5" style={{ background: 'rgba(15,23,42,0.6)' }}>
              <h3 className="text-sm font-semibold text-slate-200 mb-4">Emergencies — Last 14 Days</h3>
              {emergencyData.length === 0 ? (
                <p className="text-xs text-slate-500 py-8 text-center">No data yet. Create some emergencies first.</p>
              ) : (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={emergencyData}>
                    <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 10 }} />
                    <YAxis tick={{ fill: '#64748b', fontSize: 10 }} />
                    <Tooltip
                      contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                      labelStyle={{ color: '#94a3b8' }}
                    />
                    <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Pie Chart */}
            <div className="rounded-xl border border-slate-800 p-5" style={{ background: 'rgba(15,23,42,0.6)' }}>
              <h3 className="text-sm font-semibold text-slate-200 mb-4">Severity Distribution</h3>
              {pieData.length === 0 ? (
                <p className="text-xs text-slate-500 py-8 text-center">No data yet.</p>
              ) : (
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80}
                      dataKey="value" nameKey="name" paddingAngle={3}>
                      {pieData.map((entry: any, i: number) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Pie>
                    <Legend
                      formatter={(value) => <span style={{ color: '#94a3b8', fontSize: 12 }}>{value}</span>}
                    />
                    <Tooltip
                      contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

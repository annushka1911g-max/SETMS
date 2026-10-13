// =============================================================================
// SETMS — AI Computer Vision & Traffic Density Estimation (Milestone 8)
// Interactive YOLOv8 detection workbench with vehicle classification,
// bounding box display, emergency vehicle candidate identification, and density metrics.
// =============================================================================
import { useState } from 'react';
import {
  Cpu, Eye, AlertCircle, Car, Truck,
  Activity, ShieldCheck, RefreshCw,
} from 'lucide-react';
import { PageHeader, StatCard, Button } from '../components/ui';

interface DetectionBox {
  class_name: string;
  confidence: number;
  box: [number, number, number, number]; // [x1, y1, x2, y2] percentages
  is_emergency_candidate: boolean;
}

export function AIDetectionPage() {
  const [selectedIntersection, setSelectedIntersection] = useState('SIG-B2');
  const [isProcessing, setIsProcessing] = useState(false);
  const [modelType] = useState('YOLOv8 Nano (Traffic Optimized)');
  const [inferenceMode] = useState<'SIMULATED' | 'REAL'>('SIMULATED');

  // Simulated detection state with realistic bounding boxes
  const [detections, setDetections] = useState<DetectionBox[]>([
    { class_name: 'Ambulance', confidence: 0.94, box: [25, 45, 45, 75], is_emergency_candidate: true },
    { class_name: 'Car', confidence: 0.88, box: [10, 30, 24, 48], is_emergency_candidate: false },
    { class_name: 'Bus', confidence: 0.91, box: [55, 35, 75, 65], is_emergency_candidate: false },
    { class_name: 'Car', confidence: 0.82, box: [78, 50, 92, 70], is_emergency_candidate: false },
    { class_name: 'Motorcycle', confidence: 0.79, box: [48, 55, 54, 68], is_emergency_candidate: false },
  ]);

  const [densityScore, setDensityScore] = useState(68); // 0 - 100
  const [fps, setFps] = useState(28.4);

  const runInference = () => {
    setIsProcessing(true);
    setTimeout(() => {
      // Generate randomized realistic detection results for demonstration
      const count = Math.floor(Math.random() * 6) + 3;
      const hasAmbulance = Math.random() > 0.3;
      const newDets: DetectionBox[] = [];

      if (hasAmbulance) {
        newDets.push({
          class_name: 'Ambulance Candidate',
          confidence: Number((0.85 + Math.random() * 0.13).toFixed(2)),
          box: [30 + Math.random() * 20, 40 + Math.random() * 20, 50 + Math.random() * 20, 65 + Math.random() * 20],
          is_emergency_candidate: true,
        });
      }

      for (let i = 0; i < count; i++) {
        const classes = ['Car', 'Bus', 'Motorcycle', 'Truck'];
        const cls = classes[Math.floor(Math.random() * classes.length)];
        const x1 = Math.floor(Math.random() * 70);
        const y1 = Math.floor(Math.random() * 60) + 10;
        newDets.push({
          class_name: cls,
          confidence: Number((0.75 + Math.random() * 0.22).toFixed(2)),
          box: [x1, y1, x1 + 15, y1 + 20],
          is_emergency_candidate: false,
        });
      }

      setDetections(newDets);
      setDensityScore(Math.min(100, Math.floor(newDets.length * 11 + Math.random() * 15)));
      setFps(Number((24 + Math.random() * 8).toFixed(1)));
      setIsProcessing(false);
    }, 600);
  };

  const getDensityLevel = (score: number) => {
    if (score >= 80) return { label: 'SEVERE CONGESTION', color: 'text-red-400 bg-red-500/10 border-red-500/30' };
    if (score >= 60) return { label: 'HIGH TRAFFIC', color: 'text-amber-400 bg-amber-500/10 border-amber-500/30' };
    if (score >= 35) return { label: 'MODERATE TRAFFIC', color: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30' };
    return { label: 'FREE FLOW', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' };
  };

  const density = getDensityLevel(densityScore);
  const emergencyFound = detections.some((d) => d.is_emergency_candidate);

  return (
    <div className="p-6 space-y-6 animate-fade-in max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <PageHeader
            title="AI Detection & Traffic Density Estimation"
            subtitle="YOLOv8 computer vision model running on intersection camera feeds to detect congestion and emergency vehicles."
          />
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
            Inference: {inferenceMode}
          </div>
          <Button variant="primary" onClick={runInference} disabled={isProcessing}>
            <RefreshCw size={15} className={`mr-2 ${isProcessing ? 'animate-spin' : ''}`} />
            {isProcessing ? 'Detecting...' : 'Run Frame Inference'}
          </Button>
        </div>
      </div>

      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Detected Vehicles"
          value={detections.length}
          icon={<Car size={20} />}
          sub="Cars, buses, motorcycles & emergency"
        />
        <StatCard
          label="Traffic Density"
          value={`${densityScore}%`}
          icon={<Activity size={20} />}
          sub={density.label}
        />
        <StatCard
          label="Emergency Candidate"
          value={emergencyFound ? 'Detected' : 'None'}
          icon={<Truck size={20} />}
          sub={emergencyFound ? 'Ambulance spotted in approach' : 'No emergency vehicles in frame'}
        />
        <StatCard
          label="Inference FPS"
          value={`${fps} fps`}
          icon={<Cpu size={20} />}
          sub="FastAPI + OpenCV Pipeline"
        />
      </div>

      {/* Main Viewport & Analysis Split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Visual Detection Canvas */}
        <div className="lg:col-span-2 rounded-2xl border border-slate-700/60 bg-slate-900/80 p-5 shadow-xl flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Eye size={18} className="text-blue-400" />
              <h2 className="text-base font-semibold text-white">
                Intersection Feed — {selectedIntersection} (City Centre)
              </h2>
            </div>
            <select
              value={selectedIntersection}
              onChange={(e) => setSelectedIntersection(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-xs rounded-lg px-2.5 py-1.5 text-slate-200 outline-none focus:border-blue-500"
            >
              <option value="SIG-B2">SIG-B2 (City Centre)</option>
              <option value="SIG-A2">SIG-A2 (North-Central)</option>
              <option value="SIG-B1">SIG-B1 (West Junction)</option>
              <option value="SIG-C2">SIG-C2 (South-Central)</option>
            </select>
          </div>

          {/* Simulated Camera Feed Display with Bounding Boxes */}
          <div className="relative w-full aspect-video rounded-xl bg-slate-950 border border-slate-800 overflow-hidden flex items-center justify-center">
            {/* Background Simulated Road Grid */}
            <div
              className="absolute inset-0 opacity-20"
              style={{
                backgroundImage:
                  'radial-gradient(circle, #3b82f6 1px, transparent 1px), linear-gradient(to right, #1e293b 1px, transparent 1px)',
                backgroundSize: '24px 24px, 48px 48px',
              }}
            />

            {/* Video Feed Simulation Watermark */}
            <div className="absolute top-3 left-3 text-[11px] font-mono text-emerald-400 bg-slate-900/80 border border-emerald-500/30 px-2 py-1 rounded">
              REC ● 1080p | 30 FPS | CAM-{selectedIntersection}
            </div>

            {/* Render Bounding Boxes */}
            {detections.map((d, idx) => {
              const [x1, y1, x2, y2] = d.box;
              const isAmb = d.is_emergency_candidate;
              const color = isAmb ? '#ef4444' : '#3b82f6';

              return (
                <div
                  key={idx}
                  className="absolute transition-all duration-300"
                  style={{
                    left: `${x1}%`,
                    top: `${y1}%`,
                    width: `${x2 - x1}%`,
                    height: `${y2 - y1}%`,
                    border: `2px solid ${color}`,
                    backgroundColor: `${color}15`,
                    borderRadius: '4px',
                    boxShadow: isAmb ? '0 0 12px rgba(239, 68, 68, 0.6)' : 'none',
                  }}
                >
                  <span
                    className="absolute -top-5 left-0 text-[10px] font-bold px-1.5 py-0.5 rounded text-white whitespace-nowrap"
                    style={{ backgroundColor: color }}
                  >
                    {d.class_name} ({Math.round(d.confidence * 100)}%)
                  </span>
                </div>
              );
            })}

            {/* Center Crosshair Overlay */}
            <div className="w-12 h-12 border border-slate-700/50 rounded-full flex items-center justify-center pointer-events-none">
              <div className="w-1.5 h-1.5 bg-blue-500/50 rounded-full"></div>
            </div>

            {/* Simulated Banner */}
            <div className="absolute bottom-3 right-3 text-[10px] text-slate-500 bg-slate-900/90 px-2 py-0.5 rounded border border-slate-800">
              ⚠️ Simulated Vision Input Frame
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-400 mt-4 pt-3 border-t border-slate-800">
            <span>Model: {modelType}</span>
            <span className="flex items-center gap-1.5 text-emerald-400">
              <ShieldCheck size={14} /> Pipeline Healthy
            </span>
          </div>
        </div>

        {/* Detection Breakdown & Density Analytics */}
        <div className="space-y-6">
          {/* Traffic Density Card */}
          <div className="rounded-2xl border border-slate-700/60 bg-slate-900/80 p-5 shadow-xl space-y-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Activity size={16} className="text-amber-400" />
              Density Assessment
            </h3>

            <div className={`p-3 rounded-xl border ${density.color} text-center`}>
              <div className="text-xl font-bold tracking-wide">{density.label}</div>
              <div className="text-xs mt-1 opacity-90">
                Score: {densityScore} / 100 — Road capacity load estimated
              </div>
            </div>

            {/* Progress bar */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-slate-400">
                <span>Free Flow</span>
                <span>Congested</span>
              </div>
              <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${densityScore}%`,
                    backgroundColor:
                      densityScore > 75 ? '#ef4444' : densityScore > 50 ? '#f59e0b' : '#10b981',
                  }}
                />
              </div>
            </div>

            {emergencyFound && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-300 flex items-start gap-2.5">
                <AlertCircle size={16} className="text-red-400 shrink-0 mt-0.5" />
                <div>
                  <strong className="text-white block font-semibold mb-0.5">
                    Emergency Priority Alert
                  </strong>
                  Ambulance detected at intersection {selectedIntersection}. Green corridor
                  preemption candidate flagged for traffic operator.
                </div>
              </div>
            )}
          </div>

          {/* Detections List */}
          <div className="rounded-2xl border border-slate-700/60 bg-slate-900/80 p-5 shadow-xl">
            <h3 className="text-sm font-semibold text-white mb-3">
              Identified Objects ({detections.length})
            </h3>
            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {detections.map((det, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-2 rounded-lg bg-slate-800/40 border border-slate-700/40 text-xs"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        det.is_emergency_candidate ? 'bg-red-400' : 'bg-blue-400'
                      }`}
                    />
                    <span className="text-white font-medium">{det.class_name}</span>
                  </div>
                  <span className="font-mono text-slate-400">
                    {(det.confidence * 100).toFixed(0)}% conf
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

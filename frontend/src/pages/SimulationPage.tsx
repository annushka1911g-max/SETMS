// =============================================================================
// SETMS — Digital Twin Simulation Runner (Milestone 10)
// Interactive simulation of the fictional city of Navapur with multi-ambulance
// conflict scenarios, sequential signal preemption, and CSV telemetry export.
// =============================================================================
import { useState, useEffect } from 'react';
import {
  Gamepad2, Play, Pause, RotateCcw, FastForward,
  Download, AlertTriangle, ShieldCheck, Route,
} from 'lucide-react';
import { PageHeader } from '../components/ui';

interface SimSignal {
  id: string;
  name: string;
  gridRow: number;
  gridCol: number;
  phase: 'RED' | 'YELLOW' | 'GREEN';
  isLocked: boolean;
}

interface SimAmbulance {
  id: string;
  callSign: string;
  severity: 'CRITICAL' | 'HIGH' | 'NORMAL';
  x: number; // percentage on grid (0-100)
  y: number; // percentage on grid (0-100)
  currentIntersection: string;
  targetHospital: string;
  active: boolean;
}

export function SimulationPage() {
  const [scenario, setScenario] = useState<'single' | 'conflict' | 'multi'>('conflict');
  const [isRunning, setIsRunning] = useState(false);
  const [speed, setSpeed] = useState<number>(1);
  const [simStep, setSimStep] = useState(0);

  const [logs, setLogs] = useState<string[]>([
    'Simulation initialized for city of Navapur.',
    'Road graph loaded: 9 intersections, 12 road links.',
    'Select a scenario and click Play to begin simulation.',
  ]);

  // 3x3 Grid of traffic signals
  const [signals, setSignals] = useState<SimSignal[]>([
    { id: 'SIG-A1', name: 'A1-North-West', gridRow: 0, gridCol: 0, phase: 'RED', isLocked: false },
    { id: 'SIG-A2', name: 'A2-North-Central', gridRow: 0, gridCol: 1, phase: 'RED', isLocked: false },
    { id: 'SIG-A3', name: 'A3-North-East', gridRow: 0, gridCol: 2, phase: 'RED', isLocked: false },
    { id: 'SIG-B1', name: 'B1-West', gridRow: 1, gridCol: 0, phase: 'RED', isLocked: false },
    { id: 'SIG-B2', name: 'B2-City Centre', gridRow: 1, gridCol: 1, phase: 'RED', isLocked: false },
    { id: 'SIG-B3', name: 'B3-East', gridRow: 1, gridCol: 2, phase: 'RED', isLocked: false },
    { id: 'SIG-C1', name: 'C1-South-West', gridRow: 2, gridCol: 0, phase: 'RED', isLocked: false },
    { id: 'SIG-C2', name: 'C2-South-Central', gridRow: 2, gridCol: 1, phase: 'RED', isLocked: false },
    { id: 'SIG-C3', name: 'C3-South-East', gridRow: 2, gridCol: 2, phase: 'RED', isLocked: false },
  ]);

  const [ambulances, setAmbulances] = useState<SimAmbulance[]>([
    { id: 'amb-1', callSign: 'AMB-Alpha', severity: 'CRITICAL', x: 15, y: 50, currentIntersection: 'B1', targetHospital: 'Navapur City Hospital', active: true },
    { id: 'amb-2', callSign: 'AMB-Bravo', severity: 'HIGH', x: 50, y: 15, currentIntersection: 'A2', targetHospital: 'Trauma Care Institute', active: true },
  ]);

  const [timeSavedSec, setTimeSavedSec] = useState(0);

  // Simulation step loop
  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      setSimStep((prev) => {
        const next = prev + 1;

        // Animate ambulance positions & signals based on scenario
        if (scenario === 'conflict') {
          if (next === 1) {
            addLog('⚡ Scenario: Two ambulances approaching Central Intersection SIG-B2 concurrently.');
            addLog('⚖️ Priority Engine evaluating: AMB-Alpha [CRITICAL] vs AMB-Bravo [HIGH]...');
          } else if (next === 3) {
            addLog('🏆 Priority decision: AMB-Alpha granted green preemption (Score: 89.4 vs 67.2).');
            addLog('🔒 SIG-B2 preemption lock engaged for corridor path.');
            setSignals((sigs) =>
              sigs.map((s) => (s.id === 'SIG-B2' ? { ...s, phase: 'GREEN', isLocked: true } : s))
            );
          } else if (next === 6) {
            addLog('🚑 AMB-Alpha safely cleared SIG-B2. Releasing lock with all-red safety interval.');
            setSignals((sigs) =>
              sigs.map((s) => (s.id === 'SIG-B2' ? { ...s, phase: 'YELLOW', isLocked: false } : s))
            );
          } else if (next === 8) {
            addLog('🟢 Transitioning SIG-B2 to green for deferred queue: AMB-Bravo [HIGH].');
            setSignals((sigs) =>
              sigs.map((s) => (s.id === 'SIG-B2' ? { ...s, phase: 'GREEN', isLocked: true } : s))
            );
          } else if (next >= 12) {
            addLog('✅ All emergency vehicles arrived at destination hospitals. Simulation complete.');
            setIsRunning(false);
          }
        }

        // Increment time saved metric
        setTimeSavedSec((t) => t + 3 * speed);

        // Move ambulances along trajectory
        setAmbulances((ambs) =>
          ambs.map((amb) => {
            if (amb.id === 'amb-1') {
              return { ...amb, x: Math.min(85, amb.x + 4 * speed) };
            }
            if (amb.id === 'amb-2') {
              return { ...amb, y: Math.min(85, amb.y + 4 * speed) };
            }
            return amb;
          })
        );

        return next;
      });
    }, 1000 / speed);

    return () => clearInterval(interval);
  }, [isRunning, speed, scenario]);

  const addLog = (msg: string) => {
    setLogs((prev) => [`[T+${simStep}s] ${msg}`, ...prev.slice(0, 30)]);
  };

  const handleReset = () => {
    setIsRunning(false);
    setSimStep(0);
    setTimeSavedSec(0);
    setSignals((sigs) => sigs.map((s) => ({ ...s, phase: 'RED', isLocked: false })));
    setAmbulances([
      { id: 'amb-1', callSign: 'AMB-Alpha', severity: 'CRITICAL', x: 15, y: 50, currentIntersection: 'B1', targetHospital: 'Navapur City Hospital', active: true },
      { id: 'amb-2', callSign: 'AMB-Bravo', severity: 'HIGH', x: 50, y: 15, currentIntersection: 'A2', targetHospital: 'Trauma Care Institute', active: true },
    ]);
    setLogs(['Simulation reset to initial state.']);
  };

  const exportCsv = () => {
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      'Step,Ambulance,X,Y,SignalB2_Phase,TimeSavedSec\n' +
      ambulances
        .map(
          (a) =>
            `${simStep},${a.callSign},${a.x.toFixed(1)},${a.y.toFixed(1)},${
              signals.find((s) => s.id === 'SIG-B2')?.phase
            },${timeSavedSec}`
        )
        .join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `SETMS_sim_run_step_${simStep}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="p-6 space-y-6 animate-fade-in max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <PageHeader
            title="Navapur Digital Twin Simulation Runner"
            subtitle="Demonstrate multi-ambulance routing, sequential traffic light clearance, and priority conflict resolution."
          />
        </div>

        {/* Playback Controls */}
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-700/80 p-1.5 rounded-xl">
          <button
            onClick={() => setIsRunning(!isRunning)}
            className={`p-2 rounded-lg font-semibold flex items-center gap-1.5 text-xs transition-colors ${
              isRunning ? 'bg-amber-600 text-white' : 'bg-blue-600 hover:bg-blue-500 text-white'
            }`}
          >
            {isRunning ? <Pause size={14} /> : <Play size={14} />}
            {isRunning ? 'Pause' : 'Start Simulation'}
          </button>

          <button
            onClick={handleReset}
            className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 text-xs transition-colors"
            title="Reset"
          >
            <RotateCcw size={14} />
          </button>

          <div className="h-4 w-px bg-slate-700 mx-1" />

          <button
            onClick={() => setSpeed(speed === 1 ? 2 : speed === 2 ? 4 : 1)}
            className="px-2.5 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white text-xs font-mono flex items-center gap-1"
          >
            <FastForward size={13} />
            {speed}x
          </button>

          <button
            onClick={exportCsv}
            className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 text-xs transition-colors"
            title="Export Telemetry CSV"
          >
            <Download size={14} />
          </button>
        </div>
      </div>

      {/* Scenario Selector & Status */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div
          onClick={() => { setScenario('conflict'); handleReset(); }}
          className={`p-4 rounded-xl border cursor-pointer transition-all ${
            scenario === 'conflict'
              ? 'bg-blue-600/15 border-blue-500 text-white'
              : 'bg-slate-900/60 border-slate-800 hover:bg-slate-800/60 text-slate-400'
          }`}
        >
          <div className="font-bold text-sm text-white flex items-center gap-2">
            <AlertTriangle size={16} className="text-amber-400" />
            Scenario: Intersection Conflict
          </div>
          <p className="text-xs mt-1 text-slate-400">
            Two ambulances approach Central Intersection (SIG-B2). Resolves via priority score.
          </p>
        </div>

        <div
          onClick={() => { setScenario('single'); handleReset(); }}
          className={`p-4 rounded-xl border cursor-pointer transition-all ${
            scenario === 'single'
              ? 'bg-blue-600/15 border-blue-500 text-white'
              : 'bg-slate-900/60 border-slate-800 hover:bg-slate-800/60 text-slate-400'
          }`}
        >
          <div className="font-bold text-sm text-white flex items-center gap-2">
            <Route size={16} className="text-emerald-400" />
            Scenario: Single Green Corridor
          </div>
          <p className="text-xs mt-1 text-slate-400">
            AMB-Alpha travels along west-to-east corridor with sequential preemption.
          </p>
        </div>

        <div
          onClick={() => { setScenario('multi'); handleReset(); }}
          className={`p-4 rounded-xl border cursor-pointer transition-all ${
            scenario === 'multi'
              ? 'bg-blue-600/15 border-blue-500 text-white'
              : 'bg-slate-900/60 border-slate-800 hover:bg-slate-800/60 text-slate-400'
          }`}
        >
          <div className="font-bold text-sm text-white flex items-center gap-2">
            <Gamepad2 size={16} className="text-purple-400" />
            Scenario: City Rush Hour Drill
          </div>
          <p className="text-xs mt-1 text-slate-400">
            Heavy traffic grid test with multi-path corridor allocation across Navapur.
          </p>
        </div>
      </div>

      {/* Grid Canvas & Decision Log */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Visual 3x3 Simulation Grid */}
        <div className="lg:col-span-2 rounded-2xl border border-slate-700/60 bg-slate-950 p-6 shadow-xl relative min-h-[460px] flex flex-col justify-between overflow-hidden">
          {/* Header Bar inside simulation */}
          <div className="flex items-center justify-between text-xs text-slate-400 pb-4 border-b border-slate-800">
            <span className="font-mono text-emerald-400">T+{simStep}s | Navapur City Center Grid</span>
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Green Preemption
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span> Standard Red
              </span>
            </div>
          </div>

          {/* Road Grid Display */}
          <div className="grid grid-cols-3 gap-12 my-auto p-4 relative">
            {signals.map((sig) => {
              return (
                <div
                  key={sig.id}
                  className={`p-4 rounded-xl border flex flex-col items-center justify-center relative transition-all ${
                    sig.isLocked
                      ? 'bg-emerald-950/40 border-emerald-500/60 shadow-[0_0_20px_rgba(34,197,94,0.3)]'
                      : 'bg-slate-900/60 border-slate-800'
                  }`}
                >
                  <div className="text-[11px] font-mono text-slate-400 mb-2">{sig.id}</div>
                  {/* Traffic Light Visual */}
                  <div className="w-8 h-16 bg-slate-950 rounded-lg border border-slate-800 p-1 flex flex-col justify-between items-center shadow-inner">
                    <div
                      className={`w-3.5 h-3.5 rounded-full transition-all ${
                        sig.phase === 'RED' ? 'bg-red-500 shadow-[0_0_8px_#ef4444]' : 'bg-red-950'
                      }`}
                    />
                    <div
                      className={`w-3.5 h-3.5 rounded-full transition-all ${
                        sig.phase === 'YELLOW' ? 'bg-yellow-400 shadow-[0_0_8px_#eab308]' : 'bg-yellow-950'
                      }`}
                    />
                    <div
                      className={`w-3.5 h-3.5 rounded-full transition-all ${
                        sig.phase === 'GREEN' ? 'bg-emerald-400 shadow-[0_0_8px_#22c55e]' : 'bg-emerald-950'
                      }`}
                    />
                  </div>
                  <div className="text-[10px] text-slate-500 mt-2 truncate max-w-[90px]">{sig.name}</div>
                </div>
              );
            })}

            {/* Simulated Animated Ambulances */}
            {ambulances.map((amb) => (
              <div
                key={amb.id}
                className="absolute transition-all duration-700 ease-linear pointer-events-none z-10"
                style={{
                  left: `${amb.x}%`,
                  top: `${amb.y}%`,
                  transform: 'translate(-50%, -50%)',
                }}
              >
                <div className="flex flex-col items-center">
                  <div className="px-1.5 py-0.5 rounded text-[9px] font-bold text-white bg-blue-600 shadow-md whitespace-nowrap mb-1">
                    {amb.callSign} [{amb.severity}]
                  </div>
                  <div className="w-8 h-8 rounded-full bg-red-600 text-white flex items-center justify-center border-2 border-white shadow-[0_0_15px_rgba(239,68,68,0.8)] animate-bounce text-sm">
                    🚑
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="text-[11px] text-slate-500 text-center pt-2 border-t border-slate-800">
            ⚠️ Simulation environment: Models safety intervals and conflict preemption without public road connection.
          </div>
        </div>

        {/* Live Decision Audit Log */}
        <div className="rounded-2xl border border-slate-700/60 bg-slate-900/80 p-5 shadow-xl flex flex-col h-[460px]">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center justify-between">
            <span className="flex items-center gap-2">
              <ShieldCheck size={16} className="text-blue-400" />
              Decision Audit Log
            </span>
            <span className="text-xs font-mono text-emerald-400">
              Est. Saved: ~{timeSavedSec}s
            </span>
          </h3>

          <div className="flex-1 overflow-y-auto space-y-2 pr-1 font-mono text-xs">
            {logs.map((log, index) => (
              <div
                key={index}
                className={`p-2 rounded-lg border text-[11px] leading-relaxed ${
                  log.includes('Priority decision') || log.includes('Scenario:')
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                    : log.includes('green preemption') || log.includes('complete')
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : 'bg-slate-800/40 border-slate-800 text-slate-400'
                }`}
              >
                {log}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

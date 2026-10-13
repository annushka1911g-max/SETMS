// SETMS — Stub pages for Map, AI, Simulation, Users, Settings
import type React from 'react';
import { MapPin, Cpu, Gamepad2, Users, Settings } from 'lucide-react';

function StubPage({ title, subtitle, icon }: { title: string; subtitle: string; icon: React.ReactNode }) {
  return (
    <div className="p-6 animate-fade-in">
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
        <div className="w-20 h-20 rounded-2xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-5">
          {icon}
        </div>
        <h1 className="text-2xl font-bold text-white mb-2">{title}</h1>
        <p className="text-slate-400 text-sm max-w-md">{subtitle}</p>
        <div className="mt-4 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700 text-xs text-slate-500">
          🚧 Implemented in Milestones 5–10
        </div>
      </div>
    </div>
  );
}

export function MapPage() {
  return (
    <StubPage
      title="Live Emergency Map"
      subtitle="Leaflet + OpenStreetMap map with ambulance tracking, hospital markers, active corridor routes, and real-time GPS updates. Implemented in Milestone 5."
      icon={<MapPin size={36} />}
    />
  );
}

export function AIDetectionPage() {
  return (
    <StubPage
      title="AI Detection & Traffic Density"
      subtitle="YOLO-based vehicle detection, ambulance candidate classification, traffic density estimation, and annotated output frames. Implemented in Milestone 8."
      icon={<Cpu size={36} />}
    />
  );
}

export function SimulationPage() {
  return (
    <StubPage
      title="Digital Twin Simulation"
      subtitle="Visual simulation of the fictional city of Navapur with interactive controls, ambulance movement, signal state transitions, and multi-ambulance scenarios. Implemented in Milestone 10."
      icon={<Gamepad2 size={36} />}
    />
  );
}

export function UsersPage() {
  return (
    <StubPage
      title="User & Role Management"
      subtitle="Admin panel to manage user accounts, assign roles, activate/deactivate accounts, and view audit logs. Implemented in Milestone 2."
      icon={<Users size={36} />}
    />
  );
}

export function SettingsPage() {
  return (
    <StubPage
      title="System Settings"
      subtitle="Configure system parameters, routing provider, MQTT credentials, signal timing, and notification settings. Implemented in Milestone 12."
      icon={<Settings size={36} />}
    />
  );
}

// =============================================================================
// SETMS — Live Emergency Map Page (Milestone 5)
// OpenStreetMap + Leaflet integration with real-time ambulance tracking,
// hospital availability badges, traffic signal phase indicators, and corridors.
// =============================================================================
import { useEffect, useRef, useState, useCallback } from 'react';
import L from 'leaflet';
import {
  Navigation, Hospital as HospitalIcon,
  RefreshCw, Layers, ShieldAlert,
} from 'lucide-react';
import {
  ambulanceApi, hospitalApi, signalApi, corridorApi, getErrorMessage,
} from '../api/client';
import { PageHeader, LoadingSpinner, ErrorAlert, Badge } from '../components/ui';
import type { Ambulance, Hospital, TrafficSignal, Corridor } from '../types';

const NAVAPUR_CENTER: [number, number] = [18.5204, 73.8567];

export function MapPage() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layersRef = useRef<{
    ambulances: L.LayerGroup;
    hospitals: L.LayerGroup;
    signals: L.LayerGroup;
    corridors: L.LayerGroup;
  }>({
    ambulances: L.layerGroup(),
    hospitals: L.layerGroup(),
    signals: L.layerGroup(),
    corridors: L.layerGroup(),
  });

  const [ambulances, setAmbulances] = useState<Ambulance[]>([]);
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [signals, setSignals] = useState<TrafficSignal[]>([]);
  const [corridors, setCorridors] = useState<Corridor[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAmbulance, setSelectedAmbulance] = useState<string | null>(null);

  // Layer visibility toggles
  const [showAmbulances, setShowAmbulances] = useState(true);
  const [showHospitals, setShowHospitals] = useState(true);
  const [showSignals, setShowSignals] = useState(true);
  const [showCorridors, setShowCorridors] = useState(true);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: NAVAPUR_CENTER,
      zoom: 14,
      zoomControl: true,
    });

    // OpenStreetMap free tile layer (no API key required)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);

    // Add layer groups to map
    layersRef.current.ambulances.addTo(map);
    layersRef.current.hospitals.addTo(map);
    layersRef.current.signals.addTo(map);
    layersRef.current.corridors.addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Fetch telemetry & entity data
  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const [ambRes, hospRes, sigRes, corrRes] = await Promise.all([
        ambulanceApi.list({ limit: 50 }),
        hospitalApi.list(),
        signalApi.list(),
        corridorApi.list(),
      ]);

      setAmbulances(ambRes.items);
      setHospitals(hospRes.items);
      setSignals(sigRes.items);
      setCorridors(corrRes.items);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 6000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Update map markers when entities change
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // 1. Ambulances
    layersRef.current.ambulances.clearLayers();
    if (showAmbulances) {
      ambulances.forEach((amb) => {
        const lat = amb.current_lat ?? NAVAPUR_CENTER[0];
        const lng = amb.current_lng ?? NAVAPUR_CENTER[1];

        const isEmergency = amb.status === 'EN_ROUTE' || amb.status === 'TRANSPORTING';
        const color = isEmergency ? '#ef4444' : '#3b82f6';

        const icon = L.divIcon({
          className: 'custom-amb-marker',
          html: `
            <div style="
              background: ${color};
              color: white;
              border-radius: 9999px;
              width: 32px;
              height: 32px;
              display: flex;
              align-items: center;
              justify-content: center;
              box-shadow: 0 0 15px ${color}88;
              border: 2px solid white;
              font-weight: bold;
              font-size: 13px;
            ">
              🚑
            </div>
          `,
          iconSize: [32, 32],
          iconAnchor: [16, 16],
        });

        const marker = L.marker([lat, lng], { icon });
        marker.bindPopup(`
          <div style="font-family: sans-serif; font-size: 13px; color: #0f172a; line-height: 1.4;">
            <strong style="font-size: 14px;">${amb.call_sign}</strong> (${amb.registration_number})<br/>
            <strong>Status:</strong> ${amb.status}<br/>
            <strong>Type:</strong> ${amb.vehicle_type}<br/>
            <strong>Speed:</strong> ${amb.current_speed_kmh?.toFixed(1) ?? 0} km/h<br/>
            <small style="color: #64748b;">Simulated telemetry active</small>
          </div>
        `);
        layersRef.current.ambulances.addLayer(marker);
      });
    }

    // 2. Hospitals
    layersRef.current.hospitals.clearLayers();
    if (showHospitals) {
      hospitals.forEach((hosp) => {
        const icon = L.divIcon({
          className: 'custom-hosp-marker',
          html: `
            <div style="
              background: #059669;
              color: white;
              border-radius: 8px;
              width: 28px;
              height: 28px;
              display: flex;
              align-items: center;
              justify-content: center;
              box-shadow: 0 4px 10px rgba(5, 150, 105, 0.4);
              border: 2px solid white;
              font-weight: 800;
              font-size: 14px;
            ">
              H
            </div>
          `,
          iconSize: [28, 28],
          iconAnchor: [14, 14],
        });

        const marker = L.marker([hosp.latitude, hosp.longitude], { icon });
        marker.bindPopup(`
          <div style="font-family: sans-serif; font-size: 13px; color: #0f172a; line-height: 1.4;">
            <strong style="font-size: 14px;">${hosp.name}</strong><br/>
            <strong>Address:</strong> ${hosp.address}<br/>
            <strong>Available ER Bays:</strong> ${hosp.emergency_bays_available} / ${hosp.emergency_bays_total}<br/>
            <strong>Status:</strong> ${hosp.is_ready ? '🟢 Accepting' : '🔴 Diverting'}
          </div>
        `);
        layersRef.current.hospitals.addLayer(marker);
      });
    }

    // 3. Traffic Signals
    layersRef.current.signals.clearLayers();
    if (showSignals) {
      signals.forEach((sig) => {
        const phaseColor =
          sig.current_phase === 'GREEN'
            ? '#22c55e'
            : sig.current_phase === 'YELLOW'
            ? '#eab308'
            : '#ef4444';

        const icon = L.divIcon({
          className: 'custom-sig-marker',
          html: `
            <div style="
              background: #1e293b;
              border-radius: 9999px;
              width: 20px;
              height: 20px;
              display: flex;
              align-items: center;
              justify-content: center;
              border: 2px solid ${phaseColor};
              box-shadow: 0 0 10px ${phaseColor};
            ">
              <div style="width: 8px; height: 8px; border-radius: 9999px; background: ${phaseColor};"></div>
            </div>
          `,
          iconSize: [20, 20],
          iconAnchor: [10, 10],
        });

        const marker = L.marker([sig.latitude, sig.longitude], { icon });
        marker.bindPopup(`
          <div style="font-family: sans-serif; font-size: 13px; color: #0f172a; line-height: 1.4;">
            <strong style="font-size: 14px;">${sig.name}</strong><br/>
            <strong>Intersection:</strong> ${sig.intersection_name}<br/>
            <strong>Phase:</strong> <span style="font-weight: bold; color: ${phaseColor};">${sig.current_phase}</span><br/>
            <strong>Mode:</strong> ${sig.current_mode}<br/>
            <small style="color: #64748b;">⚠️ Simulated signal node</small>
          </div>
        `);
        layersRef.current.signals.addLayer(marker);
      });
    }

    // 4. Corridors (Draw polyline through signals)
    layersRef.current.corridors.clearLayers();
    if (showCorridors) {
      corridors
        .filter((c) => c.status === 'ACTIVE' || c.status === 'APPROVED')
        .forEach((corr) => {
          // Connect active corridor points if available
          const points: [number, number][] = [];
          if (corr.route_json) {
            try {
              const parsed = JSON.parse(corr.route_json);
              if (parsed.signal_ids && Array.isArray(parsed.signal_ids)) {
                parsed.signal_ids.forEach((sid: string) => {
                  const matched = signals.find((s) => s.id === sid);
                  if (matched) points.push([matched.latitude, matched.longitude]);
                });
              }
            } catch {
              // fallback
            }
          }

          if (points.length >= 2) {
            const polyline = L.polyline(points, {
              color: '#10b981',
              weight: 6,
              opacity: 0.85,
              dashArray: '8, 8',
            });
            polyline.bindPopup(`<strong>Active Green Corridor</strong><br/>Emergency ID: ${corr.emergency_id}`);
            layersRef.current.corridors.addLayer(polyline);
          }
        });
    }
  }, [ambulances, hospitals, signals, corridors, showAmbulances, showHospitals, showSignals, showCorridors]);

  // Track ambulance button handler
  const handleTrackAmbulance = (amb: Ambulance) => {
    setSelectedAmbulance(amb.id);
    if (mapInstanceRef.current && amb.current_lat && amb.current_lng) {
      mapInstanceRef.current.flyTo([amb.current_lat, amb.current_lng], 16, {
        duration: 1.2,
      });
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] p-6 gap-4 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <PageHeader
            title="Navapur Live Emergency Map"
            subtitle="Real-time GPS telemetry, hospital bay availability, and simulated traffic signal coordination."
          />
        </div>

        <div className="flex items-center gap-2">
          <div className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Simulated City: Navapur
          </div>
          <button
            onClick={fetchData}
            className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
            title="Refresh Map Data"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} onRetry={fetchData} />}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 flex-1 min-h-0">
        {/* Map View */}
        <div className="lg:col-span-3 rounded-2xl overflow-hidden border border-slate-700/60 shadow-xl relative bg-slate-900">
          {loading && (
            <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm z-10 flex items-center justify-center">
              <LoadingSpinner label="Loading telemetry..." />
            </div>
          )}
          <div ref={mapContainerRef} className="w-full h-full min-h-[500px] dark-map" />

          {/* Map Layer Controls Floating Overlay */}
          <div className="absolute top-4 right-4 z-[1000] bg-slate-900/90 backdrop-blur-md border border-slate-700/80 rounded-xl p-3 shadow-2xl text-xs space-y-2">
            <div className="font-semibold text-slate-300 flex items-center gap-1.5 mb-2 pb-1 border-b border-slate-800">
              <Layers size={14} className="text-blue-400" />
              Layer Visibility
            </div>
            <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={showAmbulances}
                onChange={(e) => setShowAmbulances(e.target.checked)}
                className="rounded accent-blue-500"
              />
              🚑 Ambulances ({ambulances.length})
            </label>
            <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={showHospitals}
                onChange={(e) => setShowHospitals(e.target.checked)}
                className="rounded accent-emerald-500"
              />
              🏥 Hospitals ({hospitals.length})
            </label>
            <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={showSignals}
                onChange={(e) => setShowSignals(e.target.checked)}
                className="rounded accent-yellow-500"
              />
              🚦 Signals ({signals.length})
            </label>
            <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={showCorridors}
                onChange={(e) => setShowCorridors(e.target.checked)}
                className="rounded accent-emerald-400"
              />
              🟩 Active Corridors
            </label>
          </div>

          {/* Failsafe Notice */}
          <div className="absolute bottom-4 left-4 z-[1000] bg-amber-500/10 backdrop-blur-md border border-amber-500/30 rounded-lg px-3 py-1.5 text-[11px] text-amber-300 flex items-center gap-2">
            <ShieldAlert size={14} />
            <span>Failsafe notice: Telemetry & signal changes operate in software simulation mode.</span>
          </div>
        </div>

        {/* Sidebar: Active Ambulances List */}
        <div className="rounded-2xl border border-slate-700/60 bg-slate-900/60 backdrop-blur-sm p-4 flex flex-col min-h-0 overflow-hidden shadow-xl">
          <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Navigation size={16} className="text-blue-400" />
            Ambulance Fleet ({ambulances.length})
          </h2>

          <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
            {ambulances.map((amb) => {
              const isSelected = selectedAmbulance === amb.id;
              const isEmergency = amb.status === 'EN_ROUTE' || amb.status === 'TRANSPORTING';

              return (
                <div
                  key={amb.id}
                  onClick={() => handleTrackAmbulance(amb)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-blue-600/15 border-blue-500 text-white'
                      : 'bg-slate-800/40 border-slate-700/50 hover:bg-slate-800 text-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-sm text-white flex items-center gap-1.5">
                      {amb.call_sign}
                    </span>
                    <Badge label={amb.status} variant={isEmergency ? 'high' : 'active'} />
                  </div>

                  <div className="text-xs text-slate-400 flex items-center justify-between mt-2">
                    <span>{amb.vehicle_type}</span>
                    <span className="font-mono text-blue-400">
                      {amb.current_speed_kmh?.toFixed(0) ?? 0} km/h
                    </span>
                  </div>

                  <div className="text-[11px] text-slate-500 mt-1 truncate">
                    📍 {amb.current_lat?.toFixed(4)}, {amb.current_lng?.toFixed(4)}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Quick Hospital Status summary */}
          <div className="mt-4 pt-3 border-t border-slate-800">
            <div className="text-xs font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
              <HospitalIcon size={14} className="text-emerald-400" />
              Emergency Bay Readiness
            </div>
            <div className="space-y-1.5 text-xs text-slate-400">
              {hospitals.map((h) => (
                <div key={h.id} className="flex items-center justify-between">
                  <span className="truncate max-w-[130px]">{h.name}</span>
                  <span className="font-semibold text-emerald-400">
                    {h.emergency_bays_available}/{h.emergency_bays_total} bays
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

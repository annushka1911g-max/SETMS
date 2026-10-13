// =============================================================================
// SETMS — Shared TypeScript Types
// Mirrors the backend Pydantic schemas.
// =============================================================================

// ---- Enums ----
export type UserRole =
  | 'ADMIN'
  | 'TRAFFIC_OPERATOR'
  | 'AMBULANCE_DRIVER'
  | 'HOSPITAL_OPERATOR'
  | 'VIEWER';

export type EmergencySeverity = 'CRITICAL' | 'HIGH' | 'NORMAL';
export type EmergencyStatus = 'PENDING' | 'ACTIVE' | 'COMPLETED' | 'CANCELLED';

export type AmbulanceStatus =
  | 'AVAILABLE'
  | 'EN_ROUTE'
  | 'AT_SCENE'
  | 'TRANSPORTING'
  | 'OUT_OF_SERVICE';

export type SignalPhase = 'RED' | 'YELLOW' | 'GREEN' | 'FLASHING_RED';
export type SignalMode = 'NORMAL' | 'EMERGENCY' | 'MANUAL' | 'FLASHING' | 'OFF';
export type SignalStatus =
  | 'OPERATIONAL'
  | 'EMERGENCY_OVERRIDE'
  | 'FAULT'
  | 'OFFLINE'
  | 'MAINTENANCE';

export type CorridorStatus =
  | 'PROPOSED'
  | 'APPROVED'
  | 'ACTIVE'
  | 'SUSPENDED'
  | 'COMPLETED'
  | 'CANCELLED'
  | 'EXPIRED';

export type DeviceConnectivity = 'ONLINE' | 'OFFLINE' | 'DEGRADED' | 'UNKNOWN';
export type DensityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'GRIDLOCK';

// ---- Auth ----
export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  role: UserRole;
  full_name: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

// ---- Ambulance ----
export interface Ambulance {
  id: string;
  registration_number: string;
  call_sign: string;
  vehicle_type: string;
  status: AmbulanceStatus;
  current_lat: number | null;
  current_lng: number | null;
  current_speed_kmh: number | null;
  location_updated_at: string | null;
  driver_user_id: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ---- Emergency ----
export interface Emergency {
  id: string;
  reference_code: string;
  ambulance_id: string;
  destination_hospital_id: string | null;
  severity: EmergencySeverity;
  status: EmergencyStatus;
  description: string | null;
  origin_lat: number | null;
  origin_lng: number | null;
  origin_address: string | null;
  dest_lat: number | null;
  dest_lng: number | null;
  activated_at: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  initial_eta_minutes: number | null;
  final_duration_minutes: number | null;
  baseline_eta_minutes: number | null;
  priority_score: number | null;
  created_at: string;
  updated_at: string;
}

// ---- Traffic Signal ----
export interface TrafficSignal {
  id: string;
  name: string;
  intersection_name: string;
  latitude: number;
  longitude: number;
  status: SignalStatus;
  current_phase: SignalPhase;
  current_mode: SignalMode;
  approach_directions: string;
  green_duration_sec: number;
  yellow_duration_sec: number;
  red_duration_sec: number;
  road_node_id: string | null;
  device_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ---- Corridor ----
export interface Corridor {
  id: string;
  emergency_id: string;
  status: CorridorStatus;
  route_json: string | null;
  total_distance_meters: number | null;
  estimated_duration_seconds: number | null;
  proposed_by_user_id: string | null;
  approved_by_user_id: string | null;
  approved_at: string | null;
  activated_at: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  expires_at: string | null;
  conflict_notes: string | null;
  cancel_reason: string | null;
  created_at: string;
  updated_at: string;
}

// ---- Hospital ----
export interface Hospital {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  contact_phone: string | null;
  contact_email: string | null;
  emergency_bays_total: number;
  emergency_bays_available: number;
  is_ready: boolean;
  readiness_note: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ---- Dashboard ----
export interface DashboardSummary {
  ambulances: { total: number; active: number; available: number };
  emergencies: { active: number; today: number };
  corridors: { active: number };
  signals: { total: number; in_emergency_override: number };
  hospitals: { total: number; ready: number };
  analytics: {
    avg_journey_duration_minutes_7d: number | null;
    estimated_time_saved_minutes_label: string;
    estimated_time_saved_minutes_total: number;
  };
  generated_at: string;
}

// ---- Pagination ----
export interface Paginated<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// ---- API Error ----
export interface ApiError {
  detail: string;
}

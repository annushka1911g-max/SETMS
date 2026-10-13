// SETMS — Application Router
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './store/AuthContext';
import { ToastProvider } from './store/ToastContext';
import { RequireAuth } from './components/ui/RequireAuth';
import { AppLayout } from './components/layout/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { AmbulancesPage } from './pages/AmbulancesPage';
import { EmergenciesPage } from './pages/EmergenciesPage';
import { SignalsPage } from './pages/SignalsPage';
import { CorridorsPage } from './pages/CorridorsPage';
import { HospitalsPage } from './pages/HospitalsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { MapPage } from './pages/MapPage';
import { AIDetectionPage } from './pages/AIDetectionPage';
import { SimulationPage } from './pages/SimulationPage';
import { UsersPage, SettingsPage } from './pages/StubPages';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            {/* Public */}
            <Route path="/login" element={<LoginPage />} />

            {/* Protected — requires authentication */}
            <Route
              path="/"
              element={
                <RequireAuth>
                  <AppLayout />
                </RequireAuth>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="map" element={<MapPage />} />
              <Route path="ambulances" element={<AmbulancesPage />} />
              <Route path="emergencies" element={<EmergenciesPage />} />
              <Route path="signals" element={<SignalsPage />} />
              <Route path="corridors" element={<CorridorsPage />} />
              <Route path="ai" element={<AIDetectionPage />} />
              <Route path="hospitals" element={<HospitalsPage />} />
              <Route path="analytics" element={<AnalyticsPage />} />
              <Route path="simulation" element={<SimulationPage />} />
              <Route path="users" element={<UsersPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

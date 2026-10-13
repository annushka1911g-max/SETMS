// SETMS — AppLayout: Sidebar + content area
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export function AppLayout() {
  return (
    <div className="flex h-screen overflow-hidden" style={{ background: '#0f172a' }}>
      <Sidebar />
      <main className="flex-1 overflow-y-auto" id="main-content">
        <Outlet />
      </main>
    </div>
  );
}

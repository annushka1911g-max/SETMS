// SETMS — Sidebar Navigation
import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, MapPin, Truck, AlertTriangle, TrafficCone,
  Route, Cpu, Hospital, BarChart3, Users, Settings,
  Gamepad2, LogOut, ChevronLeft, ChevronRight, Shield,
} from 'lucide-react';
import { useAuth } from '../../store/AuthContext';
import type { UserRole } from '../../types';

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
  roles?: UserRole[];
}

const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', label: 'Overview', icon: <LayoutDashboard size={18} /> },
  { to: '/map', label: 'Live Map', icon: <MapPin size={18} /> },
  { to: '/ambulances', label: 'Ambulances', icon: <Truck size={18} /> },
  { to: '/emergencies', label: 'Emergencies', icon: <AlertTriangle size={18} /> },
  { to: '/signals', label: 'Signal Control', icon: <TrafficCone size={18} /> },
  { to: '/corridors', label: 'Green Corridors', icon: <Route size={18} /> },
  { to: '/ai', label: 'AI Detection', icon: <Cpu size={18} /> },
  { to: '/hospitals', label: 'Hospitals', icon: <Hospital size={18} /> },
  { to: '/analytics', label: 'Analytics', icon: <BarChart3 size={18} /> },
  { to: '/simulation', label: 'Simulation', icon: <Gamepad2 size={18} /> },
  {
    to: '/users', label: 'User Mgmt', icon: <Users size={18} />,
    roles: ['ADMIN'],
  },
  {
    to: '/settings', label: 'Settings', icon: <Settings size={18} />,
    roles: ['ADMIN'],
  },
];

export function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  const visibleItems = NAV_ITEMS.filter(item =>
    !item.roles || (user && item.roles.includes(user.role as UserRole))
  );

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside
      className={`flex flex-col h-screen sticky top-0 transition-all duration-300 ${
        collapsed ? 'w-16' : 'w-60'
      }`}
      style={{ background: '#0a1628', borderRight: '1px solid #1e293b' }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-4 border-b border-slate-800">
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
          <Shield size={16} className="text-white" />
        </div>
        {!collapsed && (
          <div>
            <div className="text-sm font-bold text-white tracking-tight">SETMS</div>
            <div className="text-xs text-slate-500 truncate">Emergency Traffic Mgmt</div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-3 px-2" aria-label="Main navigation">
        {visibleItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            title={collapsed ? item.label : undefined}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg mb-0.5 text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              } ${collapsed ? 'justify-center' : ''}`
            }
          >
            <span className="shrink-0">{item.icon}</span>
            {!collapsed && <span className="truncate">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* User info + Collapse toggle */}
      <div className="border-t border-slate-800 p-2">
        {!collapsed && user && (
          <div className="px-2 py-2 mb-1">
            <div className="text-xs font-semibold text-slate-300 truncate">{user.full_name}</div>
            <div className="text-xs text-slate-500 truncate">{user.role.replace('_', ' ')}</div>
          </div>
        )}
        <button
          onClick={handleLogout}
          title="Log out"
          className={`flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-red-400 hover:bg-red-950/30 transition-all ${
            collapsed ? 'justify-center' : ''
          }`}
        >
          <LogOut size={16} />
          {!collapsed && <span>Log Out</span>}
        </button>
        <button
          onClick={() => setCollapsed(c => !c)}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-xs text-slate-600 hover:text-slate-400 transition-all mt-1 justify-center"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
          {!collapsed && <span>Collapse</span>}
        </button>
      </div>
    </aside>
  );
}

// src/components/AppShell.jsx
import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useUI } from '../state/store';
import {
  LiveIcon,
  DashboardIcon,
  AnalyticsIcon,
  ReportsIcon,
  SettingsIcon,
  MenuIcon,
  CloseIcon,
  ShieldIcon,
  UserIcon,
} from './Icons';

import { useAuth } from '../state/AuthContext';

export default function AppShell({ children, wsStatus }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const { wsStatus: contextWsStatus } = useUI();
  const { user, logout } = useAuth();

  const activeWsStatus = wsStatus || contextWsStatus || 'DISCONNECTED';

  const navItems = [
    { label: 'Live Monitor', path: '/live', icon: LiveIcon },
    { label: 'Dashboard', path: '/dashboard', icon: DashboardIcon },
    { label: 'Reports', path: '/reports', icon: ReportsIcon },
    { label: 'Settings', path: '/settings', icon: SettingsIcon },
  ];

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/live':
        return 'Live Monitor';
      case '/dashboard':
        return 'Executive Dashboard';
      case '/reports':
        return 'Session Inspection Reports';
      case '/settings':
        return 'System Settings';
      case '/login':
        return 'Sign In';
      case '/register':
        return 'Register';
      default:
        return 'PostureAI';
    }
  };

  const isConnected = activeWsStatus === 'CONNECTED';

  return (
    <div className="min-h-screen bg-[#0b0f17] text-slate-100 flex flex-col md:flex-row">
      {/* Mobile Top Header */}
      <header className="md:hidden bg-[#111827] border-b border-slate-800 px-4 py-3 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-cyan-500/20">
            <ShieldIcon className="w-5 h-5" />
          </div>
          <span className="font-bold text-lg text-white tracking-wide">Posture<span className="text-cyan-400">AI</span></span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 focus:outline-none"
          aria-label="Toggle Navigation Menu"
        >
          {mobileMenuOpen ? <CloseIcon className="w-6 h-6" /> : <MenuIcon className="w-6 h-6" />}
        </button>
      </header>

      {/* Desktop Persistent Sidebar & Mobile Navigation Drawer */}
      <aside
        className={`${
          mobileMenuOpen ? 'block' : 'hidden'
        } md:block w-full md:w-64 bg-[#0f172a] border-r border-slate-800/80 flex-shrink-0 flex flex-col justify-between sticky top-0 h-auto md:h-screen z-30 transition-all`}
      >
        <div className="p-4 space-y-6">
          {/* Logo Brand */}
          <div className="hidden md:flex items-center space-x-3 px-2 py-2">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-cyan-500/20">
              <ShieldIcon className="w-6 h-6" />
            </div>
            <div>
              <h1 className="font-extrabold text-xl text-white tracking-tight leading-none">
                Posture<span className="text-cyan-400">AI</span>
              </h1>
              <span className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase">Real-Time Posture Analytics</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center space-x-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all ${
                      isActive
                        ? 'bg-gradient-to-r from-cyan-500/15 to-indigo-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                    }`
                  }
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer: System Status */}
        <div className="p-4 border-t border-slate-800/80 space-y-3 bg-slate-900/40">
          <div className="flex items-center justify-between px-2 py-1.5 rounded-lg bg-slate-950/60 border border-slate-800/60 text-xs">
            <span className="text-slate-400 font-medium">Live Stream</span>
            <div className="flex items-center space-x-1.5 font-semibold">
              <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
              <span className={isConnected ? 'text-emerald-400' : 'text-amber-400'}>
                {isConnected ? 'Connected' : 'Standby'}
              </span>
            </div>
          </div>
          <div className="flex items-center justify-between px-2 pt-1 text-[11px] text-slate-500">
            <span>PostureAI v1.0.0</span>
            <span>CV Inference Engine</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        {/* Desktop Top Header Bar */}
        <header className="hidden md:flex items-center justify-between px-8 py-4 border-b border-slate-800/80 bg-[#0f172a]/60 backdrop-blur-md sticky top-0 z-20">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">{getPageTitle()}</h2>
            <p className="text-xs text-slate-400">Computer Vision Posture Analysis & Temporal Risk System</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-800/60 border border-slate-700/50 text-xs text-slate-300">
              <span className="w-2 h-2 rounded-full bg-cyan-400" />
              <span>Real-Time CV Engine</span>
            </div>
            {user ? (
              <div className="flex items-center space-x-3">
                <div className="text-right">
                  <div className="text-xs font-bold text-white">{user.name}</div>
                  <div className="text-[10px] text-slate-400">{user.email}</div>
                </div>
                <button
                  onClick={logout}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg text-xs font-semibold transition border border-slate-700/60"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <NavLink
                to="/login"
                className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-bold transition shadow-sm"
              >
                Sign In
              </NavLink>
            )}
          </div>
        </header>

        {/* Page Content Container */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto space-y-6">
          {children}
        </main>
      </div>
    </div>
  );
}

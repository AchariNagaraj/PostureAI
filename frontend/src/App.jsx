// src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LiveMonitor from './pages/LiveMonitor.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import Reports from './pages/Reports.jsx';
import Analytics from './pages/Analytics.jsx';
import Settings from './pages/Settings.jsx';
import { UIProvider } from './state/store.js';
import { AuthProvider, useAuth } from './state/AuthContext.jsx';
import AppShell from './components/AppShell.jsx';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen bg-[#0b0f17] flex items-center justify-center text-slate-400 text-sm font-medium">
        Loading PostureAI authentication...
      </div>
    );
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function App() {
  return (
    <AuthProvider>
      <UIProvider>
        <Router>
          <AppShell>
            <Routes>
              <Route path="/" element={<Navigate to="/live" replace />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/live" element={<ProtectedRoute><LiveMonitor /></ProtectedRoute>} />
              <Route path="/reports" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
              <Route path="/analytics" element={<Navigate to="/dashboard" replace />} />
              <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
              <Route
                path="*"
                element={
                  <div className="p-12 text-center space-y-4">
                    <h1 className="text-4xl font-extrabold text-white">404</h1>
                    <p className="text-slate-400">Page not found</p>
                  </div>
                }
              />
            </Routes>
          </AppShell>
        </Router>
      </UIProvider>
    </AuthProvider>
  );
}

export default App;


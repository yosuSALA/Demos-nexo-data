import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import NuevoEnvio from './pages/NuevoEnvio'
import Login from './pages/Login'
import Register from './pages/Register'
import AdminDashboard from './pages/AdminDashboard'
import Navbar from './components/Navbar'

// Layout con Navbar para rutas protegidas
const AppLayout = ({ children }) => (
  <div className="min-h-screen bg-gray-50 flex flex-col items-center py-8 px-4">
    <div className="w-full max-w-5xl">
      <Navbar />
      {children}
    </div>
  </div>
);

// Guardián para proteger Vistas Reales
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div>Cargando...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <AppLayout>{children}</AppLayout>;
};

// Guardián para Admin y Supervisor
const AdminRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div>Cargando...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (!['admin', 'supervisor'].includes(user.rol)) return <Navigate to="/nuevo-envio" replace />;
  return <AppLayout>{children}</AppLayout>;
};

function AppConfig() {
  return (
    <Routes>
      {/* Si entras a la raiz, vas a login directo */}
      <Route path="/" element={<Navigate to="/login" replace />} />

      {/* Rutas Publicas (Auth) */}
      <Route path="/login" element={
        <div className="min-h-screen bg-gray-50 flex justify-center py-10 px-4">
          <Login />
        </div>
      } />
      <Route path="/register" element={
        <div className="min-h-screen bg-gray-50 flex justify-center py-10 px-4">
          <Register />
        </div>
      } />

      {/* Rutas Protegidas (Requieren Token) */}
      <Route path="/nuevo-envio" element={
        <ProtectedRoute><NuevoEnvio /></ProtectedRoute>
      } />

      {/* Rutas Protegidas para Admin y Supervisor */}
      <Route path="/admin" element={
        <AdminRoute><AdminDashboard /></AdminRoute>
      } />
    </Routes>
  )
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppConfig />
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App


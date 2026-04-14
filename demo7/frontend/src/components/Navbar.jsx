import React, { useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, Send, LogOut, Shield, User, ChevronRight } from 'lucide-react';

const ROL_LABELS = {
  admin: { label: 'Administrador', color: 'bg-purple-100 text-purple-700 border-purple-200' },
  supervisor: { label: 'Supervisor', color: 'bg-blue-100 text-blue-700 border-blue-200' },
  operador: { label: 'Operador', color: 'bg-green-100 text-green-700 border-green-200' },
};

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!user) return null;

  const rolInfo = ROL_LABELS[user.rol] || { label: user.rol, color: 'bg-gray-100 text-gray-700' };
  const isAdmin = location.pathname === '/admin';
  const isWizard = location.pathname === '/nuevo-envio';

  return (
    <div className="w-full max-w-5xl mx-auto mb-4">
      <div className="bg-white border border-gray-100 rounded-2xl shadow-sm px-5 py-3 flex items-center justify-between">
        {/* Logo + nombre */}
        <div className="flex items-center gap-3">
          <div className="bg-primary w-8 h-8 rounded-lg flex items-center justify-center shadow-sm">
            <Send className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-sm font-bold text-primary leading-tight">Nexo Data RRHH</p>
            <p className="text-xs text-gray-400 leading-tight">{user.nombre}</p>
          </div>
        </div>

        {/* Centro: navegación */}
        <div className="hidden sm:flex items-center gap-2">
          {['admin', 'supervisor'].includes(user.rol) && (
            <button
              onClick={() => navigate('/admin')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                isAdmin
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-gray-500 hover:bg-gray-100 hover:text-primary'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" />
              Admin Panel
            </button>
          )}
          <button
            onClick={() => navigate('/nuevo-envio')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              isWizard
                ? 'bg-secondary text-white shadow-sm'
                : 'text-gray-500 hover:bg-gray-100 hover:text-secondary'
            }`}
          >
            <Send className="w-4 h-4" />
            Nuevo Envío
          </button>
        </div>

        {/* Derecha: rol + salir */}
        <div className="flex items-center gap-3">
          <span className={`hidden sm:inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full border ${rolInfo.color}`}>
            <Shield className="w-3 h-3" />
            {rolInfo.label}
          </span>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-sm text-red-500 hover:bg-red-50 px-3 py-1.5 rounded-lg transition-all font-medium"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden sm:inline">Salir</span>
          </button>
        </div>
      </div>
    </div>
  );
}

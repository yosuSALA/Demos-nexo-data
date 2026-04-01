import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { UserPlus, User, Mail, Lock, Shield } from 'lucide-react';
import axios from 'axios';

const api = axios.create({ baseURL: 'http://localhost:8000/api' });

export default function Register() {
  const [formData, setFormData] = useState({nombre: '', email: '', password: '', rol: 'operador'});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      await api.post('/auth/register', formData);
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al completar el registro.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100 mx-auto mt-16">
      <div className="bg-primary p-6 text-white text-center">
        <h2 className="text-2xl font-bold">Unirse a RRHH</h2>
        <p className="text-sm opacity-80 mt-1">Crea tu cuenta de Empleado</p>
      </div>
      <div className="p-8">
        {error && <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded-lg">{error}</div>}
        
        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nombre Completo</label>
            <div className="relative">
              <User className="w-5 h-5 absolute left-3 top-2.5 text-gray-400" />
              <input type="text" value={formData.nombre} onChange={e=>setFormData({...formData, nombre: e.target.value})} required
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary focus:border-secondary outline-none" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Correo Electrónico</label>
            <div className="relative">
              <Mail className="w-5 h-5 absolute left-3 top-2.5 text-gray-400" />
              <input type="email" value={formData.email} onChange={e=>setFormData({...formData, email: e.target.value})} required
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary focus:border-secondary outline-none" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña Máster</label>
            <div className="relative">
              <Lock className="w-5 h-5 absolute left-3 top-2.5 text-gray-400" />
              <input type="password" value={formData.password} onChange={e=>setFormData({...formData, password: e.target.value})} required
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary focus:border-secondary outline-none" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Rol a Asumir (Demo Mode)</label>
            <div className="relative">
              <Shield className="w-5 h-5 absolute left-3 top-2.5 text-gray-400" />
              <select value={formData.rol} onChange={e=>setFormData({...formData, rol: e.target.value})}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary focus:border-secondary outline-none bg-white">
                <option value="operador">Operador (Básico)</option>
                <option value="supervisor">Supervisor (Aprobador)</option>
                <option value="admin">Administrador (Creador Grupos)</option>
              </select>
            </div>
          </div>
          
          <button type="submit" disabled={loading}
            className="w-full bg-secondary hover:bg-blue-700 text-white font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 mt-2">
            <UserPlus className="w-5 h-5" />
            {loading ? 'Procesando...' : 'Crear Cuenta'}
          </button>
        </form>
        
        <div className="mt-6 text-center text-sm text-gray-500">
          ¿Ya tienes cuenta? <Link to="/login" className="text-secondary font-medium hover:underline">Inicia Sesión</Link>
        </div>
      </div>
    </div>
  );
}

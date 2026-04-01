import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogIn, Lock, Mail } from 'lucide-react';
import axios from 'axios';

const api = axios.create({ baseURL: 'http://localhost:8000/api' });

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await api.post('/auth/login', { email, password });
      login(response.data.usuario, response.data.access_token);
      
      if (['admin', 'supervisor'].includes(response.data.usuario.rol)) {
          navigate('/admin');
      } else {
          navigate('/nuevo-envio');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al iniciar sesión. Revisa tus credenciales.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100 mx-auto mt-20">
      <div className="bg-primary p-6 text-white text-center">
        <h2 className="text-2xl font-bold">Nexo Data RRHH</h2>
        <p className="text-sm opacity-80 mt-1">Portal Seguro Corporativo</p>
      </div>
      <div className="p-8">
        {error && <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded-lg">{error}</div>}
        
        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Correo Electrónico</label>
            <div className="relative">
              <Mail className="w-5 h-5 absolute left-3 top-2.5 text-gray-400" />
              <input type="email" value={email} onChange={e=>setEmail(e.target.value)} required
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary focus:border-secondary outline-none transition-all" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña</label>
            <div className="relative">
              <Lock className="w-5 h-5 absolute left-3 top-2.5 text-gray-400" />
              <input type="password" value={password} onChange={e=>setPassword(e.target.value)} required
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary focus:border-secondary outline-none transition-all" />
            </div>
          </div>
          
          <button type="submit" disabled={loading}
            className="w-full bg-secondary hover:bg-blue-700 text-white font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2">
            <LogIn className="w-5 h-5" />
            {loading ? 'Entrando...' : 'Ingresar al Wizard'}
          </button>
        </form>
        
        <div className="mt-6 text-center text-sm text-gray-500">
          ¿No tienes cuenta de acceso? <Link to="/register" className="text-secondary font-medium hover:underline">Regístrate Aquí</Link>
        </div>
      </div>
    </div>
  );
}

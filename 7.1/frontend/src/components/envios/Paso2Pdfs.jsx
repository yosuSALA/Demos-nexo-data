import React, { useState, useEffect, useRef } from 'react';
import { Users, CheckSquare, Square, ArrowRight, ArrowLeft, Loader2, Search, X, Mail, AlertCircle, Info } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';

export default function Paso2Destinatarios({ onNext, onPrev, data, updateData }) {
  const { user } = useAuth();
  const [destinatarios, setDestinatarios] = useState([]);
  const [seleccionados, setSeleccionados] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Autocomplete
  const [allUsers, setAllUsers] = useState([]); // todos los usuarios del sistema
  const [busqueda, setBusqueda] = useState('');
  const [mostrarSugerencias, setMostrarSugerencias] = useState(false);
  const searchRef = useRef(null);

  const puedeAgregarExtra = ['admin', 'supervisor'].includes(user?.rol);

  // Cargar miembros del grupo seleccionado
  useEffect(() => {
    if (!data.grupo_id) { setError('No hay grupo seleccionado.'); setLoading(false); return; }
    const token = localStorage.getItem('rrhh_token');
    setLoading(true); setError('');
    axios.get(`http://localhost:8000/api/grupos/${data.grupo_id}/miembros`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    .then(res => setDestinatarios(res.data.map(u => ({ id: u.id, nombre: u.nombre, email: u.email, rol: u.rol, esManual: false }))))
    .catch(() => setError('No se pudo cargar los miembros del grupo.'))
    .finally(() => setLoading(false));
  }, [data.grupo_id]);

  // Para admin/supervisor: cargar todos los usuarios para el autocomplete
  useEffect(() => {
    if (!puedeAgregarExtra) return;
    const token = localStorage.getItem('rrhh_token');
    axios.get('http://localhost:8000/api/usuarios/para-envio', { headers: { Authorization: `Bearer ${token}` } })
      .then(res => setAllUsers(res.data))
      .catch(() => {});
  }, []);

  // Cerrar sugerencias al clic fuera
  useEffect(() => {
    const handler = (e) => { if (searchRef.current && !searchRef.current.contains(e.target)) setMostrarSugerencias(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  useEffect(() => {
    updateData({ ...data, destinatarios: destinatarios.filter(d => seleccionados.includes(d.id)) });
  }, [seleccionados, destinatarios]);

  const toggle = (id) => setSeleccionados(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  const seleccionarTodos = () => setSeleccionados(seleccionados.length === destinatarios.length ? [] : destinatarios.map(d => d.id));

  const agregarDesdeSugerencia = (u) => {
    const yaEsta = destinatarios.find(d => d.id === u.id);
    if (!yaEsta) {
      const nuevo = { id: u.id, nombre: u.nombre, email: u.email, rol: u.rol || 'externo', esManual: true };
      setDestinatarios(prev => [...prev, nuevo]);
      setSeleccionados(prev => [...prev, u.id]);
    } else {
      // Si ya está en la lista, solo seleccionarlo
      setSeleccionados(prev => prev.includes(u.id) ? prev : [...prev, u.id]);
    }
    setBusqueda(''); setMostrarSugerencias(false);
  };

  const eliminar = (id) => {
    setDestinatarios(prev => prev.filter(d => d.id !== id));
    setSeleccionados(prev => prev.filter(x => x !== id));
  };

  // Sugerencias filtradas: usuarios que coinciden con búsqueda y NO están ya en la lista
  const idsActuales = new Set(destinatarios.map(d => d.id));
  const sugerencias = allUsers.filter(u =>
    (u.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
     u.email.toLowerCase().includes(busqueda.toLowerCase())) &&
    !idsActuales.has(u.id)
  ).slice(0, 8);

  const todos = seleccionados.length === destinatarios.length && destinatarios.length > 0;
  const alguno = seleccionados.length > 0;
  const ROL_COLOR = { admin: 'text-purple-600 bg-purple-50', supervisor: 'text-blue-600 bg-blue-50', operador: 'text-green-600 bg-green-50', externo: 'text-amber-600 bg-amber-50' };

  return (
    <div className="flex flex-col space-y-5 animate-in fade-in zoom-in-95 duration-500">
      <div className="text-center">
        <h2 className="text-xl font-bold text-primary flex items-center justify-center gap-2">
          <Users className="text-secondary" /> Seleccionar Destinatarios
        </h2>
        <p className="text-gray-500 mt-1 text-sm">
          Miembros del grupo seleccionado. Elige a quién enviarás el correo.
        </p>
      </div>

      {/* Info: cuál grupo está seleccionado */}
      {data.grupo_id && !loading && !error && (
        <div className="flex items-center gap-2 bg-blue-50 border border-blue-100 rounded-xl px-4 py-2.5 text-sm text-blue-700">
          <Info size={15} className="shrink-0" />
          <span>Mostrando miembros del <strong>Grupo ID:{data.grupo_id}</strong>.
            {destinatarios.length === 0 && ' — Sin miembros asignados aún.'}
          </span>
        </div>
      )}

      {/* Barra superior */}
      {!loading && !error && (
        <div className="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 gap-4">
          <button
            onClick={seleccionarTodos}
            disabled={destinatarios.length === 0}
            className="flex items-center gap-2 text-sm font-semibold text-primary hover:text-secondary transition-colors disabled:opacity-40 shrink-0"
          >
            {todos
              ? <><CheckSquare size={18} className="text-secondary" /> Deseleccionar todos</>
              : <><Square size={18} /> Seleccionar todos ({destinatarios.length})</>}
          </button>

          {/* Autocomplete solo para admin/supervisor */}
          {puedeAgregarExtra && (
            <div className="relative flex-1 max-w-xs" ref={searchRef}>
              <div className="flex items-center gap-2 border border-gray-300 hover:border-secondary rounded-lg px-3 py-2 bg-white transition">
                <Search size={14} className="text-gray-400 shrink-0" />
                <input
                  type="text"
                  placeholder="Buscar usuario extra..."
                  value={busqueda}
                  onChange={e => { setBusqueda(e.target.value); setMostrarSugerencias(true); }}
                  onFocus={() => busqueda && setMostrarSugerencias(true)}
                  className="flex-1 text-sm outline-none bg-transparent"
                />
                {busqueda && <button onClick={() => { setBusqueda(''); setMostrarSugerencias(false); }}><X size={13} className="text-gray-400 hover:text-gray-600" /></button>}
              </div>
              {mostrarSugerencias && busqueda && (
                <div className="absolute top-full mt-1 left-0 right-0 bg-white border border-gray-200 rounded-xl shadow-lg z-20 overflow-hidden">
                  {sugerencias.length === 0 ? (
                    <div className="px-4 py-3 text-sm text-gray-400">Sin resultados para "{busqueda}"</div>
                  ) : (
                    sugerencias.map(u => (
                      <button key={u.id} onClick={() => agregarDesdeSugerencia(u)}
                        className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-blue-50 text-left transition">
                        <div className="w-7 h-7 rounded-full bg-gray-100 text-gray-600 flex items-center justify-center text-sm font-bold shrink-0">
                          {u.nombre.charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-sm text-gray-800">{u.nombre}</p>
                          <p className="text-xs text-gray-400 truncate">{u.email}</p>
                        </div>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0 ${ROL_COLOR[u.rol] || ROL_COLOR.externo}`}>{u.rol}</span>
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>
          )}

          {alguno && (
            <span className="text-xs font-bold bg-secondary text-white px-3 py-1.5 rounded-full shrink-0">
              {seleccionados.length} sel.
            </span>
          )}
        </div>
      )}

      {/* Estado: cargando */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-14 gap-3">
          <Loader2 className="w-8 h-8 text-secondary animate-spin" />
          <p className="text-sm text-gray-400">Cargando miembros del grupo...</p>
        </div>
      )}

      {/* Estado: error */}
      {!loading && error && (
        <div className="flex items-start gap-3 bg-red-50 border border-red-100 rounded-xl p-4 text-red-600 text-sm">
          <AlertCircle size={18} className="shrink-0 mt-0.5" />{error}
        </div>
      )}

      {/* Lista de miembros */}
      {!loading && !error && (
        <div className="border border-gray-200 rounded-xl overflow-hidden">
          {destinatarios.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <Mail size={32} className="mx-auto mb-3 opacity-40" />
              <p className="font-medium">Este grupo no tiene miembros asignados todavía.</p>
              {user?.rol === 'admin' && (
                <p className="text-sm mt-1 text-blue-500">
                  Ve al <strong>Panel Admin → Asignar Grupos</strong> y agrega usuarios a este grupo.
                </p>
              )}
              {puedeAgregarExtra && (
                <p className="text-sm mt-1 text-gray-400">
                  Puedes usar <strong>"Agregar correo extra"</strong> para enviar sin miembros del grupo.
                </p>
              )}
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {destinatarios.map(d => {
                const sel = seleccionados.includes(d.id);
                return (
                  <div
                    key={d.id}
                    onClick={() => toggle(d.id)}
                    className={`flex items-center gap-4 px-5 py-3.5 cursor-pointer transition-all ${
                      sel ? 'bg-blue-50 border-l-4 border-l-secondary' : 'hover:bg-gray-50 border-l-4 border-l-transparent'
                    }`}
                  >
                    {/* Checkbox */}
                    <div className={`w-5 h-5 rounded border-2 flex items-center justify-center shrink-0 transition-all ${
                      sel ? 'bg-secondary border-secondary' : 'border-gray-300'
                    }`}>
                      {sel && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>}
                    </div>
                    {/* Avatar */}
                    <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold shrink-0 ${
                      sel ? 'bg-secondary text-white' : 'bg-gray-100 text-gray-600'
                    }`}>
                      {d.nombre.charAt(0).toUpperCase()}
                    </div>
                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className={`font-semibold text-sm ${sel ? 'text-primary' : 'text-gray-800'}`}>{d.nombre}</p>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${ROL_COLOR[d.rol] || ROL_COLOR.externo}`}>
                          {d.rol}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 truncate">{d.email || 'Sin correo registrado'}</p>
                    </div>
                    {/* X solo en manuales */}
                    {d.esManual && (
                      <button onClick={e => { e.stopPropagation(); eliminar(d.id); }}
                        className="text-gray-300 hover:text-red-400 transition-colors p-1 rounded">
                        <X size={15} />
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Resumen selección */}
      {alguno && (
        <div className="bg-green-50 border border-green-100 rounded-xl px-5 py-3 text-sm text-green-700 font-medium flex items-center gap-2 flex-wrap">
          <CheckSquare size={16} />
          Enviarás a <strong>{seleccionados.length}</strong> persona(s):{' '}
          {destinatarios.filter(d => seleccionados.includes(d.id)).map(d => d.nombre).join(', ')}
        </div>
      )}

      {/* Navegación */}
      <div className="pt-2 flex justify-between items-center">
        <button onClick={onPrev} className="flex items-center text-gray-500 hover:text-primary font-medium px-4 py-2">
          <ArrowLeft size={18} className="mr-2" /> Atrás
        </button>
        <button
          onClick={onNext}
          disabled={!alguno}
          className="flex items-center gap-2 bg-secondary hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold py-3 px-8 rounded-lg shadow-md transition-all"
        >
          Configurar Correo <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );
}

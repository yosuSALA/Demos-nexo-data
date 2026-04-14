import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  Users, PlusCircle, UserCog, Shield, Loader2, Send,
  Pencil, Trash2, Check, X, AlertTriangle, UserMinus,
  UserPlus, FileUp, UploadCloud, ChevronDown, Download
} from 'lucide-react';

function ConfirmModal({ mensaje, onConfirm, onCancel }) {
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl p-6 max-w-sm w-full mx-4">
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-red-100 p-2 rounded-full"><AlertTriangle className="w-5 h-5 text-red-600" /></div>
          <h3 className="font-bold text-gray-800">Confirmar eliminación</h3>
        </div>
        <p className="text-gray-600 text-sm mb-6">{mensaje}</p>
        <div className="flex gap-3 justify-end">
          <button onClick={onCancel} className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg transition">Cancelar</button>
          <button onClick={onConfirm} className="px-4 py-2 text-sm font-semibold bg-red-600 text-white hover:bg-red-700 rounded-lg transition">Sí, eliminar</button>
        </div>
      </div>
    </div>
  );
}

const ROL_BADGE = { admin: 'bg-purple-100 text-purple-700', supervisor: 'bg-blue-100 text-blue-700', operador: 'bg-green-100 text-green-700' };

export default function AdminDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const token = localStorage.getItem('rrhh_token');
  const api = axios.create({ baseURL: 'http://localhost:8000/api', headers: { Authorization: `Bearer ${token}` } });

  // Grupos
  const [grupos, setGrupos] = useState([]);
  const [nombreGrupo, setNombreGrupo] = useState('');
  const [loadingGrupo, setLoadingGrupo] = useState(false);
  const [editandoId, setEditandoId] = useState(null);
  const [editNombre, setEditNombre] = useState('');
  const [confirmBorrar, setConfirmBorrar] = useState(null);

  // Usuarios
  const [usuarios, setUsuarios] = useState([]);
  const [loadingUsuarios, setLoadingUsuarios] = useState(false);

  // Asignación
  const [asignGrupoId, setAsignGrupoId] = useState('');
  const [miembrosGrupo, setMiembrosGrupo] = useState([]);
  const [loadingMiembros, setLoadingMiembros] = useState(false);
  const [asignUserId, setAsignUserId] = useState('');
  const [loadingAsign, setLoadingAsign] = useState(false);
  const [asignMsg, setAsignMsg] = useState({ text: '', ok: true });

  // Empleados
  const [empleados, setEmpleados] = useState([]);
  const [loadingEmpleados, setLoadingEmpleados] = useState(false);
  const [filtroGrupoEmp, setFiltroGrupoEmp] = useState('');
  const [confirmBorrarEmp, setConfirmBorrarEmp] = useState(null);
  
  // Modal importar
  const [showImport, setShowImport] = useState(false);
  const [importFile, setImportFile] = useState(null);
  const [importGrupoId, setImportGrupoId] = useState('');
  const [importLoading, setImportLoading] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const fileInputRef = React.useRef(null);

  const [tab, setTab] = useState('grupos');
  const esAdmin = user?.rol === 'admin';
  const esSupervisor = user?.rol === 'supervisor';
  const puedeGestionarMiembros = esAdmin || esSupervisor;
  const puedeGestionarEmpleados = esAdmin || esSupervisor;

  const cargarGrupos = async () => {
    try { const r = await api.get('/grupos/'); setGrupos(r.data); } catch (e) {}
  };

  const cargarUsuarios = async () => {
    setLoadingUsuarios(true);
    try { const r = await api.get('/usuarios/'); setUsuarios(r.data); } catch (e) {}
    finally { setLoadingUsuarios(false); }
  };

  const cargarEmpleados = async (grupoId = '') => {
    setLoadingEmpleados(true);
    try {
      const params = grupoId ? { grupo_id: grupoId } : {};
      const r = await api.get('/empleados/', { params });
      setEmpleados(r.data);
    } catch (e) {}
    finally { setLoadingEmpleados(false); }
  };

  const cargarMiembros = async (grupoId) => {
    if (!grupoId) { setMiembrosGrupo([]); return; }
    setLoadingMiembros(true);
    try { const r = await api.get(`/grupos/${grupoId}/miembros`); setMiembrosGrupo(r.data); }
    catch (e) { setMiembrosGrupo([]); }
    finally { setLoadingMiembros(false); }
  };

  useEffect(() => { cargarGrupos(); cargarUsuarios(); }, []);
  useEffect(() => { if (tab === 'empleados') cargarEmpleados(filtroGrupoEmp); }, [tab, filtroGrupoEmp]);

  // Cuando cambia el grupo seleccionado en Asignar, cargar miembros
  useEffect(() => { cargarMiembros(asignGrupoId); setAsignMsg({ text: '', ok: true }); }, [asignGrupoId]);

  const handleCreateGrupo = async (e) => {
    e.preventDefault(); setLoadingGrupo(true);
    try { await api.post('/grupos/', { nombre: nombreGrupo }); setNombreGrupo(''); cargarGrupos(); }
    catch (e) { alert('Error: ' + (e.response?.data?.detail || e.message)); }
    finally { setLoadingGrupo(false); }
  };

  const handleEditarGrupo = async (id) => {
    if (!editNombre.trim()) return;
    try { await api.patch(`/grupos/${id}`, { nombre: editNombre }); setEditandoId(null); setEditNombre(''); cargarGrupos(); }
    catch (e) { alert('Error: ' + (e.response?.data?.detail || e.message)); }
  };

  const handleBorrarGrupo = async () => {
    try { await api.delete(`/grupos/${confirmBorrar.id}`); setConfirmBorrar(null); cargarGrupos(); }
    catch (e) { alert('Error: ' + (e.response?.data?.detail || e.message)); }
  };

  const handleCambiarRol = async (uid, rol) => {
    try { await api.patch(`/usuarios/${uid}/rol`, { rol }); cargarUsuarios(); }
    catch (e) { alert('Error: ' + (e.response?.data?.detail || e.message)); }
  };

  const handleAsignar = async (e) => {
    e.preventDefault();
    if (!asignGrupoId || !asignUserId) return;
    setLoadingAsign(true); setAsignMsg({ text: '', ok: true });
    try {
      const r = await api.post(`/grupos/${asignGrupoId}/asignar`, { user_id: parseInt(asignUserId) });
      setAsignMsg({ text: r.data.msg, ok: true });
      setAsignUserId('');
      cargarMiembros(asignGrupoId);
    } catch (e) { setAsignMsg({ text: e.response?.data?.detail || e.message, ok: false }); }
    finally { setLoadingAsign(false); }
  };

  const handleDesasignar = async (userId, userName) => {
    if (!window.confirm(`¿Quitar a "${userName}" del grupo?`)) return;
    try {
      await api.delete(`/grupos/${asignGrupoId}/desasignar/${userId}`);
      cargarMiembros(asignGrupoId);
    } catch (e) { alert('Error: ' + (e.response?.data?.detail || e.message)); }
  };

  // Usuarios no asignados al grupo actual (para el dropdown de asignar)
  const miembrosIds = miembrosGrupo.map(m => m.id);
  const usuariosDisponibles = usuarios.filter(u => !miembrosIds.includes(u.id));

  const handleEliminarEmpleado = async () => {
    if (!confirmBorrarEmp) return;
    try {
      await api.delete(`/empleados/${confirmBorrarEmp.id}`);
      setConfirmBorrarEmp(null);
      cargarEmpleados(filtroGrupoEmp);
    } catch (e) { alert('Error: ' + (e.response?.data?.detail || e.message)); }
  };

  const handleCambiarGrupoEmpleado = async (empId, nuevoGrupoId) => {
    try {
      await api.patch(`/empleados/${empId}`, { grupo_id: nuevoGrupoId ? parseInt(nuevoGrupoId) : null });
      cargarEmpleados(filtroGrupoEmp);
    } catch (e) { alert('Error al cambiar grupo: ' + (e.response?.data?.detail || e.message)); }
  };



  const handleImportar = async (e) => {
    e.preventDefault();
    if (!importFile) return;
    setImportLoading(true); setImportResult(null);
    const form = new FormData();
    form.append('file', importFile);
    const params = importGrupoId ? `?grupo_id=${importGrupoId}` : '';
    try {
      const r = await api.post(`/empleados/importar${params}`, form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setImportResult(r.data);
      cargarEmpleados(filtroGrupoEmp);
    } catch (e) { setImportResult({ error: e.response?.data?.detail || e.message }); }
    finally { setImportLoading(false); }
  };

  const ALL_TABS = [
    { id: 'grupos', label: 'Grupos', icon: Users, roles: ['admin', 'supervisor'] },
    { id: 'usuarios', label: esAdmin ? 'Usuarios' : 'Usuarios (Solo lectura)', icon: UserCog, roles: ['admin', 'supervisor'] },
    { id: 'asignar', label: 'Asignar Miembros', icon: Shield, roles: ['admin', 'supervisor'] },
    { id: 'empleados', label: 'Empleados', icon: UserPlus, roles: ['admin', 'supervisor'] },
  ];
  const TABS = ALL_TABS.filter(t => t.roles.includes(user?.rol));

  return (
    <div className="w-full max-w-5xl mx-auto">
      {confirmBorrar && (
        <ConfirmModal
          mensaje={`¿Seguro que quieres eliminar el grupo "${confirmBorrar.nombre}"? Esta acción no se puede deshacer.`}
          onConfirm={handleBorrarGrupo}
          onCancel={() => setConfirmBorrar(null)}
        />
      )}

      {/* Header */}
      <div className="flex justify-between items-center mb-6 bg-white p-5 rounded-2xl shadow-sm border border-gray-100">
        <div>
          <h1 className="text-2xl font-bold text-primary">Panel de Administración</h1>
          <p className="text-gray-500 text-sm mt-0.5">
            Nivel: <span className={`font-semibold ${esAdmin ? 'text-purple-600' : 'text-blue-600'}`}>{user?.rol?.toUpperCase()}</span> | {user?.nombre}
          </p>
        </div>
        <button onClick={() => navigate('/nuevo-envio')} className="flex items-center gap-2 bg-secondary text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition shadow-sm">
          <Send className="w-4 h-4" /> Ir al Wizard
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => setTab(id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-sm transition-all ${tab === id ? 'bg-primary text-white shadow-md' : 'bg-white text-gray-500 hover:bg-gray-50 border border-gray-200'}`}>
            <Icon className="w-4 h-4" /> {label}
          </button>
        ))}
      </div>

      {/* ══ TAB GRUPOS ══ */}
      {tab === 'grupos' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {esAdmin && (
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 h-fit">
              <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2"><PlusCircle className="w-5 h-5 text-secondary" /> Crear Grupo</h3>
              <form onSubmit={handleCreateGrupo} className="space-y-4">
                <input type="text" value={nombreGrupo} onChange={e => setNombreGrupo(e.target.value)} required placeholder="Ej. Operaciones Sur..."
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-secondary outline-none transition" />
                <button type="submit" disabled={loadingGrupo}
                  className="w-full bg-primary text-white py-2.5 rounded-lg font-medium hover:bg-blue-900 transition flex items-center justify-center gap-2">
                  {loadingGrupo ? <Loader2 className="w-4 h-4 animate-spin" /> : <PlusCircle className="w-4 h-4" />}
                  {loadingGrupo ? 'Guardando...' : 'Añadir a Base de Datos'}
                </button>
              </form>
            </div>
          )}
          <div className={`${esAdmin ? 'md:col-span-2' : 'md:col-span-3'} bg-white p-6 rounded-2xl shadow-sm border border-gray-100`}>
            <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2"><Users className="w-5 h-5 text-secondary" /> Grupos ({grupos.length})</h3>
            {grupos.length === 0 ? (
              <div className="text-center py-10 text-gray-400 bg-gray-50 rounded-xl border border-dashed border-gray-200">No hay grupos creados.</div>
            ) : (
              <div className="space-y-3">
                {grupos.map(g => (
                  <div key={g.id} className="border border-gray-100 rounded-xl bg-gray-50 hover:border-blue-100 transition">
                    {editandoId === g.id ? (
                      <div className="flex items-center gap-2 p-3">
                        <input autoFocus value={editNombre} onChange={e => setEditNombre(e.target.value)}
                          onKeyDown={e => e.key === 'Enter' && handleEditarGrupo(g.id)}
                          className="flex-1 px-3 py-1.5 border border-secondary rounded-lg text-sm font-medium focus:ring-2 focus:ring-secondary outline-none" />
                        <button onClick={() => handleEditarGrupo(g.id)} className="p-1.5 bg-green-100 hover:bg-green-200 text-green-700 rounded-lg"><Check size={16} /></button>
                        <button onClick={() => { setEditandoId(null); setEditNombre(''); }} className="p-1.5 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-lg"><X size={16} /></button>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between p-4">
                        <div className="flex items-center gap-3">
                          <span className="text-xs bg-white border border-gray-200 font-bold px-2 py-1 rounded-md text-gray-500 shadow-sm">ID: {g.id}</span>
                          <span className="font-bold text-gray-800">{g.nombre}</span>
                        </div>
                        {esAdmin && (
                          <div className="flex items-center gap-2">
                            <button onClick={() => { setEditandoId(g.id); setEditNombre(g.nombre); }}
                              className="p-1.5 hover:bg-blue-50 text-gray-400 hover:text-secondary rounded-lg transition" title="Editar nombre"><Pencil size={15} /></button>
                            <button onClick={() => setConfirmBorrar({ id: g.id, nombre: g.nombre })}
                              className="p-1.5 hover:bg-red-50 text-gray-400 hover:text-red-500 rounded-lg transition" title="Eliminar grupo"><Trash2 size={15} /></button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ══ TAB USUARIOS ══ */}
      {tab === 'usuarios' && (
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-bold text-gray-800 flex items-center gap-2"><UserCog className="w-5 h-5 text-secondary" /> Todos los Usuarios ({usuarios.length})</h3>
            {!esAdmin && <span className="text-xs bg-amber-50 text-amber-600 border border-amber-200 px-3 py-1 rounded-full font-medium">Solo lectura</span>}
          </div>
          {loadingUsuarios ? (
            <div className="flex justify-center py-10"><Loader2 className="w-8 h-8 text-secondary animate-spin" /></div>
          ) : (
            <div className="space-y-3">
              {usuarios.map(u => (
                <div key={u.id} className="flex items-center justify-between p-4 rounded-xl bg-gray-50 border border-gray-100 hover:border-blue-100 transition">
                  <div>
                    <p className="font-semibold text-gray-800">{u.nombre}</p>
                    <p className="text-xs text-gray-400">{u.email}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${ROL_BADGE[u.rol]}`}>{u.rol}</span>
                    {esAdmin && u.id !== user?.id && (
                      <select value={u.rol} onChange={e => handleCambiarRol(u.id, e.target.value)}
                        className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:ring-2 focus:ring-secondary outline-none">
                        <option value="operador">Operador</option>
                        <option value="supervisor">Supervisor</option>
                        <option value="admin">Admin</option>
                      </select>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ══ TAB ASIGNAR MIEMBROS ══ */}
      {tab === 'asignar' && puedeGestionarMiembros && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

          {/* Formulario izquierda */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h3 className="font-bold text-gray-800 mb-5 flex items-center gap-2">
              <Shield className="w-5 h-5 text-secondary" /> Asignar Miembro al Grupo
            </h3>
            <form onSubmit={handleAsignar} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Seleccionar Grupo</label>
                <select value={asignGrupoId} onChange={e => setAsignGrupoId(e.target.value)} required
                  className="w-full px-3 py-2.5 border rounded-lg focus:ring-2 focus:ring-secondary outline-none bg-white">
                  <option value="">-- Elige un grupo --</option>
                  {grupos.map(g => <option key={g.id} value={g.id}>{g.nombre} (ID: {g.id})</option>)}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Agregar Usuario</label>
                <select value={asignUserId} onChange={e => setAsignUserId(e.target.value)} required disabled={!asignGrupoId}
                  className="w-full px-3 py-2.5 border rounded-lg focus:ring-2 focus:ring-secondary outline-none bg-white disabled:opacity-50">
                  <option value="">-- Elige un usuario --</option>
                  {usuariosDisponibles.map(u => (
                    <option key={u.id} value={u.id}>{u.nombre} [{u.rol}] — {u.email}</option>
                  ))}
                </select>
                {asignGrupoId && usuariosDisponibles.length === 0 && (
                  <p className="text-xs text-green-600 mt-1">✅ Todos los usuarios ya están en este grupo.</p>
                )}
              </div>
              {asignMsg.text && (
                <div className={`p-3 rounded-lg text-sm font-medium ${asignMsg.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'}`}>
                  {asignMsg.ok ? '✅ ' : '❌ '}{asignMsg.text}
                </div>
              )}
              <button type="submit" disabled={loadingAsign || !asignGrupoId || !asignUserId}
                className="w-full bg-secondary text-white py-2.5 rounded-lg font-semibold hover:bg-blue-700 transition flex items-center justify-center gap-2 disabled:opacity-50">
                {loadingAsign ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                {loadingAsign ? 'Asignando...' : 'Confirmar Asignación'}
              </button>
            </form>
          </div>

          {/* Miembros actuales del grupo - derecha */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
              <Users className="w-5 h-5 text-secondary" />
              {asignGrupoId
                ? `Miembros del Grupo (${miembrosGrupo.length})`
                : 'Selecciona un grupo'}
            </h3>

            {!asignGrupoId && (
              <div className="text-center py-10 text-gray-400 bg-gray-50 rounded-xl border border-dashed border-gray-200 text-sm">
                Elige un grupo a la izquierda para ver sus miembros actuales.
              </div>
            )}

            {asignGrupoId && loadingMiembros && (
              <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 text-secondary animate-spin" /></div>
            )}

            {asignGrupoId && !loadingMiembros && miembrosGrupo.length === 0 && (
              <div className="text-center py-10 text-gray-400 bg-gray-50 rounded-xl border border-dashed border-gray-200 text-sm">
                Este grupo no tiene miembros aún. Asigna uno con el formulario.
              </div>
            )}

            {asignGrupoId && !loadingMiembros && miembrosGrupo.length > 0 && (
              <div className="space-y-2">
                {miembrosGrupo.map(m => (
                  <div key={m.id} className="flex items-center justify-between p-3 rounded-xl bg-gray-50 border border-gray-100 hover:border-red-100 group transition">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-secondary text-white flex items-center justify-center text-sm font-bold shrink-0">
                        {m.nombre.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-semibold text-sm text-gray-800">{m.nombre}</p>
                        <p className="text-xs text-gray-400">{m.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${ROL_BADGE[m.rol]}`}>{m.rol}</span>
                      <button onClick={() => handleDesasignar(m.id, m.nombre)}
                        className="p-1.5 rounded-lg text-gray-300 hover:text-red-500 hover:bg-red-50 transition opacity-0 group-hover:opacity-100"
                        title="Quitar del grupo">
                        <UserMinus size={15} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB EMPLEADOS */}
      {tab === 'empleados' && puedeGestionarEmpleados && (
        <div className="space-y-5">

          {confirmBorrarEmp && (
            <ConfirmModal
              mensaje={`¿Estás seguro de que deseas eliminar a "${confirmBorrarEmp.nombre} ${confirmBorrarEmp.apellido}" (Cédula: ${confirmBorrarEmp.cedula})? Esta acción no se puede deshacer.`}
              onConfirm={handleEliminarEmpleado}
              onCancel={() => setConfirmBorrarEmp(null)}
            />
          )}

          <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 flex flex-wrap items-center gap-3">
            <div className="flex-1 min-w-[200px]">
              <label className="text-xs font-semibold text-gray-500 mb-1 block">Filtrar por Grupo</label>
              <select value={filtroGrupoEmp} onChange={e => setFiltroGrupoEmp(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm bg-white focus:ring-2 focus:ring-secondary outline-none">
                <option value="">Todos los grupos</option>
                {grupos.map(g => <option key={g.id} value={g.id}>{g.nombre}</option>)}
              </select>
            </div>
            <div className="flex items-end gap-2 pt-4">
              <span className="text-sm text-gray-500 font-medium">{empleados.length} empleado{empleados.length !== 1 ? 's' : ''}</span>
              <button onClick={() => { setShowImport(true); setImportResult(null); setImportFile(null); }}
                className="flex items-center gap-2 bg-secondary text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-blue-700 transition shadow-sm">
                <UploadCloud className="w-4 h-4" /> Importar Excel/CSV
              </button>
            </div>
          </div>

          {showImport && (
            <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-lg">
                <div className="flex items-center justify-between mb-5">
                  <h3 className="font-bold text-gray-800 flex items-center gap-2">
                    <FileUp className="w-5 h-5 text-secondary" /> Importar Empleados
                  </h3>
                  <button onClick={() => setShowImport(false)} className="p-1.5 hover:bg-gray-100 rounded-lg transition"><X size={18} /></button>
                </div>
                {!importResult ? (
                  <form onSubmit={handleImportar} className="space-y-4">
                    <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 text-xs text-blue-700 space-y-1">
                      <p className="font-semibold">Columnas del archivo:</p>
                      <p><span className="font-bold">Requeridas:</span> cedula, nombre, apellido</p>
                      <p><span className="font-bold">Opcionales:</span> email, departamento, cargo, grupo_id</p>
                      <p className="text-blue-500">Los duplicados (misma cedula) se omiten automaticamente.</p>
                    </div>
                    
                    <a
                      href="/Nexus_Data.xlsx"
                      download="Plantilla_Nexo.xlsx"
                      className="w-full flex items-center justify-center gap-2 border-2 border-dashed border-green-300 bg-green-50 hover:bg-green-100 text-green-700 font-semibold py-2.5 rounded-xl transition cursor-pointer"
                    >
                      <Download className="w-4 h-4" />
                      Descargar Plantilla Oficial (con diseño)
                    </a>

                    <div>
                      <label className="text-sm font-medium text-gray-700 mb-1 block">Archivo (.xlsx o .csv)</label>
                      <div onClick={() => fileInputRef.current?.click()}
                        className="border-2 border-dashed border-gray-200 rounded-xl p-6 text-center cursor-pointer hover:border-secondary hover:bg-blue-50 transition group">
                        <UploadCloud className="w-8 h-8 text-gray-300 group-hover:text-secondary mx-auto mb-2 transition" />
                        {importFile
                          ? <p className="text-sm font-semibold text-secondary">{importFile.name}</p>
                          : <p className="text-sm text-gray-400">Haz clic o arrastra tu archivo aqui</p>}
                      </div>
                      <input ref={fileInputRef} type="file" accept=".xlsx,.csv" className="hidden"
                        onChange={e => setImportFile(e.target.files[0] || null)} />
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700 mb-1 block">Asignar a un grupo (opcional)</label>
                      <select value={importGrupoId} onChange={e => setImportGrupoId(e.target.value)}
                        className="w-full px-3 py-2.5 border rounded-lg text-sm bg-white focus:ring-2 focus:ring-secondary outline-none">
                        <option value="">Sin grupo (o usar columna grupo_id del archivo)</option>
                        {grupos.map(g => <option key={g.id} value={g.id}>{g.nombre}</option>)}
                      </select>
                    </div>
                    <button type="submit" disabled={importLoading || !importFile}
                      className="w-full bg-primary text-white py-2.5 rounded-lg font-semibold hover:bg-blue-900 transition flex items-center justify-center gap-2 disabled:opacity-50">
                      {importLoading
                        ? <><Loader2 className="w-4 h-4 animate-spin" /> Procesando...</>
                        : <><FileUp className="w-4 h-4" /> Importar Ahora</>}
                    </button>
                  </form>
                ) : (
                  <div className="space-y-4">
                    {importResult.error ? (
                      <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">{importResult.error}</div>
                    ) : (
                      <>
                        <div className="grid grid-cols-3 gap-3 text-center">
                          <div className="bg-green-50 border border-green-200 rounded-xl p-3">
                            <p className="text-2xl font-bold text-green-600">{importResult.insertados}</p>
                            <p className="text-xs text-green-600 font-medium">Insertados</p>
                          </div>
                          <div className="bg-amber-50 border border-amber-200 rounded-xl p-3">
                            <p className="text-2xl font-bold text-amber-500">{importResult.omitidos}</p>
                            <p className="text-xs text-amber-500 font-medium">Omitidos</p>
                          </div>
                          <div className="bg-red-50 border border-red-200 rounded-xl p-3">
                            <p className="text-2xl font-bold text-red-500">{importResult.errores?.length ?? 0}</p>
                            <p className="text-xs text-red-500 font-medium">Errores</p>
                          </div>
                        </div>
                        {importResult.errores?.length > 0 && (
                          <div className="bg-red-50 rounded-xl p-3 max-h-32 overflow-y-auto">
                            {importResult.errores.map((err, i) => <p key={i} className="text-xs text-red-600">- {err}</p>)}
                          </div>
                        )}
                      </>
                    )}
                    <div className="flex gap-2">
                      <button onClick={() => { setImportResult(null); setImportFile(null); }}
                        className="flex-1 py-2 text-sm border rounded-lg hover:bg-gray-50 transition font-medium">Importar otro</button>
                      <button onClick={() => setShowImport(false)}
                        className="flex-1 py-2 text-sm bg-primary text-white rounded-lg hover:bg-blue-900 transition font-semibold">Cerrar</button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            {loadingEmpleados ? (
              <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 text-secondary animate-spin" /></div>
            ) : empleados.length === 0 ? (
              <div className="text-center py-14 text-gray-400 text-sm bg-gray-50">
                <UserPlus className="w-10 h-10 mx-auto mb-3 text-gray-300" />
                No hay empleados. Importa un archivo para comenzar.
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-100 text-left">
                    <th className="px-4 py-3 font-semibold text-gray-500">Cedula</th>
                    <th className="px-4 py-3 font-semibold text-gray-500">Nombre</th>
                    <th className="px-4 py-3 font-semibold text-gray-500 hidden md:table-cell">Email</th>
                    <th className="px-4 py-3 font-semibold text-gray-500 hidden lg:table-cell">Grupo</th>
                    <th className="px-4 py-3 font-semibold text-gray-500">Estado</th>
                    <th className="px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {empleados.map(emp => (
                    <tr key={emp.id} className="hover:bg-gray-50 transition group">
                      <td className="px-4 py-3 font-mono text-xs text-gray-500">{emp.cedula}</td>
                      <td className="px-4 py-3">
                        <p className="font-semibold text-gray-800">{emp.nombre} {emp.apellido}</p>
                        {emp.cargo && <p className="text-xs text-gray-400">{emp.cargo}</p>}
                      </td>
                      <td className="px-4 py-3 text-gray-500 hidden md:table-cell">
                        {emp.email || <span className="text-gray-300">s/d</span>}
                      </td>
                      <td className="px-4 py-3 hidden lg:table-cell">
                        <select 
                          value={emp.grupo_id || ''} 
                          onChange={(e) => handleCambiarGrupoEmpleado(emp.id, e.target.value)}
                          className={`text-xs border ${emp.grupo_id ? 'border-blue-200 bg-blue-50 text-blue-700 font-medium' : 'border-gray-200 bg-white text-gray-500'} rounded-lg px-2 py-1.5 focus:ring-2 focus:ring-secondary outline-none w-full max-w-[140px] appearance-none cursor-pointer hover:border-secondary transition`}
                          title="Cambiar grupo"
                        >
                          <option value="">Sin grupo</option>
                          {grupos.map(g => (
                            <option key={g.id} value={g.id}>{g.nombre}</option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${emp.estado === 'prueba' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>
                          {emp.estado === 'prueba' ? 'Pendiente' : emp.estado}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button onClick={() => setConfirmBorrarEmp(emp)}
                          className="p-1.5 rounded-lg text-gray-300 hover:text-red-500 hover:bg-red-50 transition opacity-0 group-hover:opacity-100"
                          title="Eliminar empleado">
                          <Trash2 size={15} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

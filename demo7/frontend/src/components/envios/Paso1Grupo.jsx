import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';

export default function Paso1Grupo({ data, updateData, onNext }) {
  const [gruposFetch, setGruposFetch] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user, logout } = useAuth();

  useEffect(() => {
    const token = localStorage.getItem('rrhh_token');
    // Operador: solo sus grupos asignados. Admin/Supervisor: todos.
    const endpoint = 'http://localhost:8000/api/grupos/mis-grupos';
    axios.get(endpoint, {
       headers: { Authorization: `Bearer ${token}` }
    })
    .then(res => {
        setGruposFetch(res.data);
        setLoading(false);
    })
    .catch(err => {
        console.error(err);
        setLoading(false);
    });
  }, []);

  const selectGroup = (id, nombre) => {
    updateData({ ...data, grupo_id: id });
  };

  return (
    <div className="space-y-6 animate-fade-in pb-8">
      {/* Header Interactivo que muestra tu Sesión */}
      <div className="flex justify-between items-center text-sm mb-4 bg-blue-50 p-3 rounded-lg border border-blue-100 max-w-3xl mx-auto">
         <span className="font-semibold text-primary">Operador Registrado: <span className="text-gray-600 font-normal">{user?.nombre}</span></span>
         <div className="flex gap-4">
             {user?.rol === 'admin' && (
                 <a href="/admin" className="text-secondary font-bold hover:underline">Panel Admin (Crear Grupos)</a>
             )}
             <button onClick={logout} className="text-red-500 font-medium hover:underline">Cerrar Sesión</button>
         </div>
      </div>

      <div className="text-center mt-2">
        <h2 className="text-xl font-bold text-primary flex items-center justify-center gap-2">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
          Selección de Destino
        </h2>
        <p className="text-gray-500 text-sm mt-2">Estos grupos provienen directamente de la Base de Datos SQLite.</p>
      </div>

      {loading ? (
          <div className="text-center text-gray-400 p-8 font-medium animate-pulse">Conectando con Servidor Python...</div>
      ) : (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl mx-auto mt-6">
        {gruposFetch.length === 0 && (
           <div className="col-span-2 text-center text-red-500 p-6 bg-red-50 rounded-xl border border-red-100 font-medium shadow-sm">
               🚨 No hay grupos en la Base de Datos.<br/>
               <span className="text-sm font-normal text-gray-600 block mt-1">Cierra sesión, Regístrate como Admin y créalos en el Panel.</span>
           </div>
        )}
        {gruposFetch.map((grupo) => (
          <div 
            key={grupo.id}
            onClick={() => selectGroup(grupo.id, grupo.nombre)}
            className={`cursor-pointer transition-all duration-200 border rounded-xl p-6 hover:shadow-md flex justify-between items-center ${
              data.grupo_id === grupo.id 
                ? 'border-secondary bg-blue-50 ring-2 ring-secondary ring-opacity-50 shadow-sm' 
                : 'border-gray-200 bg-white hover:border-blue-300'
            }`}
          >
            <span className={`font-semibold ${data.grupo_id === grupo.id ? 'text-primary' : 'text-gray-700'}`}>
              {grupo.nombre}
            </span>
            <span className="text-xs bg-gray-100 text-gray-500 border border-gray-200 px-3 py-1 rounded-full font-bold shadow-sm">
              SQL ID: {grupo.id}
            </span>
          </div>
        ))}
      </div>
      )}

      <div className="flex justify-end pt-4 max-w-3xl mx-auto border-t border-gray-100 mt-6 gap-4">
        <button 
          onClick={onNext}
          disabled={!data.grupo_id}
          className={`px-8 py-2.5 rounded-lg flex items-center font-bold tracking-wide transition-all ${
            data.grupo_id
              ? 'bg-secondary text-white hover:bg-blue-700 shadow-md transform hover:scale-105'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
        >
          SIGUIENTE PASO
          <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
        </button>
      </div>
    </div>
  );
}

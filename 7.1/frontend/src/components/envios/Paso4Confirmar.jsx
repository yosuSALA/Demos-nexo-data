import React, { useState } from 'react';
import {
  Send, CheckCircle, ArrowLeft, ShieldCheck, MailWarning,
  Loader2, AlertCircle, XCircle, BarChart2
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';

export default function Paso4Confirmar({ onPrev, data }) {
  const { user } = useAuth();
  const [ejecutando, setEjecutando] = useState(false);
  const [terminado,  setTerminado]  = useState(false);
  const [resultado,  setResultado]  = useState(null);
  const [error,      setError]      = useState('');

  const isDirectExecution = user?.rol === 'admin' || user?.rol === 'supervisor';

  const handleAction = async () => {
    const token = localStorage.getItem('rrhh_token');
    setEjecutando(true);
    setError('');

    try {
      // 1. Crear el envío en la BD
      const mes = new Date().toLocaleDateString('es-EC', { month: 'long', year: 'numeric' });
      const crearRes = await axios.post(
        'http://localhost:8000/api/envios/',
        {
          nombre:       `Envío ${data.asunto || 'Nómina'} – ${mes}`,
          grupo_id:     data.grupo_id,
          plantilla_id: data.plantilla_id || null,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const envioId = crearRes.data.id;

      // 2. Ejecutar el envío (llama al SMTP real)
      const ejecutarRes = await axios.post(
        `http://localhost:8000/api/envios/${envioId}/ejecutar`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setResultado(ejecutarRes.data);
      setTerminado(true);
    } catch (e) {
      const detalle = e.response?.data?.detail || e.message || 'Error desconocido.';
      setError(detalle);
      setEjecutando(false);
    }
  };

  // ── Pantalla de resultado ────────────────────────────────────────────────
  if (terminado && resultado) {
    const isPending = resultado.estado === 'pendiente_aprobacion';
    const total     = resultado.total     ?? 0;
    const ok        = resultado.enviados_ok    ?? 0;
    const fallos    = resultado.enviados_fallo ?? 0;

    return (
      <div className="flex flex-col items-center justify-center p-12 text-center animate-in zoom-in-50 duration-500">
        <div className={`p-6 rounded-full mb-6 ${isPending ? 'bg-orange-100 text-orange-500' : 'bg-green-100 text-green-600'}`}>
          <CheckCircle size={64} className={isPending ? '' : 'animate-pulse'} />
        </div>

        <h2 className="text-3xl font-bold text-gray-800 mb-2">
          {isPending ? 'Enviado a revisión' : '¡Proceso Terminado!'}
        </h2>

        <p className="text-gray-500 max-w-sm mb-4 text-base">{resultado.msg}</p>

        <span className={`text-sm font-bold px-4 py-1.5 rounded-full mb-8 ${
          isPending ? 'bg-orange-100 text-orange-700' : 'bg-green-100 text-green-700'
        }`}>
          {resultado.estado?.replace(/_/g, ' ').toUpperCase()}
        </span>

        {/* Métricas de resultado (solo si hubo envío real) */}
        {total > 0 && (
          <div className="flex gap-6 mb-8">
            <div className="flex flex-col items-center bg-gray-50 border border-gray-200 rounded-xl px-6 py-4">
              <BarChart2 size={20} className="text-gray-400 mb-1" />
              <span className="text-2xl font-bold text-primary">{total}</span>
              <span className="text-xs text-gray-400 mt-0.5">Total</span>
            </div>
            <div className="flex flex-col items-center bg-green-50 border border-green-200 rounded-xl px-6 py-4">
              <CheckCircle size={20} className="text-green-500 mb-1" />
              <span className="text-2xl font-bold text-green-700">{ok}</span>
              <span className="text-xs text-green-500 mt-0.5">Enviados</span>
            </div>
            {fallos > 0 && (
              <div className="flex flex-col items-center bg-red-50 border border-red-200 rounded-xl px-6 py-4">
                <XCircle size={20} className="text-red-500 mb-1" />
                <span className="text-2xl font-bold text-red-700">{fallos}</span>
                <span className="text-xs text-red-500 mt-0.5">Fallos</span>
              </div>
            )}
          </div>
        )}

        <button
          onClick={() => window.location.reload()}
          className="bg-primary text-white font-semibold py-3 px-8 rounded-lg shadow-md hover:bg-blue-900 transition-all"
        >
          Volver al Inicio
        </button>
      </div>
    );
  }

  // ── Pantalla principal ───────────────────────────────────────────────────
  return (
    <div className="flex flex-col space-y-6 animate-in fade-in zoom-in-95 duration-500">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-primary flex items-center justify-center gap-2">
          Resumen de la Transacción <Send className="text-secondary ml-2" />
        </h2>
      </div>

      {/* Resumen del despacho */}
      <div className="bg-gray-50 border border-gray-200 p-6 rounded-xl shadow-inner max-w-2xl mx-auto w-full">
        <h4 className="font-semibold text-gray-400 uppercase text-xs tracking-wider mb-4 border-b pb-2">
          Información del Despacho
        </h4>
        <div className="space-y-4">
          <div className="flex justify-between items-center border-b border-gray-100 pb-3">
            <span className="text-gray-600 font-medium">Grupo Destino:</span>
            <span className="text-primary font-bold text-lg">ID {data.grupo_id}</span>
          </div>
          <div className="flex justify-between items-center border-b border-gray-100 pb-3">
            <span className="text-gray-600 font-medium">Usuario:</span>
            <span className="text-gray-800 font-semibold">
              {user?.nombre}{' '}
              <span className="text-xs text-secondary font-bold">({user?.rol})</span>
            </span>
          </div>
          <div className="flex justify-between items-start border-b border-gray-100 pb-3">
            <span className="text-gray-600 font-medium">Asunto:</span>
            <span className="text-gray-800 font-mono text-sm max-w-[260px] text-right truncate">
              "{data.asunto}"
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600 font-medium">Modo de ejecución:</span>
            <span className={`text-sm font-bold px-3 py-0.5 rounded-full ${
              isDirectExecution
                ? 'bg-green-100 text-green-700'
                : 'bg-orange-100 text-orange-700'
            }`}>
              {isDirectExecution ? 'Directo' : 'Pendiente aprobación'}
            </span>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-3 bg-red-50 border border-red-100 rounded-xl p-4 text-red-600 text-sm max-w-2xl mx-auto w-full">
          <AlertCircle size={18} className="shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Spinner mientras envía */}
      {ejecutando && (
        <div className="flex flex-col items-center gap-3 py-6">
          <Loader2 className="w-8 h-8 text-secondary animate-spin" />
          <p className="text-sm text-gray-500 font-medium">
            Conectando con SMTP y enviando correos...
          </p>
          <p className="text-xs text-gray-400">
            Esto puede tomar unos segundos. No cierres la ventana.
          </p>
        </div>
      )}

      {/* Botones de acción */}
      {!ejecutando && (
        <div className="pt-10 flex flex-col items-center border-t border-gray-100 mt-8 gap-6">
          {isDirectExecution ? (
            <div className="text-center">
              <p className="text-sm font-bold text-green-700 bg-green-50 rounded-lg px-4 py-2 border border-green-200 mb-4 inline-flex items-center gap-2 shadow-sm">
                <ShieldCheck size={18} />
                {user?.rol === 'admin' ? 'ADMIN' : 'SUPERVISOR'} — Ejecución Directa Autorizada
              </p>
              <button
                onClick={handleAction}
                className="w-full sm:w-auto flex items-center justify-center gap-3 bg-secondary hover:bg-blue-700 text-white font-bold text-lg py-4 px-12 rounded-xl shadow-[0_4px_14px_0_rgba(37,99,235,0.39)] hover:shadow-[0_6px_20px_rgba(37,99,235,0.23)] transition-all hover:-translate-y-1"
              >
                Ejecutar Envío Ahora <Send size={22} />
              </button>
            </div>
          ) : (
            <div className="text-center">
              <p className="text-sm font-semibold text-orange-700 bg-orange-50 rounded-lg px-4 py-2 border border-orange-200 mb-4 inline-flex items-center gap-2 shadow-sm animate-pulse">
                <MailWarning size={18} />
                Tu Supervisor revisará este envío antes de que se ejecute.
              </p>
              <button
                onClick={handleAction}
                className="w-full sm:w-auto flex items-center justify-center gap-3 bg-primary hover:bg-blue-900 text-white font-bold text-lg py-4 px-12 rounded-xl shadow-[0_4px_14px_0_rgba(26,60,110,0.39)] transition-all hover:-translate-y-1"
              >
                Enviar para Aprobación
              </button>
            </div>
          )}

          <button
            onClick={onPrev}
            className="text-gray-400 hover:text-gray-800 font-medium text-sm flex items-center gap-1 transition-colors"
          >
            <ArrowLeft size={16} /> Regresar y editar el correo
          </button>
        </div>
      )}
    </div>
  );
}

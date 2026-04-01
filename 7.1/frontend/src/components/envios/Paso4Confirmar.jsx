import React, { useState, useEffect } from 'react';
import { Send, CheckCircle, ArrowLeft, ShieldCheck, MailWarning, Loader2 } from 'lucide-react';

export default function Paso4Confirmar({ onPrev, data }) {
  const [ejecutando, setEjecutando] = useState(false);
  const [progreso, setProgreso] = useState(0);
  const [terminado, setTerminado] = useState(false);

  // MOCK JWT ROL para la demo UI visual de los 2 botones
  // Puede ser: 'admin', 'supervisor', 'operador_con_confianza', 'operador_sin_confianza'
  const [mockRol, setMockRol] = useState('operador_sin_confianza');

  const isDirectExecution = ['admin', 'supervisor', 'operador_con_confianza'].includes(mockRol);

  // Simulación de WebSocket/Barra de Progreso
  useEffect(() => {
    let intervalo;
    if (ejecutando && progreso < 100) {
      intervalo = setInterval(() => {
        setProgreso(p => {
          if (p >= 98) {
            clearInterval(intervalo);
            setTimeout(() => setTerminado(true), 500);
            return 100;
          }
          return p + Math.floor(Math.random() * 15) + 5;
        });
      }, 400);
    }
    return () => clearInterval(intervalo);
  }, [ejecutando, progreso]);

  const handleAction = () => {
    setEjecutando(true);
  };

  if (terminado) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center animate-in zoom-in-50 duration-500">
        <div className="bg-green-100 text-green-600 p-6 rounded-full mb-6 relative">
          <CheckCircle size={64} className="animate-pulse" />
        </div>
        <h2 className="text-3xl font-bold text-gray-800 mb-2">¡Proceso Terminado!</h2>
        <p className="text-gray-500 max-w-sm mb-8 text-lg">
          {isDirectExecution 
            ? `Se han despachado exitosamente los ${data.archivos_subidos.length} recibos.` 
            : `El lote ha sido encolado y el Supervisor fue notificado para revisar.`}
        </p>
        <button onClick={() => window.location.reload()} className="bg-primary text-white font-semibold py-3 px-8 rounded-lg shadow-md hover:bg-blue-900 transition-all">
          Volver al Inicio
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col space-y-6 animate-in fade-in zoom-in-95 duration-500">
      
      {/* Easter Egg Simulator ROL para la demo */}
      <div className="bg-orange-50 text-orange-800 p-2 text-xs flex gap-2 justify-center rounded mb-2 border border-orange-200">
        <span className="font-bold">MODO DEMO: Alterna rol para ver el botón Mágico</span>
        <select value={mockRol} onChange={(e) => setMockRol(e.target.value)} className="bg-white border rounded">
          <option value="operador_sin_confianza">Operador (Aprobación Requerida)</option>
          <option value="operador_con_confianza">Operador (Modo Confianza Activo)</option>
          <option value="supervisor">Supervisor</option>
        </select>
      </div>

      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-primary flex items-center justify-center gap-2">
          Resumen de la Transacción <Send className="text-secondary ml-2" />
        </h2>
      </div>

      <div className="bg-gray-50 border border-gray-200 p-6 rounded-xl shadow-inner max-w-2xl mx-auto w-full">
        <h4 className="font-semibold text-gray-400 uppercase text-xs tracking-wider mb-4 border-b pb-2">Información del Despacho</h4>
        
        <div className="space-y-4">
          <div className="flex justify-between items-center border-b border-gray-100 pb-3">
            <span className="text-gray-600 font-medium">Grupo Destino:</span>
            <span className="text-primary font-bold text-lg">
              {data.grupo_id === 1 ? 'Planta Guayaquil' : data.grupo_id === 2 ? 'Departamento Ventas' : 'Grupo Central'}
            </span>
          </div>

          <div className="flex justify-between items-center border-b border-gray-100 pb-3">
            <span className="text-gray-600 font-medium">Documentos a procesar:</span>
            <span className="text-primary font-bold">{data.archivos_subidos?.length || 0} PDFs validados</span>
          </div>

          <div className="flex justify-between items-start border-b border-gray-100 pb-3">
            <span className="text-gray-600 font-medium">Asunto Global:</span>
            <span className="text-gray-800 font-mono text-sm max-w-[250px] text-right truncate">"{data.asunto}"</span>
          </div>
        </div>
      </div>

      {/* Progress Bar Interactiva */}
      {ejecutando && (
        <div className="w-full max-w-2xl mx-auto pt-4">
          <div className="flex justify-between text-sm font-semibold mb-2">
            <span className="text-secondary">Procesando envíos...</span>
            <span className="text-primary">{progreso}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3.5 shadow-inner">
            <div 
              className="bg-secondary h-3.5 rounded-full transition-all duration-300 ease-in-out relative flex items-center justify-end"
              style={{ width: `${progreso}%` }}
            >
              {progreso > 5 && <div className="absolute right-1 w-2 h-2 bg-white rounded-full animate-ping opacity-75"></div>}
            </div>
          </div>
        </div>
      )}

      {/* FOOTER ACTIONS */}
      {!ejecutando && (
        <div className="pt-10 flex flex-col items-center border-t border-gray-100 mt-8 gap-6">
          
          {isDirectExecution ? (
            <div className="text-center">
              <p className="text-sm font-bold text-green-700 bg-green-50 rounded-lg px-4 py-2 border border-green-200 mb-4 inline-flex items-center gap-2 shadow-sm">
                <ShieldCheck size={18} /> MODO CONFIANZA ACTIVO (Ejecución Directa)
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
                <MailWarning size={18} /> Tu Supervisor revisará este envío antes de que se ejecute.
              </p>
              <button 
                onClick={handleAction}
                className="w-full sm:w-auto flex items-center justify-center gap-3 bg-primary hover:bg-blue-900 text-white font-bold text-lg py-4 px-12 rounded-xl shadow-[0_4px_14px_0_rgba(26,60,110,0.39)] transition-all hover:-translate-y-1"
              >
                Enviar para Aprobación
              </button>
            </div>
          )}

          <button onClick={onPrev} className="text-gray-400 hover:text-gray-800 font-medium text-sm flex items-center gap-1 transition-colors">
            <ArrowLeft size={16} /> Regresar y editar el correo
          </button>
        </div>
      )}
    </div>
  )
}

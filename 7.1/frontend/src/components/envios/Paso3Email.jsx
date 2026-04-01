import React, { useState, useEffect } from 'react';
import { Mail, ArrowRight, ArrowLeft, Paintbrush } from 'lucide-react';

// Plantillas: cada una tiene su asunto y cuerpo por defecto
const PLANTILLAS = [
  {
    id: 1,
    nombre: "Rol de Pagos (Plantilla RRHH Generica)",
    asunto: "Rol de Pagos de [mes] - NexoData",
    cuerpo: `Estimado(a) [nombre],

Adjunto a este correo encontrara su Rol de Pagos correspondiente al mes de [mes], emitido por el Departamento de Nomina de [empresa].

Por favor, reviselo y conservelo en sus registros.

Si tiene alguna consulta, no dude en contactarnos.

Atentamente,
Departamento de RRHH - [empresa]`
  },
  {
    id: 2,
    nombre: "Comprobante de Decimo Sueldo",
    asunto: "Comprobante de Decimo Sueldo [mes] - NexoData",
    cuerpo: `Estimado(a) [nombre],

Le informamos que se ha acreditado su Decimo Sueldo correspondiente al periodo [mes].

Adjunto encontrara el comprobante oficial de este beneficio de ley.

Para cualquier consulta, puede comunicarse con el Departamento de Recursos Humanos.

Atentamente,
Departamento de RRHH - [empresa]`
  },
  {
    id: 3,
    nombre: "Notificacion de Vacaciones Anuales",
    asunto: "Autorizacion de Vacaciones - [nombre] - [mes]",
    cuerpo: `Estimado(a) [nombre],

Por medio del presente correo, se le notifica que su solicitud de vacaciones anuales ha sido aprobada para el periodo indicado en el documento adjunto.

Le pedimos revisar las fechas y confirmar su recepcion respondiendo este correo.

Buen descanso,
Departamento de RRHH - [empresa]`
  }
];

export default function Paso3Email({ onNext, onPrev, data, updateData }) {
  const [cuerpoEditado, setCuerpoEditado] = useState('');

  // Obtener la plantilla activa
  const plantillaActiva = PLANTILLAS.find(p => p.id === (data.plantilla_id || 1)) || PLANTILLAS[0];

  // Cuando cambia la plantilla, actualizar asunto y cuerpo
  useEffect(() => {
    setCuerpoEditado(plantillaActiva.cuerpo);
    // Solo cambia el asunto automaticamente si el usuario no lo ha editado manualmente
    updateData({
      ...data,
      asunto: plantillaActiva.asunto,
      cuerpo_email: plantillaActiva.cuerpo
    });
  }, [data.plantilla_id]);

  // Sincronizar cuerpo editado con formData
  useEffect(() => {
    if (cuerpoEditado) {
      updateData({ ...data, cuerpo_email: cuerpoEditado });
    }
  }, [cuerpoEditado]);

  // Inicializar cuerpo si no existe
  useEffect(() => {
    if (!cuerpoEditado) {
      setCuerpoEditado(plantillaActiva.cuerpo);
    }
  }, []);

  const handlePlantillaChange = (e) => {
    const nuevoId = parseInt(e.target.value);
    const nuevaPlantilla = PLANTILLAS.find(p => p.id === nuevoId) || PLANTILLAS[0];
    setCuerpoEditado(nuevaPlantilla.cuerpo);
    updateData({
      ...data,
      plantilla_id: nuevoId,
      asunto: nuevaPlantilla.asunto,
      cuerpo_email: nuevaPlantilla.cuerpo
    });
  };

  // Preview con variables reemplazadas
  const previewAsunto = (data.asunto || '')
    .replace('[nombre]', 'Juan Tamayo')
    .replace('[mes]', 'Marzo 2026')
    .replace('[empresa]', 'NexoData');

  const previewCuerpo = cuerpoEditado
    .replace(/\[nombre\]/g, 'Juan Tamayo')
    .replace(/\[mes\]/g, 'Marzo 2026')
    .replace(/\[empresa\]/g, 'NexoData');

  return (
    <div className="flex flex-col space-y-6 animate-in fade-in zoom-in-95 duration-500">

      <div className="text-center mb-2">
        <h2 className="text-xl font-bold text-primary flex items-center justify-center gap-2">
          <Mail className="text-secondary" /> Configura el Correo
        </h2>
        <p className="text-gray-500 mt-2 text-sm">
          Escoge la plantilla y personaliza el mensaje. Usa <span className="font-mono font-bold text-primary">[nombre]</span>, <span className="font-mono font-bold text-primary">[mes]</span> y <span className="font-mono font-bold text-primary">[empresa]</span> como variables.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Controles izquierda */}
        <div className="space-y-5">

          {/* Selector de plantilla */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Plantilla de Diseno HTML</label>
            <div className="relative">
              <select
                value={data.plantilla_id || 1}
                onChange={handlePlantillaChange}
                className="block w-full px-4 py-3 bg-white border border-gray-300 rounded-lg focus:ring-secondary focus:border-secondary outline-none appearance-none font-medium text-gray-700"
              >
                {PLANTILLAS.map(pt => (
                  <option key={pt.id} value={pt.id}>{pt.nombre}</option>
                ))}
              </select>
              <Paintbrush className="absolute right-3 top-3 text-gray-400 pointer-events-none" size={20} />
            </div>
          </div>

          {/* Asunto editable */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Asunto del Correo</label>
            <input
              type="text"
              value={data.asunto || ''}
              onChange={(e) => updateData({ ...data, asunto: e.target.value })}
              className="block w-full px-4 py-3 bg-white border border-gray-300 rounded-lg focus:ring-secondary focus:border-secondary outline-none font-medium transition-colors"
              placeholder="Ej: Su rol de pago de [mes]"
            />
          </div>

          {/* Cuerpo editable */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Cuerpo del Mensaje
              <span className="ml-2 font-normal text-gray-400 text-xs">(editable — cambia con la plantilla)</span>
            </label>
            <textarea
              value={cuerpoEditado}
              onChange={(e) => setCuerpoEditado(e.target.value)}
              rows={9}
              className="block w-full px-4 py-3 bg-white border border-gray-300 rounded-lg focus:ring-secondary focus:border-secondary outline-none font-mono text-sm transition-colors resize-none leading-relaxed"
              placeholder="Escribe el cuerpo del correo..."
            />
            <p className="text-xs text-gray-400 mt-1">
              Variables disponibles: <code className="bg-gray-100 px-1 rounded">[nombre]</code> <code className="bg-gray-100 px-1 rounded">[mes]</code> <code className="bg-gray-100 px-1 rounded">[empresa]</code>
            </p>
          </div>
        </div>

        {/* Preview derecha — diseño cambia con la plantilla */}
        <div className="rounded-xl overflow-hidden border-2 border-gray-200 shadow-sm">

          {/* Header del email simulado — color cambia por plantilla */}
          <div className={`p-5 text-white ${
            (data.plantilla_id || 1) === 1 ? 'bg-gradient-to-r from-blue-700 to-blue-500' :
            (data.plantilla_id || 1) === 2 ? 'bg-gradient-to-r from-emerald-700 to-teal-500' :
            'bg-gradient-to-r from-violet-700 to-purple-500'
          }`}>
            <div className="text-[10px] font-bold uppercase tracking-widest opacity-70 mb-1">
              {(data.plantilla_id || 1) === 1 ? '📄 ROL DE PAGOS' :
               (data.plantilla_id || 1) === 2 ? '💰 DÉCIMO SUELDO' :
               '🏖️ VACACIONES ANUALES'}
            </div>
            <h4 className="font-bold text-sm leading-tight">{previewAsunto}</h4>
            <p className="text-[11px] opacity-70 mt-1">Para: juan.tamayo@empresa.com</p>
          </div>

          {/* Cuerpo simulado */}
          <div className="bg-white p-5">
            <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed font-sans">
              {previewCuerpo}
            </div>

            {/* PDF adjunto simulado */}
            <div className={`mt-5 flex items-center p-3 border rounded-lg ${
              (data.plantilla_id || 1) === 1 ? 'bg-blue-50 border-blue-100' :
              (data.plantilla_id || 1) === 2 ? 'bg-emerald-50 border-emerald-100' :
              'bg-violet-50 border-violet-100'
            }`}>
              <div className={`text-white text-xs font-bold px-2 py-1 rounded inline-block ${
                (data.plantilla_id || 1) === 1 ? 'bg-blue-600' :
                (data.plantilla_id || 1) === 2 ? 'bg-emerald-600' :
                'bg-violet-600'
              }`}>PDF</div>
              <span className="ml-3 text-xs font-mono text-gray-600 truncate flex-1">
                {(data.plantilla_id || 1) === 1 ? '0912345678_rol_marzo_2026.pdf' :
                 (data.plantilla_id || 1) === 2 ? '0912345678_decimo_2026.pdf' :
                 '0912345678_vacaciones_aprobadas.pdf'}
              </span>
            </div>
          </div>

          {/* Pie */}
          <div className={`py-2 px-5 text-center text-[10px] font-medium text-white ${
            (data.plantilla_id || 1) === 1 ? 'bg-blue-700' :
            (data.plantilla_id || 1) === 2 ? 'bg-emerald-700' :
            'bg-violet-700'
          }`}>
            NexoData RRHH · Sistema automático — no responder este correo
          </div>
        </div>

      </div>

      <div className="pt-4 flex justify-between items-center">
        <button onClick={onPrev} className="flex items-center text-gray-500 hover:text-primary font-medium px-4 py-2">
          <ArrowLeft size={18} className="mr-2" /> Atras
        </button>
        <button
          onClick={onNext}
          disabled={!data.asunto?.trim()}
          className="flex items-center gap-2 bg-secondary hover:bg-blue-700 disabled:bg-gray-300 text-white font-semibold py-3 px-8 rounded-lg shadow-md hover:shadow-lg transition-all"
        >
          Confirmar y Enviar <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );
}

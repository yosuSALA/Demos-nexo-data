import React, { useState } from 'react';
import { ChevronRight } from 'lucide-react';
import Paso1Grupo from '../components/envios/Paso1Grupo';
import Paso2Pdfs from '../components/envios/Paso2Pdfs';
import Paso3Email from '../components/envios/Paso3Email';
import Paso4Confirmar from '../components/envios/Paso4Confirmar';

const STEPS = ["Selección Grupo", "Destinatarios", "Configurar Email", "Confirmación"];

export default function NuevoEnvio() {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    grupo_id: null,
    archivos_subidos: [],
    mapeo_resultado: null,
    plantilla_id: 1,
    asunto: 'Rol de Pagos de [mes] - NexoData'
  });

  const nextStep = () => setCurrentStep(prev => Math.min(prev + 1, 4));
  const prevStep = () => setCurrentStep(prev => Math.max(prev - 1, 1));

  function renderStep() {
    switch(currentStep) {
      case 1: return <Paso1Grupo onNext={nextStep} data={formData} updateData={setFormData} />;
      case 2: return <Paso2Pdfs onNext={nextStep} onPrev={prevStep} data={formData} updateData={setFormData} />;
      case 3: return <Paso3Email onNext={nextStep} onPrev={prevStep} data={formData} updateData={setFormData} />;
      case 4: return <Paso4Confirmar onPrev={prevStep} data={formData} />;
      default: return null;
    }
  }

  return (
    <div className="w-full max-w-5xl bg-white shadow-xl shadow-blue-900/5 rounded-xl border border-gray-100 overflow-hidden">
      
      {/* Encabezado Corporativo */}
      <div className="bg-primary text-white p-6 md:px-10">
        <h1 className="text-2xl font-bold tracking-tight">Bot de Envíos Masivos (RRHH)</h1>
        <p className="text-sm font-medium opacity-80 mt-1">Sigue el proceso para despachar la nómina al grupo seleccionado.</p>
      </div>

      {/* Header Wizard Pasos */}
      <div className="bg-gray-50/50 border-b border-gray-200 px-6 py-5 hidden sm:flex items-center justify-between">
        {STEPS.map((step, idx) => {
          const stepNumber = idx + 1;
          const isActive = currentStep === stepNumber;
          const isPassed = currentStep > stepNumber;
          
          return (
            <div key={step} className="flex items-center group">
              <div className={`
                flex items-center justify-center w-9 h-9 rounded-full text-sm font-semibold transition-all duration-300
                ${isPassed ? 'bg-green-600 text-white' : 
                  isActive ? 'bg-secondary text-white ring-4 ring-blue-100' : 
                  'bg-gray-200 text-gray-500'}
              `}>
                {stepNumber}
              </div>
              <span className={`ml-3 text-sm font-semibold tracking-wide ${isActive ? 'text-primary' : isPassed ? 'text-gray-800' : 'text-gray-400'}`}>
                {step}
              </span>
              {idx < STEPS.length - 1 && (
                <ChevronRight className="w-5 h-5 mx-4 md:mx-6 text-gray-300" />
              )}
            </div>
          )
        })}
      </div>

      {/* Contenedor Renderizado Dinámico */}
      <div className="p-6 md:p-10 min-h-[400px]">
        {renderStep()}
      </div>
    </div>
  )
}

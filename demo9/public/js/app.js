// Auto-calculate days between dates for permits
document.addEventListener('DOMContentLoaded', () => {
  const fechaInicio = document.querySelector('input[name="fecha_inicio"]');
  const fechaFin = document.querySelector('input[name="fecha_fin"]');
  const diasInput = document.querySelector('input[name="dias"]');

  if (fechaInicio && fechaFin && diasInput) {
    const calcDias = () => {
      if (fechaInicio.value && fechaFin.value) {
        const d1 = new Date(fechaInicio.value);
        const d2 = new Date(fechaFin.value);
        const diff = Math.ceil((d2 - d1) / (1000 * 60 * 60 * 24)) + 1;
        if (diff > 0) diasInput.value = diff;
      }
    };
    fechaInicio.addEventListener('change', calcDias);
    fechaFin.addEventListener('change', calcDias);
  }
});

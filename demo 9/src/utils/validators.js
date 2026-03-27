/**
 * Validación de cédula ecuatoriana (10 dígitos, algoritmo módulo 10)
 */
function validarCedula(cedula) {
  if (!cedula || cedula.length !== 10 || !/^\d{10}$/.test(cedula)) return false;

  const provincia = parseInt(cedula.substring(0, 2), 10);
  if (provincia < 1 || (provincia > 24 && provincia !== 30)) return false;

  const tercerDigito = parseInt(cedula[2], 10);
  if (tercerDigito > 5) return false;

  const coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2];
  let suma = 0;

  for (let i = 0; i < 9; i++) {
    let valor = parseInt(cedula[i], 10) * coeficientes[i];
    if (valor > 9) valor -= 9;
    suma += valor;
  }

  const digitoVerificador = suma % 10 === 0 ? 0 : 10 - (suma % 10);
  return digitoVerificador === parseInt(cedula[9], 10);
}

/**
 * Formatear número como moneda USD
 */
function formatMoney(num) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(num || 0);
}

/**
 * Calcular días entre dos fechas
 */
function diasEntre(fecha1, fecha2) {
  const d1 = new Date(fecha1);
  const d2 = new Date(fecha2);
  const diff = Math.abs(d2 - d1);
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

/**
 * Calcular años de servicio
 */
function aniosServicio(fechaIngreso, fechaRef = new Date()) {
  const ingreso = new Date(fechaIngreso);
  const ref = new Date(fechaRef);
  let anios = ref.getFullYear() - ingreso.getFullYear();
  const m = ref.getMonth() - ingreso.getMonth();
  if (m < 0 || (m === 0 && ref.getDate() < ingreso.getDate())) {
    anios--;
  }
  return Math.max(0, anios);
}

/**
 * Calcular meses de servicio
 */
function mesesServicio(fechaIngreso, fechaRef = new Date()) {
  const ingreso = new Date(fechaIngreso);
  const ref = new Date(fechaRef);
  return (
    (ref.getFullYear() - ingreso.getFullYear()) * 12 +
    (ref.getMonth() - ingreso.getMonth())
  );
}

module.exports = {
  validarCedula,
  formatMoney,
  diasEntre,
  aniosServicio,
  mesesServicio,
};

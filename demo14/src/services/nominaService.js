const db = require('../config/database');
const { getConfig, getTablaIR, esFeriado } = require('./configService');
const { mesesServicio } = require('../utils/validators');

// =============================================
// CÁLCULO DE HORAS EXTRAS
// =============================================
function calcularValorHoraExtra(sueldoBase, horas, tipo) {
  const valorHora = sueldoBase / 240; // 30 días * 8 horas
  const recargo =
    tipo === 'suplementaria'
      ? getConfig('hora_suplementaria_recargo') / 100
      : getConfig('hora_extraordinaria_recargo') / 100;
  return horas * valorHora * (1 + recargo);
}

// =============================================
// CÁLCULO DE ATRASO / MULTA
// =============================================
function calcularMultaAtraso(sueldoBase, minutosAtraso) {
  const valorMinuto = sueldoBase / 240 / 60;
  return minutosAtraso * valorMinuto;
}

// =============================================
// CÁLCULO IESS
// =============================================
function calcularAportePersonal(totalIngresos) {
  const pct = getConfig('aporte_personal_pct') / 100;
  return Math.round(totalIngresos * pct * 100) / 100;
}

function calcularAportePatronal(totalIngresos) {
  const pct = getConfig('aporte_patronal_pct') / 100;
  return Math.round(totalIngresos * pct * 100) / 100;
}

// =============================================
// CÁLCULO IMPUESTO A LA RENTA
// =============================================
function calcularRetencionIR(ingresoMensualGravable, gastosPersonalesAnuales = 0, anio = 2026) {
  const ingresoAnualProyectado = ingresoMensualGravable * 12;
  const aporteIESSAnual = calcularAportePersonal(ingresoMensualGravable) * 12;

  let baseImponible = ingresoAnualProyectado - aporteIESSAnual - gastosPersonalesAnuales;
  if (baseImponible <= 0) return 0;

  const tabla = getTablaIR(anio);
  let impuestoAnual = 0;

  for (const tramo of tabla) {
    if (baseImponible >= tramo.fraccion_basica && baseImponible <= tramo.exceso_hasta) {
      impuestoAnual =
        tramo.impuesto_fraccion +
        ((baseImponible - tramo.fraccion_basica) * tramo.porcentaje_excedente) / 100;
      break;
    }
  }

  return Math.round((impuestoAnual / 12) * 100) / 100;
}

// =============================================
// PROVISIONES
// =============================================
function calcularFondosReserva(sueldoBase, fechaIngreso) {
  const meses = mesesServicio(fechaIngreso);
  if (meses < 13) return 0;
  const pct = getConfig('fondos_reserva_pct') / 100;
  return Math.round(sueldoBase * pct * 100) / 100;
}

function calcularProvDecTercero(totalIngresos) {
  return Math.round((totalIngresos / 12) * 100) / 100;
}

function calcularProvDecCuarto() {
  const sbu = getConfig('sbu');
  return Math.round((sbu / 12) * 100) / 100;
}

function calcularProvVacaciones(sueldoBase) {
  return Math.round(((sueldoBase * 15) / 360) * 100) / 100;
}

// =============================================
// GENERAR ROL DE PAGO
// =============================================
function generarRolPago(empleadoId, mes, anio) {
  const empleado = db
    .prepare('SELECT * FROM empleados WHERE id = ? AND activo = 1')
    .get(empleadoId);
  if (!empleado) throw new Error('Empleado no encontrado o inactivo');

  // Obtener asistencia del mes
  const mesStr = String(mes).padStart(2, '0');
  const asistencia = db
    .prepare(
      "SELECT * FROM asistencia WHERE empleado_id = ? AND strftime('%Y', fecha) = ? AND strftime('%m', fecha) = ?"
    )
    .all(empleadoId, String(anio), mesStr);

  let totalHorasSupl = 0;
  let totalHorasExtr = 0;
  let totalAtrasoMin = 0;

  for (const reg of asistencia) {
    totalHorasSupl += reg.horas_suplementarias || 0;
    totalHorasExtr += reg.horas_extraordinarias || 0;
    totalAtrasoMin += reg.atraso_minutos || 0;
  }

  const horasSupVal = calcularValorHoraExtra(empleado.sueldo_base, totalHorasSupl, 'suplementaria');
  const horasExtVal = calcularValorHoraExtra(empleado.sueldo_base, totalHorasExtr, 'extraordinaria');

  // Buscar comisiones/bonos si hay rol borrador
  const rolExistente = db
    .prepare(
      'SELECT * FROM roles_pago WHERE empleado_id = ? AND mes = ? AND anio = ? AND estado = ?'
    )
    .get(empleadoId, mes, anio, 'Borrador');

  const comisiones = rolExistente ? rolExistente.comisiones : 0;
  const bonos = rolExistente ? rolExistente.bonos : 0;
  const otrosIngresos = rolExistente ? rolExistente.otros_ingresos : 0;

  // Ingresos
  const totalIngresos =
    empleado.sueldo_base + horasSupVal + horasExtVal + comisiones + bonos + otrosIngresos;

  // Deducciones
  const aporteIESS = calcularAportePersonal(totalIngresos);
  const retencionIR = calcularRetencionIR(totalIngresos);
  const multas = calcularMultaAtraso(empleado.sueldo_base, totalAtrasoMin);

  // Préstamos activos
  const prestamos = db
    .prepare(
      'SELECT * FROM prestamos WHERE empleado_id = ? AND activo = 1'
    )
    .all(empleadoId);

  let prestamoQuiro = 0;
  let prestamoHipo = 0;
  for (const p of prestamos) {
    if (p.tipo === 'Quirografario') prestamoQuiro = p.cuota_mensual;
    if (p.tipo === 'Hipotecario') prestamoHipo = p.cuota_mensual;
  }

  // Anticipos y pensiones del rol existente
  const anticipo = rolExistente ? rolExistente.anticipo_sueldo : 0;
  const pension = rolExistente ? rolExistente.pension_alimenticia : 0;
  const otrasDed = rolExistente ? rolExistente.otras_deducciones : 0;

  const totalDeducciones =
    aporteIESS + retencionIR + multas + prestamoQuiro + prestamoHipo + anticipo + pension + otrasDed;

  const netoRecibir = Math.round((totalIngresos - totalDeducciones) * 100) / 100;

  // Provisiones
  const aportePatronal = calcularAportePatronal(totalIngresos);
  const fondosReserva = calcularFondosReserva(totalIngresos, empleado.fecha_ingreso);
  const provDecTercero = calcularProvDecTercero(totalIngresos);
  const provDecCuarto = calcularProvDecCuarto();
  const provVacaciones = calcularProvVacaciones(empleado.sueldo_base);

  const periodo = `${anio}-${mesStr}`;

  const rol = {
    empleado_id: empleadoId,
    periodo,
    mes,
    anio,
    tipo: 'Mensual',
    sueldo_base: empleado.sueldo_base,
    horas_suplementarias_valor: Math.round(horasSupVal * 100) / 100,
    horas_extraordinarias_valor: Math.round(horasExtVal * 100) / 100,
    comisiones,
    bonos,
    otros_ingresos: otrosIngresos,
    total_ingresos: Math.round(totalIngresos * 100) / 100,
    aporte_iess: aporteIESS,
    prestamo_quirografario: prestamoQuiro,
    prestamo_hipotecario: prestamoHipo,
    anticipo_sueldo: anticipo,
    pension_alimenticia: pension,
    retencion_ir: retencionIR,
    multas: Math.round(multas * 100) / 100,
    otras_deducciones: otrasDed,
    total_deducciones: Math.round(totalDeducciones * 100) / 100,
    neto_a_recibir: netoRecibir,
    aporte_patronal: aportePatronal,
    decimo_tercero_prov: provDecTercero,
    decimo_cuarto_prov: provDecCuarto,
    fondos_reserva_prov: fondosReserva,
    vacaciones_prov: provVacaciones,
    estado: 'Calculado',
  };

  // Insertar o actualizar
  if (rolExistente) {
    const setClauses = Object.keys(rol)
      .filter((k) => k !== 'empleado_id')
      .map((k) => `${k} = @${k}`)
      .join(', ');
    db.prepare(`UPDATE roles_pago SET ${setClauses} WHERE id = @id`).run({
      ...rol,
      id: rolExistente.id,
    });
    return { ...rol, id: rolExistente.id };
  } else {
    const cols = Object.keys(rol).join(', ');
    const vals = Object.keys(rol)
      .map((k) => `@${k}`)
      .join(', ');
    const result = db
      .prepare(`INSERT INTO roles_pago (${cols}) VALUES (${vals})`)
      .run(rol);
    return { ...rol, id: result.lastInsertRowid };
  }
}

// =============================================
// GENERAR NÓMINA COMPLETA DEL MES
// =============================================
function generarNominaMensual(mes, anio) {
  const empleados = db
    .prepare('SELECT id FROM empleados WHERE activo = 1')
    .all();

  const roles = [];
  for (const emp of empleados) {
    try {
      const rol = generarRolPago(emp.id, mes, anio);
      roles.push(rol);
    } catch (err) {
      roles.push({ empleado_id: emp.id, error: err.message });
    }
  }
  return roles;
}

module.exports = {
  calcularValorHoraExtra,
  calcularMultaAtraso,
  calcularAportePersonal,
  calcularAportePatronal,
  calcularRetencionIR,
  calcularFondosReserva,
  calcularProvDecTercero,
  calcularProvDecCuarto,
  calcularProvVacaciones,
  generarRolPago,
  generarNominaMensual,
};

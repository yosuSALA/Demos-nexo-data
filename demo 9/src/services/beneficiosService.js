const db = require('../config/database');
const { getConfig } = require('./configService');
const { aniosServicio, diasEntre } = require('../utils/validators');

// =============================================
// DÉCIMO TERCER SUELDO
// Período: 1 dic año anterior - 30 nov año actual
// =============================================
function calcularDecimoTercero(empleadoId, anio) {
  const empleado = db.prepare('SELECT * FROM empleados WHERE id = ?').get(empleadoId);
  if (!empleado) throw new Error('Empleado no encontrado');

  // Total percibido en el período
  const roles = db
    .prepare(
      `SELECT SUM(total_ingresos) as total FROM roles_pago
       WHERE empleado_id = ? AND estado != 'Borrador'
       AND ((anio = ? AND mes = 12) OR (anio = ? AND mes BETWEEN 1 AND 11))`
    )
    .get(empleadoId, anio - 1, anio);

  const totalPercibido = roles ? roles.total || 0 : 0;

  // Proporcional si no trabajó el período completo
  const fechaInicio = new Date(`${anio - 1}-12-01`);
  const fechaFin = new Date(`${anio}-11-30`);
  const fechaIngreso = new Date(empleado.fecha_ingreso);

  let diasTrabajados = 360; // año comercial
  if (fechaIngreso > fechaInicio) {
    diasTrabajados = diasEntre(fechaIngreso, fechaFin);
    if (diasTrabajados > 360) diasTrabajados = 360;
  }

  const decimoTercero = totalPercibido / 12;

  return {
    empleado_id: empleadoId,
    empleado: `${empleado.apellidos} ${empleado.nombres}`,
    periodo: `Dic ${anio - 1} - Nov ${anio}`,
    total_percibido: Math.round(totalPercibido * 100) / 100,
    dias_trabajados: diasTrabajados,
    valor: Math.round(decimoTercero * 100) / 100,
  };
}

// =============================================
// DÉCIMO CUARTO SUELDO
// Costa: Mar año anterior - Feb año actual
// Sierra: Ago año anterior - Jul año actual
// =============================================
function calcularDecimoCuarto(empleadoId, anio) {
  const empleado = db.prepare('SELECT * FROM empleados WHERE id = ?').get(empleadoId);
  if (!empleado) throw new Error('Empleado no encontrado');

  const sbu = getConfig('sbu', anio);
  const esCosta = empleado.region === 'Costa/Galápagos';

  let fechaInicio, fechaFin;
  if (esCosta) {
    fechaInicio = new Date(`${anio - 1}-03-01`);
    fechaFin = new Date(`${anio}-02-28`);
  } else {
    fechaInicio = new Date(`${anio - 1}-08-01`);
    fechaFin = new Date(`${anio}-07-31`);
  }

  const fechaIngreso = new Date(empleado.fecha_ingreso);
  let diasTrabajados = 360;
  if (fechaIngreso > fechaInicio) {
    diasTrabajados = diasEntre(fechaIngreso, fechaFin);
    if (diasTrabajados > 360) diasTrabajados = 360;
  }

  const valor = (sbu * diasTrabajados) / 360;

  return {
    empleado_id: empleadoId,
    empleado: `${empleado.apellidos} ${empleado.nombres}`,
    region: empleado.region,
    periodo: esCosta
      ? `Mar ${anio - 1} - Feb ${anio}`
      : `Ago ${anio - 1} - Jul ${anio}`,
    sbu,
    dias_trabajados: diasTrabajados,
    valor: Math.round(valor * 100) / 100,
  };
}

// =============================================
// VACACIONES
// 15 días base + 1 día extra desde el 5to año (máx 15 adicionales)
// =============================================
function calcularVacaciones(empleadoId) {
  const empleado = db.prepare('SELECT * FROM empleados WHERE id = ?').get(empleadoId);
  if (!empleado) throw new Error('Empleado no encontrado');

  const anios = aniosServicio(empleado.fecha_ingreso);
  const diasBase = getConfig('vacaciones_dias_base');
  const anioExtra = getConfig('vacaciones_dia_extra_desde_anio');

  let diasAdicionales = 0;
  if (anios >= anioExtra) {
    diasAdicionales = Math.min(anios - anioExtra + 1, 15);
  }

  const diasTotales = diasBase + diasAdicionales;

  // Días de vacaciones ya tomadas en el último año
  const haceUnAnio = new Date();
  haceUnAnio.setFullYear(haceUnAnio.getFullYear() - 1);

  const tomadas = db
    .prepare(
      `SELECT COALESCE(SUM(dias), 0) as total FROM permisos
       WHERE empleado_id = ? AND tipo = 'Vacaciones' AND estado = 'Aprobado'
       AND fecha_inicio >= ?`
    )
    .get(empleadoId, haceUnAnio.toISOString().split('T')[0]);

  const diasDisponibles = diasTotales - (tomadas ? tomadas.total : 0);
  const valorDiario = empleado.sueldo_base / 30;

  return {
    empleado_id: empleadoId,
    empleado: `${empleado.apellidos} ${empleado.nombres}`,
    anios_servicio: anios,
    dias_derecho: diasTotales,
    dias_tomados: tomadas ? tomadas.total : 0,
    dias_disponibles: Math.max(0, diasDisponibles),
    valor_diario: Math.round(valorDiario * 100) / 100,
    valor_total: Math.round(diasDisponibles * valorDiario * 100) / 100,
  };
}

// =============================================
// UTILIDADES (15%)
// 10% equitativo por días trabajados
// 5% proporcional a cargas familiares
// =============================================
function calcularUtilidades(utilidadLiquida, anio) {
  const total15 = utilidadLiquida * 0.15;
  const total10 = utilidadLiquida * 0.10;
  const total5 = utilidadLiquida * 0.05;

  const empleados = db
    .prepare(
      `SELECT e.id, e.apellidos, e.nombres, e.fecha_ingreso, e.cargas_familiares,
              e.fecha_salida
       FROM empleados e
       WHERE e.fecha_ingreso <= ? AND (e.fecha_salida IS NULL OR e.fecha_salida >= ?)`
    )
    .all(`${anio}-12-31`, `${anio}-01-01`);

  // Calcular días trabajados en el año para cada empleado
  let totalDiasTodos = 0;
  let totalCargasDias = 0;
  const detalles = [];

  for (const emp of empleados) {
    const inicio = new Date(
      Math.max(new Date(emp.fecha_ingreso), new Date(`${anio}-01-01`))
    );
    const fin = emp.fecha_salida
      ? new Date(Math.min(new Date(emp.fecha_salida), new Date(`${anio}-12-31`)))
      : new Date(`${anio}-12-31`);

    const dias = Math.min(360, Math.max(0, diasEntre(inicio, fin)));
    totalDiasTodos += dias;
    totalCargasDias += (emp.cargas_familiares || 0) * dias;

    detalles.push({
      empleado_id: emp.id,
      empleado: `${emp.apellidos} ${emp.nombres}`,
      dias_trabajados: dias,
      cargas_familiares: emp.cargas_familiares || 0,
    });
  }

  // Distribuir
  for (const det of detalles) {
    det.valor_10 =
      totalDiasTodos > 0
        ? Math.round(((total10 * det.dias_trabajados) / totalDiasTodos) * 100) / 100
        : 0;
    det.valor_5 =
      totalCargasDias > 0
        ? Math.round(
            ((total5 * det.cargas_familiares * det.dias_trabajados) / totalCargasDias) * 100
          ) / 100
        : 0;
    det.total = Math.round((det.valor_10 + det.valor_5) * 100) / 100;
  }

  // Guardar en BD
  const insertUtilidad = db.prepare(
    `INSERT INTO utilidades (anio, utilidad_liquida, total_15_porciento, total_10_porciento, total_5_porciento)
     VALUES (?, ?, ?, ?, ?)`
  );
  const result = insertUtilidad.run(anio, utilidadLiquida, total15, total10, total5);
  const utilidadId = result.lastInsertRowid;

  const insertDetalle = db.prepare(
    `INSERT INTO utilidades_detalle (utilidad_id, empleado_id, dias_trabajados, cargas_familiares, valor_10, valor_5, total)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  );

  const insertAll = db.transaction((items) => {
    for (const d of items) {
      insertDetalle.run(utilidadId, d.empleado_id, d.dias_trabajados, d.cargas_familiares, d.valor_10, d.valor_5, d.total);
    }
  });
  insertAll(detalles);

  return {
    utilidad_id: utilidadId,
    anio,
    utilidad_liquida: utilidadLiquida,
    total_15: Math.round(total15 * 100) / 100,
    total_10: Math.round(total10 * 100) / 100,
    total_5: Math.round(total5 * 100) / 100,
    detalles,
  };
}

module.exports = {
  calcularDecimoTercero,
  calcularDecimoCuarto,
  calcularVacaciones,
  calcularUtilidades,
};

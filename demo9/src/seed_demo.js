/**
 * seed_demo.js — Datos de demostración para Nexo Data · Sistema de Nómina
 * Ejecutar: node src/seed_demo.js
 *
 * Agrega: 12 empleados, 3 meses de roles de pago (Ene-Mar 2026),
 *         registros de asistencia Marzo 2026 y permisos de ejemplo.
 */

'use strict';

const db = require('./config/database');
const { initializeDatabase } = require('./models/schema');

initializeDatabase();

// ─── Constantes 2026 ────────────────────────────────────────────────────────
const APORTE_PERSONAL = 0.0945;
const APORTE_PATRONAL = 0.1115;
const D13_PCT = 1 / 12;
const D14_BASE = 470.00;
const FONDOS_RESERVA = 0.0833;
const VACACIONES_PCT = 1 / 24;

// ─── Empleados ───────────────────────────────────────────────────────────────
const empleados = [
  ['1712345678', 'García López',     'María José',     '1990-05-15', '2022-01-15', 'Analista de Sistemas',      'Tecnología',     1200.00, 'Indefinido',  'Sierra/Amazonía',   2, '2200012345', 'Banco Pichincha',    'Ahorros',   'maria.garcia@nexodata.ec'],
  ['0912345678', 'Pérez Morales',    'Carlos Andrés',  '1988-11-20', '2024-06-01', 'Contador General',          'Finanzas',       1800.00, 'Indefinido',  'Costa/Galápagos',   1, '3300067890', 'Banco del Pacífico', 'Corriente', 'carlos.perez@nexodata.ec'],
  ['1812345678', 'Rodríguez Silva',  'Ana Lucía',      '1995-03-08', '2025-03-01', 'Asistente Administrativa',  'Administración',  550.00, 'Plazo Fijo',  'Sierra/Amazonía',   0, '1100098765', 'Banco de Guayaquil', 'Ahorros',   'ana.rodriguez@nexodata.ec'],
  ['0912876543', 'Vásquez Torres',   'Diego Sebastián','1992-07-22', '2021-09-01', 'Desarrollador Full Stack',  'Tecnología',     1500.00, 'Indefinido',  'Costa/Galápagos',   0, '2200054321', 'Banco Pichincha',    'Ahorros',   'diego.vasquez@nexodata.ec'],
  ['1756789012', 'Moreno Jiménez',   'Patricia Elena', '1985-01-30', '2020-03-15', 'Gerente de Proyectos',      'Operaciones',    2500.00, 'Indefinido',  'Sierra/Amazonía',   3, '3300011223', 'Banco del Pacífico', 'Corriente', 'patricia.moreno@nexodata.ec'],
  ['0987654321', 'Castro Herrera',   'Luis Felipe',    '1997-09-12', '2025-01-10', 'Soporte Técnico',           'Tecnología',      700.00, 'Plazo Fijo',  'Costa/Galápagos',   0, '1100055678', 'Banco de Guayaquil', 'Ahorros',   'luis.castro@nexodata.ec'],
  ['1734567890', 'Espinoza Rueda',   'Gabriela Andrea','1993-04-18', '2023-07-01', 'Diseñadora UX/UI',          'Tecnología',     1100.00, 'Indefinido',  'Sierra/Amazonía',   1, '2200077890', 'Banco Pichincha',    'Ahorros',   'gabriela.espinoza@nexodata.ec'],
  ['0956781234', 'Mendoza Alvarado', 'Roberto Carlos', '1980-12-05', '2019-05-20', 'Director Comercial',        'Ventas',         3200.00, 'Indefinido',  'Costa/Galápagos',   2, '3300099887', 'Banco del Pacífico', 'Corriente', 'roberto.mendoza@nexodata.ec'],
  ['1798765432', 'Sánchez Ponce',    'Valeria Mishell','1999-06-14', '2025-08-01', 'Pasante Marketing',         'Marketing',       470.00, 'Pasantía',    'Sierra/Amazonía',   0, '1100033445', 'Banco de Guayaquil', 'Ahorros',   'valeria.sanchez@nexodata.ec'],
  ['0923456789', 'Guerrero Lema',    'Andrés Patricio','1986-02-28', '2018-11-01', 'Jefe de Recursos Humanos',  'RRHH',           2100.00, 'Indefinido',  'Costa/Galápagos',   1, '2200033456', 'Banco Pichincha',    'Corriente', 'andres.guerrero@nexodata.ec'],
  ['1745678901', 'Delgado Naranjo',  'Sofía Paola',    '1994-08-07', '2023-02-14', 'Analista Financiera',       'Finanzas',       1350.00, 'Indefinido',  'Sierra/Amazonía',   0, '3300022334', 'Banco del Pacífico', 'Ahorros',   'sofia.delgado@nexodata.ec'],
  ['0934567890', 'Cevallos Intriago','Miguel Ángel',   '1991-10-19', '2022-06-01', 'Especialista en Datos',     'Tecnología',     1650.00, 'Indefinido',  'Costa/Galápagos',   2, '1100077654', 'Banco de Guayaquil', 'Ahorros',   'miguel.cevallos@nexodata.ec'],
];

const insertEmpleado = db.prepare(`
  INSERT OR IGNORE INTO empleados
    (cedula, apellidos, nombres, fecha_nacimiento, fecha_ingreso, cargo, departamento,
     sueldo_base, tipo_contrato, region, cargas_familiares, cuenta_bancaria, banco,
     tipo_cuenta, email)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

db.transaction(() => {
  for (const e of empleados) insertEmpleado.run(...e);
})();

// Obtener IDs tras inserción
const empRows = db.prepare('SELECT id, cedula, sueldo_base FROM empleados ORDER BY id').all();

// ─── Helper: calcular rol mensual ────────────────────────────────────────────
function calcularRol(empId, sueldo, mes, anio, extras = {}) {
  const { hrsSupl = 0, hrsExtra = 0, comisiones = 0, bonos = 0 } = extras;

  const valorHora = sueldo / 240;
  const hrsSuplValor  = +(hrsSupl  * valorHora * 1.5).toFixed(2);
  const hrsExtraValor = +(hrsExtra * valorHora * 2.0).toFixed(2);

  const totalIngresos = +(sueldo + hrsSuplValor + hrsExtraValor + comisiones + bonos).toFixed(2);
  const aporteIess    = +(totalIngresos * APORTE_PERSONAL).toFixed(2);
  const neto          = +(totalIngresos - aporteIess).toFixed(2);

  const patronal      = +(sueldo * APORTE_PATRONAL).toFixed(2);
  const d13Prov       = +(sueldo * D13_PCT).toFixed(2);
  const d14Prov       = +(D14_BASE / 12).toFixed(2);
  const frProv        = +(sueldo * FONDOS_RESERVA).toFixed(2);
  const vacProv       = +(sueldo * VACACIONES_PCT).toFixed(2);

  const periodo = `${String(mes).padStart(2,'0')}/${anio}`;

  return {
    empleado_id: empId, periodo, mes, anio,
    tipo: 'Mensual',
    sueldo_base: sueldo,
    horas_suplementarias_valor: hrsSuplValor,
    horas_extraordinarias_valor: hrsExtraValor,
    comisiones, bonos,
    otros_ingresos: 0,
    total_ingresos: totalIngresos,
    aporte_iess: aporteIess,
    prestamo_quirografario: 0,
    prestamo_hipotecario: 0,
    anticipo_sueldo: 0,
    pension_alimenticia: 0,
    retencion_ir: 0,
    multas: 0,
    otras_deducciones: 0,
    total_deducciones: aporteIess,
    neto_a_recibir: neto,
    aporte_patronal: patronal,
    decimo_tercero_prov: d13Prov,
    decimo_cuarto_prov: d14Prov,
    fondos_reserva_prov: frProv,
    vacaciones_prov: vacProv,
    estado: mes < 4 ? 'Pagado' : 'Borrador',
  };
}

// ─── Roles de pago: Enero, Febrero, Marzo 2026 ──────────────────────────────
const insertRol = db.prepare(`
  INSERT OR IGNORE INTO roles_pago
    (empleado_id, periodo, mes, anio, tipo,
     sueldo_base, horas_suplementarias_valor, horas_extraordinarias_valor,
     comisiones, bonos, otros_ingresos, total_ingresos,
     aporte_iess, prestamo_quirografario, prestamo_hipotecario,
     anticipo_sueldo, pension_alimenticia, retencion_ir, multas,
     otras_deducciones, total_deducciones, neto_a_recibir,
     aporte_patronal, decimo_tercero_prov, decimo_cuarto_prov,
     fondos_reserva_prov, vacaciones_prov, estado)
  VALUES
    (@empleado_id, @periodo, @mes, @anio, @tipo,
     @sueldo_base, @horas_suplementarias_valor, @horas_extraordinarias_valor,
     @comisiones, @bonos, @otros_ingresos, @total_ingresos,
     @aporte_iess, @prestamo_quirografario, @prestamo_hipotecario,
     @anticipo_sueldo, @pension_alimenticia, @retencion_ir, @multas,
     @otras_deducciones, @total_deducciones, @neto_a_recibir,
     @aporte_patronal, @decimo_tercero_prov, @decimo_cuarto_prov,
     @fondos_reserva_prov, @vacaciones_prov, @estado)
`);

// Extras variados por empleado para que no sean monótonos
const extrasMap = {
  0: { 2: { hrsSupl: 4 }, 3: { comisiones: 80 } },
  3: { 1: { hrsSupl: 8, bonos: 100 }, 3: { hrsExtra: 2 } },
  7: { 1: { comisiones: 500 }, 2: { comisiones: 320 }, 3: { comisiones: 450, bonos: 200 } },
  9: { 3: { bonos: 150 } },
};

db.transaction(() => {
  for (const [idx, emp] of empRows.entries()) {
    for (const mes of [1, 2, 3]) {
      const extras = (extrasMap[idx] || {})[mes] || {};
      const rol = calcularRol(emp.id, emp.sueldo_base, mes, 2026, extras);
      insertRol.run(rol);
    }
  }
})();

// ─── Asistencia: días hábiles de Marzo 2026 ──────────────────────────────────
// Días hábiles (lun-vie, sin feriados): 1-6, 9-13, 16-20, 23-27, 30-31
const diasHabilesMar = [
  '2026-03-02','2026-03-03','2026-03-04','2026-03-05','2026-03-06',
  '2026-03-09','2026-03-10','2026-03-11','2026-03-12','2026-03-13',
  '2026-03-16','2026-03-17','2026-03-18','2026-03-19','2026-03-20',
  '2026-03-23','2026-03-24','2026-03-25','2026-03-26','2026-03-27',
  '2026-03-30','2026-03-31',
];

const insertAsist = db.prepare(`
  INSERT OR IGNORE INTO asistencia
    (empleado_id, fecha, hora_entrada, hora_salida, horas_normales,
     horas_suplementarias, atraso_minutos, observacion)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
`);

// Simulación realista: algún atraso, alguna hora extra ocasional
function generarAsistencia(empIdx, empId) {
  const registros = [];
  for (const fecha of diasHabilesMar) {
    const rnd = Math.random();
    let entrada = '08:00', salida = '17:00', hNorm = 8, hSupl = 0, atraso = 0, obs = null;

    if (rnd < 0.05) {
      // Falta justificada (skip)
      continue;
    } else if (rnd < 0.12) {
      atraso = Math.floor(Math.random() * 20) + 5;
      entrada = `08:${String(atraso).padStart(2,'0')}`;
      obs = 'Llegada tarde';
    } else if (rnd < 0.18) {
      hSupl = 2;
      salida = '19:00';
      obs = 'Horas suplementarias';
    }

    registros.push([empId, fecha, entrada, salida, hNorm, hSupl, atraso, obs]);
  }
  return registros;
}

db.transaction(() => {
  for (const [idx, emp] of empRows.entries()) {
    const rows = generarAsistencia(idx, emp.id);
    for (const r of rows) insertAsist.run(...r);
  }
})();

// ─── Permisos de ejemplo ─────────────────────────────────────────────────────
const insertPermiso = db.prepare(`
  INSERT OR IGNORE INTO permisos
    (empleado_id, tipo, fecha_inicio, fecha_fin, dias, justificado, estado, observacion)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
`);

const permisos = [
  // [emp_idx, tipo, inicio, fin, dias, justificado, estado, obs]
  [0, 'Vacaciones',    '2026-02-02', '2026-02-06', 5,   1, 'Aprobado',  'Vacaciones anuales'],
  [2, 'Permiso Médico','2026-01-14', '2026-01-14', 0.5, 1, 'Aprobado',  'Consulta médica'],
  [4, 'Vacaciones',    '2026-03-16', '2026-03-20', 5,   1, 'Aprobado',  'Vacaciones planificadas'],
  [3, 'Calamidad',     '2026-02-19', '2026-02-19', 1,   1, 'Aprobado',  'Fallecimiento familiar'],
  [7, 'Comisión',      '2026-03-09', '2026-03-11', 3,   1, 'Aprobado',  'Visita a cliente Quito'],
  [9, 'Permiso Médico','2026-03-25', '2026-03-26', 2,   1, 'Pendiente', 'Cirugía programada'],
  [5, 'Permiso Personal','2026-02-27','2026-02-27',1,   0, 'Rechazado', 'Sin justificación'],
  [10,'Maternidad',    '2026-04-01', '2026-07-11', 70,  1, 'Aprobado',  'Licencia por maternidad'],
];

db.transaction(() => {
  for (const [idx, ...rest] of permisos) {
    if (idx < empRows.length) {
      insertPermiso.run(empRows[idx].id, ...rest);
    }
  }
})();

// ─── Préstamos de ejemplo ─────────────────────────────────────────────────────
const insertPrestamo = db.prepare(`
  INSERT OR IGNORE INTO prestamos
    (empleado_id, tipo, monto_total, cuota_mensual, saldo, fecha_inicio, activo)
  VALUES (?, ?, ?, ?, ?, ?, ?)
`);

const prestamos = [
  [0, 'Quirografario', 2000, 166.67, 1833.33, '2026-01-15', 1],
  [3, 'Quirografario', 1500, 125.00, 1375.00, '2025-11-01', 1],
  [7, 'Hipotecario',  15000, 312.50, 14687.50,'2025-06-01', 1],
  [9, 'Quirografario', 3000, 250.00, 2750.00, '2026-02-01', 1],
];

db.transaction(() => {
  for (const [idx, ...rest] of prestamos) {
    if (idx < empRows.length) {
      insertPrestamo.run(empRows[idx].id, ...rest);
    }
  }
})();

// ─── Resumen ─────────────────────────────────────────────────────────────────
const totales = {
  empleados:  db.prepare('SELECT COUNT(*) as n FROM empleados').get().n,
  roles:      db.prepare('SELECT COUNT(*) as n FROM roles_pago').get().n,
  asistencia: db.prepare('SELECT COUNT(*) as n FROM asistencia').get().n,
  permisos:   db.prepare('SELECT COUNT(*) as n FROM permisos').get().n,
  prestamos:  db.prepare('SELECT COUNT(*) as n FROM prestamos').get().n,
};

console.log('✅ Datos de demo cargados:');
console.log(`   Empleados:  ${totales.empleados}`);
console.log(`   Roles pago: ${totales.roles}`);
console.log(`   Asistencia: ${totales.asistencia} registros`);
console.log(`   Permisos:   ${totales.permisos}`);
console.log(`   Préstamos:  ${totales.prestamos}`);
process.exit(0);

const db = require('./config/database');
const { initializeDatabase } = require('./models/schema');

initializeDatabase();

// =============================================
// CONFIGURACIÓN PARAMETRIZABLE 2026
// =============================================
const configs = [
  ['sbu', '470.00', 'Salario Básico Unificado', 2026],
  ['aporte_personal_pct', '9.45', 'Aporte personal IESS (%)', 2026],
  ['aporte_patronal_pct', '11.15', 'Aporte patronal IESS (%)', 2026],
  ['fondos_reserva_pct', '8.33', 'Fondos de reserva (%)', 2026],
  ['decimo_tercero_pct', '8.33', 'Provisión décimo tercero (%)', 2026],
  ['decimo_cuarto_pct', '8.33', 'Provisión décimo cuarto (%)', 2026],
  ['vacaciones_pct', '4.17', 'Provisión vacaciones (%)', 2026],
  ['hora_suplementaria_recargo', '50', 'Recargo horas suplementarias (%)', 2026],
  ['hora_extraordinaria_recargo', '100', 'Recargo horas extraordinarias (%)', 2026],
  ['jornada_horas', '8', 'Horas jornada laboral diaria', 2026],
  ['jornada_semanal', '40', 'Horas jornada laboral semanal', 2026],
  ['vacaciones_dias_base', '15', 'Días base de vacaciones anuales', 2026],
  ['vacaciones_dia_extra_desde_anio', '5', 'Año desde el que se suma 1 día adicional', 2026],
  ['d14_periodo_costa', 'marzo', 'Mes de pago décimo cuarto Costa/Galápagos', 2026],
  ['d14_periodo_sierra', 'agosto', 'Mes de pago décimo cuarto Sierra/Amazonía', 2026],
  ['utilidades_pct', '15', 'Porcentaje de utilidades para empleados', 2026],
  ['gastos_personales_max', '18800.00', 'Máximo gastos personales deducibles IR', 2026],
];

const insertConfig = db.prepare(
  'INSERT OR REPLACE INTO configuracion (clave, valor, descripcion, anio) VALUES (?, ?, ?, ?)'
);

const insertMany = db.transaction((items) => {
  for (const item of items) insertConfig.run(...item);
});
insertMany(configs);

// =============================================
// TABLA IMPUESTO A LA RENTA 2026 (estimada)
// =============================================
const tablaIR_fixed = [
  [2026, 0, 11902, 0, 0],
  [2026, 11902, 15159, 0, 5],
  [2026, 15159, 19682, 163, 10],
  [2026, 19682, 26031, 615, 12],
  [2026, 26031, 34255, 1377, 15],
  [2026, 34255, 45407, 2611, 20],
  [2026, 45407, 60538, 4841, 25],
  [2026, 60538, 80717, 8624, 30],
  [2026, 80717, 107623, 14678, 35],
  [2026, 107623, 999999999, 24095, 37],
];

const insertIR = db.prepare(
  'INSERT OR REPLACE INTO tabla_ir (anio, fraccion_basica, exceso_hasta, impuesto_fraccion, porcentaje_excedente) VALUES (?, ?, ?, ?, ?)'
);

const insertIRMany = db.transaction((items) => {
  for (const item of items) insertIR.run(...item);
});
insertIRMany(tablaIR_fixed);

// =============================================
// FERIADOS 2026
// =============================================
const feriados = [
  ['2026-01-01', 'Año Nuevo', 2026],
  ['2026-02-16', 'Carnaval', 2026],
  ['2026-02-17', 'Carnaval', 2026],
  ['2026-04-02', 'Viernes Santo', 2026],
  ['2026-05-01', 'Día del Trabajo', 2026],
  ['2026-05-24', 'Batalla de Pichincha', 2026],
  ['2026-08-10', 'Primer Grito de Independencia', 2026],
  ['2026-10-09', 'Independencia de Guayaquil', 2026],
  ['2026-11-02', 'Día de los Difuntos', 2026],
  ['2026-11-03', 'Independencia de Cuenca', 2026],
  ['2026-12-25', 'Navidad', 2026],
];

const insertFeriado = db.prepare(
  'INSERT OR REPLACE INTO feriados (fecha, descripcion, anio) VALUES (?, ?, ?)'
);

const insertFeriadoMany = db.transaction((items) => {
  for (const item of items) insertFeriado.run(...item);
});
insertFeriadoMany(feriados);

// =============================================
// EMPLEADOS DE EJEMPLO
// =============================================
const empleados = [
  ['1712345678', 'García López', 'María José', '1990-05-15', '2022-01-15', 'Analista de Sistemas', 'Tecnología', 1200.00, 'Indefinido', 'Sierra/Amazonía', 2, '2200012345', 'Banco Pichincha', 'Ahorros', 'maria.garcia@empresa.com'],
  ['0912345678', 'Pérez Morales', 'Carlos Andrés', '1988-11-20', '2024-06-01', 'Contador General', 'Finanzas', 1800.00, 'Indefinido', 'Costa/Galápagos', 1, '3300067890', 'Banco del Pacífico', 'Corriente', 'carlos.perez@empresa.com'],
  ['1812345678', 'Rodríguez Silva', 'Ana Lucía', '1995-03-08', '2025-03-01', 'Asistente Administrativa', 'Administración', 550.00, 'Plazo Fijo', 'Sierra/Amazonía', 0, '1100098765', 'Banco de Guayaquil', 'Ahorros', 'ana.rodriguez@empresa.com'],
];

const insertEmpleado = db.prepare(`
  INSERT OR IGNORE INTO empleados (cedula, apellidos, nombres, fecha_nacimiento, fecha_ingreso, cargo, departamento, sueldo_base, tipo_contrato, region, cargas_familiares, cuenta_bancaria, banco, tipo_cuenta, email)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

const insertEmpleadoMany = db.transaction((items) => {
  for (const item of items) insertEmpleado.run(...item);
});
insertEmpleadoMany(empleados);

console.log('Base de datos inicializada con datos de configuración y ejemplo.');
process.exit(0);

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
// EMPLEADOS DE EJEMPLO (10 empleados)
// =============================================
const empleados = [
  ['1712345678', 'García López', 'María José',      '1990-05-15', '2022-01-15', 'Gerente de Tecnología',    'Tecnología',    1800.00, 'Indefinido', 'Sierra/Amazonía',  2, '2200012345', 'Banco Pichincha',    'Ahorros',   'maria.garcia@empresa.com'],
  ['0912345678', 'Pérez Morales', 'Carlos Andrés',  '1988-11-20', '2021-06-01', 'Contador General',         'Finanzas',      2100.00, 'Indefinido', 'Costa/Galápagos',  1, '3300067890', 'Banco del Pacífico', 'Corriente', 'carlos.perez@empresa.com'],
  ['1812345678', 'Rodríguez Silva', 'Ana Lucía',    '1995-03-08', '2025-03-01', 'Asistente Administrativa', 'Administración', 550.00, 'Plazo Fijo', 'Sierra/Amazonía',  0, '1100098765', 'Banco de Guayaquil', 'Ahorros',   'ana.rodriguez@empresa.com'],
  ['1756789012', 'Torres Vega', 'Luis Fernando',   '1987-07-22', '2020-08-10', 'Jefe de Ventas',           'Ventas',        2400.00, 'Indefinido', 'Sierra/Amazonía',  3, '2200054321', 'Banco Pichincha',    'Corriente', 'luis.torres@empresa.com'],
  ['0834567890', 'Mendoza Castro', 'Sofía Daniela','1993-12-01', '2023-02-15', 'Desarrolladora Backend',   'Tecnología',    1500.00, 'Indefinido', 'Costa/Galápagos',  1, '3300012876', 'Banco del Pacífico', 'Ahorros',   'sofia.mendoza@empresa.com'],
  ['1723456789', 'Vargas Ríos', 'Diego Sebastián', '1991-09-14', '2022-05-20', 'Analista de Marketing',    'Marketing',     1100.00, 'Indefinido', 'Sierra/Amazonía',  0, '2200078432', 'Banco Pichincha',    'Ahorros',   'diego.vargas@empresa.com'],
  ['1734567890', 'Flores Ortiz', 'Paola Andrea',   '1996-04-30', '2024-01-08', 'Diseñadora UX',            'Tecnología',     900.00, 'Indefinido', 'Sierra/Amazonía',  0, '2200034521', 'Banco Pichincha',    'Ahorros',   'paola.flores@empresa.com'],
  ['0823456789', 'Cabrera Muñoz', 'Roberto Carlos','1985-02-18', '2019-11-01', 'Director Financiero',      'Finanzas',      3200.00, 'Indefinido', 'Costa/Galápagos',  2, '3300056789', 'Banco del Pacífico', 'Corriente', 'roberto.cabrera@empresa.com'],
  ['1745678901', 'Salazar Ponce', 'Valentina',     '1998-08-25', '2025-07-01', 'Asistente Contable',       'Finanzas',       530.00, 'Plazo Fijo', 'Sierra/Amazonía',  0, '2200090123', 'Banco Pichincha',    'Ahorros',   'valentina.salazar@empresa.com'],
  ['1756890123', 'Espinoza Luna', 'Andrés Felipe', '1989-06-11', '2021-03-15', 'Jefe de RRHH',             'RRHH',          1950.00, 'Indefinido', 'Sierra/Amazonía',  1, '2200067890', 'Banco Pichincha',    'Ahorros',   'andres.espinoza@empresa.com'],
];

const insertEmpleado = db.prepare(`
  INSERT OR IGNORE INTO empleados (cedula, apellidos, nombres, fecha_nacimiento, fecha_ingreso, cargo, departamento, sueldo_base, tipo_contrato, region, cargas_familiares, cuenta_bancaria, banco, tipo_cuenta, email)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

const insertEmpleadoMany = db.transaction((items) => {
  for (const item of items) insertEmpleado.run(...item);
});
insertEmpleadoMany(empleados);

// =============================================
// ASISTENCIA (Marzo 2026 - sample)
// =============================================
const empIds = db.prepare('SELECT id FROM empleados WHERE activo = 1 ORDER BY id LIMIT 5').all().map(e => e.id);
const insertAsist = db.prepare(`
  INSERT OR IGNORE INTO asistencia (empleado_id, fecha, hora_entrada, hora_salida, horas_normales, horas_suplementarias)
  VALUES (?, ?, ?, ?, ?, ?)
`);
const diasMar = ['2026-03-02','2026-03-03','2026-03-04','2026-03-05','2026-03-06',
                 '2026-03-09','2026-03-10','2026-03-11','2026-03-12','2026-03-13',
                 '2026-03-16','2026-03-17','2026-03-18','2026-03-19','2026-03-20',
                 '2026-03-23','2026-03-24','2026-03-25','2026-03-26','2026-03-27'];
const insertAsistMany = db.transaction(() => {
  for (const eid of empIds) {
    for (const fecha of diasMar) {
      const supl = Math.random() > 0.8 ? 2 : 0;
      insertAsist.run(eid, fecha, '08:00', supl > 0 ? '18:00' : '17:00', 8, supl);
    }
  }
});
insertAsistMany();

// =============================================
// PRÉSTAMO DE EJEMPLO
// =============================================
const emp1 = db.prepare("SELECT id FROM empleados WHERE cedula = '1756789012'").get();
if (emp1) {
  db.prepare(`INSERT OR IGNORE INTO prestamos (empleado_id, tipo, monto_total, cuota_mensual, saldo, fecha_inicio)
    VALUES (?, 'Quirografario', 3000, 125, 2750, '2026-01-01')`).run(emp1.id);
}

// =============================================
// PERMISOS DE EJEMPLO
// =============================================
const emp2 = db.prepare("SELECT id FROM empleados WHERE cedula = '0834567890'").get();
if (emp2) {
  db.prepare(`INSERT OR IGNORE INTO permisos (empleado_id, tipo, fecha_inicio, fecha_fin, dias, estado, observacion)
    VALUES (?, 'Vacaciones', '2026-04-14', '2026-04-25', 10, 'Aprobado', 'Vacaciones programadas Q2')`).run(emp2.id);
}

// =============================================
// CICLO DE EVALUACIÓN 360° (demo pre-cargado)
// =============================================
const cicloPrev = db.prepare("SELECT id FROM ciclos_evaluacion WHERE nombre = 'Evaluación Semestral Q1 2026'").get();
if (!cicloPrev) {
  const ciclo = db.prepare(`
    INSERT INTO ciclos_evaluacion (nombre, descripcion, fecha_inicio, fecha_fin, estado)
    VALUES ('Evaluación Semestral Q1 2026', 'Evaluación de desempeño 360° primer semestre 2026', '2026-03-01', '2026-04-30', 'Activo')
  `).run();
  const cicloId = ciclo.lastInsertRowid;

  // Criterios
  const criterios = [
    ['Liderazgo',               'Capacidad de guiar y motivar al equipo',              1.5, 1],
    ['Trabajo en Equipo',       'Colaboración y disposición de apoyo',                 1.2, 2],
    ['Orientación al Resultado','Cumplimiento de objetivos y metas',                   1.5, 3],
    ['Comunicación',            'Claridad y asertividad en la comunicación',           1.0, 4],
    ['Innovación',              'Propone mejoras y soluciones creativas',              1.0, 5],
    ['Puntualidad y Compromiso','Cumplimiento de horarios y responsabilidades',        1.0, 6],
  ];
  const insertCrit = db.prepare('INSERT INTO criterios_evaluacion (ciclo_id, nombre, descripcion, peso, orden) VALUES (?, ?, ?, ?, ?)');
  const critIds = [];
  for (const c of criterios) {
    const r = insertCrit.run(cicloId, ...c);
    critIds.push(r.lastInsertRowid);
  }

  // Evaluados: los primeros 3 empleados activos
  const evaluados = db.prepare('SELECT id, nombres, apellidos FROM empleados WHERE activo = 1 ORDER BY id LIMIT 3').all();

  const insertEval = db.prepare(`
    INSERT INTO evaluaciones (ciclo_id, evaluado_id, evaluador_id, tipo_evaluador, token, completada, fecha_completada)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `);
  const insertResp = db.prepare('INSERT INTO respuestas_evaluacion (evaluacion_id, criterio_id, puntaje) VALUES (?, ?, ?)');

  const tipos = ['Jefe', 'Par', 'Par', 'Subordinado'];

  // Pre-populate completed evaluations for demo
  const scoresSets = [
    [5, 4, 5, 4, 3, 5], // evaluación jefe
    [4, 5, 4, 5, 4, 4], // evaluación par 1
    [3, 4, 5, 4, 5, 3], // evaluación par 2
    [4, 3, 4, 5, 3, 4], // evaluación subordinado
  ];

  for (const ev of evaluados) {
    for (let t = 0; t < tipos.length; t++) {
      const token = Math.random().toString(36).substring(2, 12);
      const evalRow = insertEval.run(
        cicloId, ev.id, null, tipos[t], token, 1, '2026-03-20'
      );
      const evalId = evalRow.lastInsertRowid;
      critIds.forEach((cid, idx) => {
        // Slight variation per evaluado
        const score = Math.min(5, Math.max(1, scoresSets[t][idx] + (Math.random() > 0.7 ? 1 : 0) - (Math.random() > 0.8 ? 1 : 0)));
        insertResp.run(evalId, cid, Math.round(score));
      });
    }
  }

  // One pending evaluation (not completed) - so the form demo works
  const pendToken = 'demo-token-001';
  const ev0 = evaluados[0];
  if (ev0) {
    insertEval.run(cicloId, ev0.id, null, 'Par', pendToken, 0, null);
  }
}

console.log('Base de datos inicializada con datos de demo (10 empleados + evaluación 360°).');
process.exit(0);

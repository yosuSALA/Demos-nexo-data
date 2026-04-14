const db = require('../config/database');

function initializeDatabase() {
  db.exec(`
    -- =============================================
    -- TABLA DE CONFIGURACIÓN (parametrizable)
    -- =============================================
    CREATE TABLE IF NOT EXISTS configuracion (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      clave TEXT UNIQUE NOT NULL,
      valor TEXT NOT NULL,
      descripcion TEXT,
      anio INTEGER DEFAULT 2026,
      updated_at TEXT DEFAULT (datetime('now'))
    );

    -- =============================================
    -- TABLA DEL IMPUESTO A LA RENTA (SRI)
    -- =============================================
    CREATE TABLE IF NOT EXISTS tabla_ir (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      anio INTEGER NOT NULL,
      fraccion_basica REAL NOT NULL,
      exceso_hasta REAL NOT NULL,
      impuesto_fraccion REAL NOT NULL,
      porcentaje_excedente REAL NOT NULL
    );

    -- =============================================
    -- EMPLEADOS
    -- =============================================
    CREATE TABLE IF NOT EXISTS empleados (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      cedula TEXT UNIQUE NOT NULL,
      apellidos TEXT NOT NULL,
      nombres TEXT NOT NULL,
      fecha_nacimiento TEXT,
      fecha_ingreso TEXT NOT NULL,
      fecha_salida TEXT,
      cargo TEXT NOT NULL,
      departamento TEXT,
      sueldo_base REAL NOT NULL,
      tipo_contrato TEXT NOT NULL DEFAULT 'Indefinido',
      region TEXT NOT NULL DEFAULT 'Sierra/Amazonía',
      cargas_familiares INTEGER DEFAULT 0,
      cuenta_bancaria TEXT,
      banco TEXT,
      tipo_cuenta TEXT DEFAULT 'Ahorros',
      email TEXT,
      telefono TEXT,
      direccion TEXT,
      activo INTEGER DEFAULT 1,
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    );

    -- =============================================
    -- ASISTENCIA
    -- =============================================
    CREATE TABLE IF NOT EXISTS asistencia (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      empleado_id INTEGER NOT NULL,
      fecha TEXT NOT NULL,
      hora_entrada TEXT,
      hora_salida TEXT,
      horas_normales REAL DEFAULT 0,
      horas_suplementarias REAL DEFAULT 0,
      horas_extraordinarias REAL DEFAULT 0,
      atraso_minutos INTEGER DEFAULT 0,
      observacion TEXT,
      FOREIGN KEY (empleado_id) REFERENCES empleados(id)
    );

    -- =============================================
    -- PERMISOS Y VACACIONES
    -- =============================================
    CREATE TABLE IF NOT EXISTS permisos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      empleado_id INTEGER NOT NULL,
      tipo TEXT NOT NULL,
      fecha_inicio TEXT NOT NULL,
      fecha_fin TEXT NOT NULL,
      dias REAL NOT NULL,
      justificado INTEGER DEFAULT 1,
      estado TEXT DEFAULT 'Pendiente',
      observacion TEXT,
      created_at TEXT DEFAULT (datetime('now')),
      FOREIGN KEY (empleado_id) REFERENCES empleados(id)
    );

    -- =============================================
    -- ROLES DE PAGO (cabecera)
    -- =============================================
    CREATE TABLE IF NOT EXISTS roles_pago (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      empleado_id INTEGER NOT NULL,
      periodo TEXT NOT NULL,
      mes INTEGER NOT NULL,
      anio INTEGER NOT NULL,
      tipo TEXT DEFAULT 'Mensual',

      -- Ingresos
      sueldo_base REAL DEFAULT 0,
      horas_suplementarias_valor REAL DEFAULT 0,
      horas_extraordinarias_valor REAL DEFAULT 0,
      comisiones REAL DEFAULT 0,
      bonos REAL DEFAULT 0,
      otros_ingresos REAL DEFAULT 0,
      total_ingresos REAL DEFAULT 0,

      -- Deducciones
      aporte_iess REAL DEFAULT 0,
      prestamo_quirografario REAL DEFAULT 0,
      prestamo_hipotecario REAL DEFAULT 0,
      anticipo_sueldo REAL DEFAULT 0,
      pension_alimenticia REAL DEFAULT 0,
      retencion_ir REAL DEFAULT 0,
      multas REAL DEFAULT 0,
      otras_deducciones REAL DEFAULT 0,
      total_deducciones REAL DEFAULT 0,

      -- Neto
      neto_a_recibir REAL DEFAULT 0,

      -- Provisiones (aporte patronal y beneficios)
      aporte_patronal REAL DEFAULT 0,
      decimo_tercero_prov REAL DEFAULT 0,
      decimo_cuarto_prov REAL DEFAULT 0,
      fondos_reserva_prov REAL DEFAULT 0,
      vacaciones_prov REAL DEFAULT 0,

      estado TEXT DEFAULT 'Borrador',
      created_at TEXT DEFAULT (datetime('now')),
      FOREIGN KEY (empleado_id) REFERENCES empleados(id)
    );

    -- =============================================
    -- PRÉSTAMOS Y ANTICIPOS
    -- =============================================
    CREATE TABLE IF NOT EXISTS prestamos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      empleado_id INTEGER NOT NULL,
      tipo TEXT NOT NULL,
      monto_total REAL NOT NULL,
      cuota_mensual REAL NOT NULL,
      saldo REAL NOT NULL,
      fecha_inicio TEXT NOT NULL,
      activo INTEGER DEFAULT 1,
      FOREIGN KEY (empleado_id) REFERENCES empleados(id)
    );

    -- =============================================
    -- UTILIDADES
    -- =============================================
    CREATE TABLE IF NOT EXISTS utilidades (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      anio INTEGER NOT NULL,
      utilidad_liquida REAL NOT NULL,
      total_15_porciento REAL DEFAULT 0,
      total_10_porciento REAL DEFAULT 0,
      total_5_porciento REAL DEFAULT 0,
      estado TEXT DEFAULT 'Calculado',
      created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS utilidades_detalle (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      utilidad_id INTEGER NOT NULL,
      empleado_id INTEGER NOT NULL,
      dias_trabajados INTEGER DEFAULT 0,
      cargas_familiares INTEGER DEFAULT 0,
      valor_10 REAL DEFAULT 0,
      valor_5 REAL DEFAULT 0,
      total REAL DEFAULT 0,
      FOREIGN KEY (utilidad_id) REFERENCES utilidades(id),
      FOREIGN KEY (empleado_id) REFERENCES empleados(id)
    );

    -- =============================================
    -- FERIADOS
    -- =============================================
    CREATE TABLE IF NOT EXISTS feriados (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      fecha TEXT NOT NULL,
      descripcion TEXT NOT NULL,
      anio INTEGER NOT NULL
    );

    -- Índices
    CREATE INDEX IF NOT EXISTS idx_asistencia_empleado ON asistencia(empleado_id, fecha);
    CREATE INDEX IF NOT EXISTS idx_roles_periodo ON roles_pago(empleado_id, anio, mes);
    CREATE INDEX IF NOT EXISTS idx_permisos_empleado ON permisos(empleado_id, estado);
  `);
}

module.exports = { initializeDatabase };

const express = require('express');
const path = require('path');
const session = require('express-session');
const { initializeDatabase } = require('./models/schema');

// Inicializar base de datos
initializeDatabase();

const app = express();
const PORT = process.env.PORT || 3000;

// Configuración
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, '..', 'views'));
app.use(express.static(path.join(__dirname, '..', 'public')));
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(
  session({
    secret: 'nomina-ec-2026-secret',
    resave: false,
    saveUninitialized: false,
  })
);

// Variables globales para vistas
app.use((req, res, next) => {
  res.locals.currentPath = req.path;
  res.locals.formatMoney = (n) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n || 0);
  res.locals.meses = [
    '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
  ];
  next();
});

// Rutas
app.use('/empleados', require('./routes/empleados'));
app.use('/asistencia', require('./routes/asistencia'));
app.use('/nomina', require('./routes/nomina'));
app.use('/permisos', require('./routes/permisos'));
app.use('/configuracion', require('./routes/configuracion'));
app.use('/reportes', require('./routes/reportes'));

// Dashboard
const db = require('./config/database');

app.get('/', (req, res) => {
  const totalEmpleados = db
    .prepare('SELECT COUNT(*) as total FROM empleados WHERE activo = 1')
    .get().total;

  const mes = new Date().getMonth() + 1;
  const anio = new Date().getFullYear();

  const costoNomina = db
    .prepare(
      'SELECT SUM(total_ingresos) as ingresos, SUM(neto_a_recibir) as neto, SUM(aporte_patronal) as patronal FROM roles_pago WHERE mes = ? AND anio = ?'
    )
    .get(mes, anio);

  // Contratos por vencer (próximos 30 días)
  const hoy = new Date().toISOString().split('T')[0];
  const en30 = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

  const contratosPorVencer = db
    .prepare(
      `SELECT * FROM empleados
       WHERE activo = 1 AND tipo_contrato = 'Plazo Fijo'
       AND fecha_ingreso <= ?`
    )
    .all(en30);

  // Permisos pendientes
  const permisosPendientes = db
    .prepare("SELECT COUNT(*) as total FROM permisos WHERE estado = 'Pendiente'")
    .get().total;

  res.render('dashboard', {
    totalEmpleados,
    costoNomina: costoNomina || { ingresos: 0, neto: 0, patronal: 0 },
    contratosPorVencer,
    permisosPendientes,
    mes,
    anio,
  });
});

app.listen(PORT, () => {
  console.log(`Sistema de Nómina ejecutándose en http://localhost:${PORT}`);
});

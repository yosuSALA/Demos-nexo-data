const express = require('express');
const router = express.Router();
const db = require('../config/database');
const { generarRolPago, generarNominaMensual } = require('../services/nominaService');
const { calcularDecimoTercero, calcularDecimoCuarto, calcularVacaciones, calcularUtilidades } = require('../services/beneficiosService');

// Vista principal de nómina
router.get('/', (req, res) => {
  const mes = parseInt(req.query.mes) || new Date().getMonth() + 1;
  const anio = parseInt(req.query.anio) || new Date().getFullYear();

  const roles = db
    .prepare(
      `SELECT r.*, e.cedula, e.apellidos, e.nombres, e.cargo
       FROM roles_pago r
       JOIN empleados e ON r.empleado_id = e.id
       WHERE r.mes = ? AND r.anio = ?
       ORDER BY e.apellidos`
    )
    .all(mes, anio);

  const totales = db
    .prepare(
      `SELECT
         SUM(total_ingresos) as total_ingresos,
         SUM(total_deducciones) as total_deducciones,
         SUM(neto_a_recibir) as total_neto,
         SUM(aporte_patronal) as total_patronal,
         COUNT(*) as num_empleados
       FROM roles_pago WHERE mes = ? AND anio = ?`
    )
    .get(mes, anio);

  res.render('nomina/index', { roles, totales, mes, anio });
});

// Generar nómina mensual completa
router.post('/generar', (req, res) => {
  const { mes, anio } = req.body;
  try {
    generarNominaMensual(parseInt(mes), parseInt(anio));
    res.redirect(`/nomina?mes=${mes}&anio=${anio}`);
  } catch (err) {
    res.redirect(`/nomina?mes=${mes}&anio=${anio}&error=${encodeURIComponent(err.message)}`);
  }
});

// Generar rol individual
router.post('/generar/:empleadoId', (req, res) => {
  const { mes, anio } = req.body;
  try {
    generarRolPago(parseInt(req.params.empleadoId), parseInt(mes), parseInt(anio));
    res.redirect(`/nomina?mes=${mes}&anio=${anio}`);
  } catch (err) {
    res.redirect(`/nomina?mes=${mes}&anio=${anio}&error=${encodeURIComponent(err.message)}`);
  }
});

// Ver rol de pago individual
router.get('/rol/:id', (req, res) => {
  const rol = db
    .prepare(
      `SELECT r.*, e.cedula, e.apellidos, e.nombres, e.cargo, e.departamento,
              e.fecha_ingreso, e.cuenta_bancaria, e.banco
       FROM roles_pago r
       JOIN empleados e ON r.empleado_id = e.id
       WHERE r.id = ?`
    )
    .get(req.params.id);
  if (!rol) return res.redirect('/nomina');
  res.render('nomina/rol', { rol });
});

// Editar valores adicionales del rol (comisiones, bonos, anticipos, etc.)
router.post('/rol/:id/extras', (req, res) => {
  const { comisiones, bonos, otros_ingresos, anticipo_sueldo, pension_alimenticia, otras_deducciones } = req.body;

  db.prepare(
    `UPDATE roles_pago SET
       comisiones = ?, bonos = ?, otros_ingresos = ?,
       anticipo_sueldo = ?, pension_alimenticia = ?, otras_deducciones = ?,
       estado = 'Borrador'
     WHERE id = ?`
  ).run(
    parseFloat(comisiones) || 0,
    parseFloat(bonos) || 0,
    parseFloat(otros_ingresos) || 0,
    parseFloat(anticipo_sueldo) || 0,
    parseFloat(pension_alimenticia) || 0,
    parseFloat(otras_deducciones) || 0,
    req.params.id
  );

  // Recalcular
  const rol = db.prepare('SELECT empleado_id, mes, anio FROM roles_pago WHERE id = ?').get(req.params.id);
  if (rol) {
    generarRolPago(rol.empleado_id, rol.mes, rol.anio);
  }

  res.redirect(`/nomina/rol/${req.params.id}`);
});

// Aprobar nómina
router.post('/aprobar', (req, res) => {
  const { mes, anio } = req.body;
  db.prepare(
    "UPDATE roles_pago SET estado = 'Aprobado' WHERE mes = ? AND anio = ? AND estado = 'Calculado'"
  ).run(parseInt(mes), parseInt(anio));
  res.redirect(`/nomina?mes=${mes}&anio=${anio}`);
});

// =============================================
// BENEFICIOS SOCIALES
// =============================================

// Décimo Tercero
router.get('/decimo-tercero', (req, res) => {
  const anio = parseInt(req.query.anio) || new Date().getFullYear();
  const empleados = db.prepare('SELECT id FROM empleados WHERE activo = 1').all();

  const detalles = [];
  for (const emp of empleados) {
    try {
      detalles.push(calcularDecimoTercero(emp.id, anio));
    } catch (e) { /* skip */ }
  }

  const total = detalles.reduce((s, d) => s + d.valor, 0);
  res.render('nomina/decimo-tercero', { detalles, anio, total });
});

// Décimo Cuarto
router.get('/decimo-cuarto', (req, res) => {
  const anio = parseInt(req.query.anio) || new Date().getFullYear();
  const empleados = db.prepare('SELECT id FROM empleados WHERE activo = 1').all();

  const detalles = [];
  for (const emp of empleados) {
    try {
      detalles.push(calcularDecimoCuarto(emp.id, anio));
    } catch (e) { /* skip */ }
  }

  const total = detalles.reduce((s, d) => s + d.valor, 0);
  res.render('nomina/decimo-cuarto', { detalles, anio, total });
});

// Vacaciones
router.get('/vacaciones', (req, res) => {
  const empleados = db.prepare('SELECT id FROM empleados WHERE activo = 1').all();

  const detalles = [];
  for (const emp of empleados) {
    try {
      detalles.push(calcularVacaciones(emp.id));
    } catch (e) { /* skip */ }
  }

  res.render('nomina/vacaciones', { detalles });
});

// Utilidades
router.get('/utilidades', (req, res) => {
  const anio = parseInt(req.query.anio) || new Date().getFullYear() - 1;
  const historial = db.prepare('SELECT * FROM utilidades ORDER BY anio DESC').all();
  res.render('nomina/utilidades', { historial, anio });
});

router.post('/utilidades', (req, res) => {
  const { utilidad_liquida, anio } = req.body;
  try {
    calcularUtilidades(parseFloat(utilidad_liquida), parseInt(anio));
    res.redirect(`/nomina/utilidades?anio=${anio}`);
  } catch (err) {
    res.redirect(`/nomina/utilidades?error=${encodeURIComponent(err.message)}`);
  }
});

// Ver detalle de utilidades
router.get('/utilidades/:id', (req, res) => {
  const utilidad = db.prepare('SELECT * FROM utilidades WHERE id = ?').get(req.params.id);
  if (!utilidad) return res.redirect('/nomina/utilidades');

  const detalles = db
    .prepare(
      `SELECT ud.*, e.cedula, e.apellidos, e.nombres
       FROM utilidades_detalle ud
       JOIN empleados e ON ud.empleado_id = e.id
       WHERE ud.utilidad_id = ?
       ORDER BY e.apellidos`
    )
    .all(req.params.id);

  res.render('nomina/utilidades-detalle', { utilidad, detalles });
});

module.exports = router;

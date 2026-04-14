const express = require('express');
const router = express.Router();
const db = require('../config/database');
const { getAllConfig, updateConfig, getTablaIR } = require('../services/configService');

// Ver configuración
router.get('/', (req, res) => {
  const anio = parseInt(req.query.anio) || new Date().getFullYear();
  const configs = getAllConfig(anio);
  const tablaIR = getTablaIR(anio);
  const feriados = db.prepare('SELECT * FROM feriados WHERE anio = ? ORDER BY fecha').all(anio);
  res.render('configuracion/index', { configs, tablaIR, feriados, anio });
});

// Actualizar configuración
router.post('/', (req, res) => {
  const { anio } = req.body;
  const configs = getAllConfig(parseInt(anio));

  for (const config of configs) {
    const newVal = req.body[`config_${config.clave}`];
    if (newVal !== undefined && newVal !== config.valor) {
      updateConfig(config.clave, newVal, parseInt(anio));
    }
  }

  res.redirect(`/configuracion?anio=${anio}`);
});

// Actualizar tabla IR
router.post('/tabla-ir', (req, res) => {
  const { anio, fraccion_basica, exceso_hasta, impuesto_fraccion, porcentaje_excedente } = req.body;

  // Eliminar tabla anterior del año
  db.prepare('DELETE FROM tabla_ir WHERE anio = ?').run(parseInt(anio));

  // Insertar nueva tabla
  const insert = db.prepare(
    'INSERT INTO tabla_ir (anio, fraccion_basica, exceso_hasta, impuesto_fraccion, porcentaje_excedente) VALUES (?, ?, ?, ?, ?)'
  );

  if (Array.isArray(fraccion_basica)) {
    const insertAll = db.transaction(() => {
      for (let i = 0; i < fraccion_basica.length; i++) {
        insert.run(
          parseInt(anio),
          parseFloat(fraccion_basica[i]),
          parseFloat(exceso_hasta[i]),
          parseFloat(impuesto_fraccion[i]),
          parseFloat(porcentaje_excedente[i])
        );
      }
    });
    insertAll();
  }

  res.redirect(`/configuracion?anio=${anio}`);
});

// Agregar feriado
router.post('/feriados', (req, res) => {
  const { fecha, descripcion, anio } = req.body;
  db.prepare('INSERT INTO feriados (fecha, descripcion, anio) VALUES (?, ?, ?)').run(
    fecha, descripcion, parseInt(anio)
  );
  res.redirect(`/configuracion?anio=${anio}`);
});

// Eliminar feriado
router.post('/feriados/:id/eliminar', (req, res) => {
  const feriado = db.prepare('SELECT anio FROM feriados WHERE id = ?').get(req.params.id);
  db.prepare('DELETE FROM feriados WHERE id = ?').run(req.params.id);
  res.redirect(`/configuracion?anio=${feriado ? feriado.anio : ''}`);
});

// Préstamos
router.get('/prestamos', (req, res) => {
  const prestamos = db
    .prepare(
      `SELECT p.*, e.cedula, e.apellidos, e.nombres
       FROM prestamos p
       JOIN empleados e ON p.empleado_id = e.id
       WHERE p.activo = 1
       ORDER BY e.apellidos`
    )
    .all();
  const empleados = db.prepare('SELECT id, apellidos, nombres FROM empleados WHERE activo = 1 ORDER BY apellidos').all();
  res.render('configuracion/prestamos', { prestamos, empleados });
});

router.post('/prestamos', (req, res) => {
  const { empleado_id, tipo, monto_total, cuota_mensual, fecha_inicio } = req.body;
  db.prepare(
    'INSERT INTO prestamos (empleado_id, tipo, monto_total, cuota_mensual, saldo, fecha_inicio) VALUES (?, ?, ?, ?, ?, ?)'
  ).run(empleado_id, tipo, parseFloat(monto_total), parseFloat(cuota_mensual), parseFloat(monto_total), fecha_inicio);
  res.redirect('/configuracion/prestamos');
});

module.exports = router;

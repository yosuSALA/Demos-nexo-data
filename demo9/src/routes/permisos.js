const express = require('express');
const router = express.Router();
const db = require('../config/database');

// Listar permisos
router.get('/', (req, res) => {
  const estado = req.query.estado || 'Pendiente';
  const permisos = db
    .prepare(
      `SELECT p.*, e.cedula, e.apellidos, e.nombres, e.cargo
       FROM permisos p
       JOIN empleados e ON p.empleado_id = e.id
       WHERE p.estado = ?
       ORDER BY p.created_at DESC`
    )
    .all(estado);

  const empleados = db.prepare('SELECT id, apellidos, nombres FROM empleados WHERE activo = 1 ORDER BY apellidos').all();
  res.render('permisos/index', { permisos, estado, empleados });
});

// Crear permiso
router.post('/', (req, res) => {
  const { empleado_id, tipo, fecha_inicio, fecha_fin, dias, justificado, observacion } = req.body;

  db.prepare(
    `INSERT INTO permisos (empleado_id, tipo, fecha_inicio, fecha_fin, dias, justificado, observacion)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  ).run(
    empleado_id, tipo, fecha_inicio, fecha_fin,
    parseFloat(dias), justificado === 'on' ? 1 : 0, observacion || null
  );

  res.redirect('/permisos');
});

// Aprobar/Rechazar
router.post('/:id/estado', (req, res) => {
  const { estado } = req.body;
  db.prepare('UPDATE permisos SET estado = ? WHERE id = ?').run(estado, req.params.id);
  res.redirect('/permisos');
});

module.exports = router;

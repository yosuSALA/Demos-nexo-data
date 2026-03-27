const express = require('express');
const router = express.Router();
const db = require('../config/database');
const { validarCedula } = require('../utils/validators');

// Listar empleados
router.get('/', (req, res) => {
  const filtro = req.query.q || '';
  const activo = req.query.activo !== '0' ? 1 : 0;

  let empleados;
  if (filtro) {
    empleados = db
      .prepare(
        `SELECT * FROM empleados WHERE activo = ? AND (cedula LIKE ? OR apellidos LIKE ? OR nombres LIKE ?) ORDER BY apellidos`
      )
      .all(activo, `%${filtro}%`, `%${filtro}%`, `%${filtro}%`);
  } else {
    empleados = db
      .prepare('SELECT * FROM empleados WHERE activo = ? ORDER BY apellidos')
      .all(activo);
  }

  res.render('empleados/index', { empleados, filtro, activo });
});

// Formulario nuevo empleado
router.get('/nuevo', (req, res) => {
  res.render('empleados/form', { empleado: null, error: null });
});

// Crear empleado
router.post('/', (req, res) => {
  const {
    cedula, apellidos, nombres, fecha_nacimiento, fecha_ingreso,
    cargo, departamento, sueldo_base, tipo_contrato, region,
    cargas_familiares, cuenta_bancaria, banco, tipo_cuenta, email, telefono, direccion,
  } = req.body;

  if (!validarCedula(cedula)) {
    return res.render('empleados/form', {
      empleado: req.body,
      error: 'Cédula inválida. Debe tener 10 dígitos y pasar la validación.',
    });
  }

  try {
    db.prepare(
      `INSERT INTO empleados (cedula, apellidos, nombres, fecha_nacimiento, fecha_ingreso, cargo, departamento, sueldo_base, tipo_contrato, region, cargas_familiares, cuenta_bancaria, banco, tipo_cuenta, email, telefono, direccion)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).run(
      cedula, apellidos, nombres, fecha_nacimiento || null, fecha_ingreso,
      cargo, departamento || null, parseFloat(sueldo_base), tipo_contrato, region,
      parseInt(cargas_familiares) || 0, cuenta_bancaria || null, banco || null,
      tipo_cuenta || 'Ahorros', email || null, telefono || null, direccion || null
    );
    res.redirect('/empleados');
  } catch (err) {
    res.render('empleados/form', {
      empleado: req.body,
      error: err.message.includes('UNIQUE') ? 'Ya existe un empleado con esa cédula.' : err.message,
    });
  }
});

// Ver detalle
router.get('/:id', (req, res) => {
  const empleado = db.prepare('SELECT * FROM empleados WHERE id = ?').get(req.params.id);
  if (!empleado) return res.redirect('/empleados');

  const roles = db
    .prepare('SELECT * FROM roles_pago WHERE empleado_id = ? ORDER BY anio DESC, mes DESC LIMIT 12')
    .all(req.params.id);
  const permisos = db
    .prepare('SELECT * FROM permisos WHERE empleado_id = ? ORDER BY fecha_inicio DESC LIMIT 10')
    .all(req.params.id);

  res.render('empleados/detalle', { empleado, roles, permisos });
});

// Editar
router.get('/:id/editar', (req, res) => {
  const empleado = db.prepare('SELECT * FROM empleados WHERE id = ?').get(req.params.id);
  if (!empleado) return res.redirect('/empleados');
  res.render('empleados/form', { empleado, error: null });
});

// Actualizar
router.post('/:id', (req, res) => {
  const {
    cedula, apellidos, nombres, fecha_nacimiento, fecha_ingreso,
    cargo, departamento, sueldo_base, tipo_contrato, region,
    cargas_familiares, cuenta_bancaria, banco, tipo_cuenta, email, telefono, direccion,
  } = req.body;

  if (!validarCedula(cedula)) {
    return res.render('empleados/form', {
      empleado: { ...req.body, id: req.params.id },
      error: 'Cédula inválida.',
    });
  }

  try {
    db.prepare(
      `UPDATE empleados SET cedula=?, apellidos=?, nombres=?, fecha_nacimiento=?, fecha_ingreso=?,
       cargo=?, departamento=?, sueldo_base=?, tipo_contrato=?, region=?,
       cargas_familiares=?, cuenta_bancaria=?, banco=?, tipo_cuenta=?, email=?, telefono=?, direccion=?,
       updated_at=datetime('now')
       WHERE id=?`
    ).run(
      cedula, apellidos, nombres, fecha_nacimiento || null, fecha_ingreso,
      cargo, departamento || null, parseFloat(sueldo_base), tipo_contrato, region,
      parseInt(cargas_familiares) || 0, cuenta_bancaria || null, banco || null,
      tipo_cuenta || 'Ahorros', email || null, telefono || null, direccion || null,
      req.params.id
    );
    res.redirect(`/empleados/${req.params.id}`);
  } catch (err) {
    res.render('empleados/form', {
      empleado: { ...req.body, id: req.params.id },
      error: err.message,
    });
  }
});

// Desactivar
router.post('/:id/desactivar', (req, res) => {
  const { fecha_salida } = req.body;
  db.prepare(
    "UPDATE empleados SET activo = 0, fecha_salida = ?, updated_at = datetime('now') WHERE id = ?"
  ).run(fecha_salida || new Date().toISOString().split('T')[0], req.params.id);
  res.redirect('/empleados');
});

module.exports = router;

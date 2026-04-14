const express = require('express');
const router = express.Router();
const db = require('../config/database');
const { esFeriado } = require('../services/configService');

// Listar asistencia por fecha
router.get('/', (req, res) => {
  const fecha = req.query.fecha || new Date().toISOString().split('T')[0];
  const registros = db
    .prepare(
      `SELECT a.*, e.cedula, e.apellidos, e.nombres, e.cargo
       FROM asistencia a
       JOIN empleados e ON a.empleado_id = e.id
       WHERE a.fecha = ?
       ORDER BY e.apellidos`
    )
    .all(fecha);

  const empleados = db.prepare('SELECT id, cedula, apellidos, nombres FROM empleados WHERE activo = 1 ORDER BY apellidos').all();

  res.render('asistencia/index', { registros, fecha, empleados });
});

// Registrar entrada/salida
router.post('/marcar', (req, res) => {
  const { empleado_id, fecha, hora_entrada, hora_salida, observacion } = req.body;

  // Verificar si ya existe registro para ese día
  const existente = db
    .prepare('SELECT * FROM asistencia WHERE empleado_id = ? AND fecha = ?')
    .get(empleado_id, fecha);

  if (existente && hora_salida && !existente.hora_salida) {
    // Actualizar salida
    const empleado = db.prepare('SELECT sueldo_base FROM empleados WHERE id = ?').get(empleado_id);
    const { hNorm, hSupl, hExtr, atraso } = calcularHoras(
      existente.hora_entrada,
      hora_salida,
      fecha,
      empleado
    );

    db.prepare(
      `UPDATE asistencia SET hora_salida = ?, horas_normales = ?, horas_suplementarias = ?,
       horas_extraordinarias = ?, atraso_minutos = ?, observacion = COALESCE(?, observacion)
       WHERE id = ?`
    ).run(hora_salida, hNorm, hSupl, hExtr, atraso, observacion || null, existente.id);
  } else if (!existente) {
    // Calcular atraso (asumiendo entrada estándar 08:00)
    let atraso = 0;
    if (hora_entrada) {
      const [h, m] = hora_entrada.split(':').map(Number);
      const minutosEntrada = h * 60 + m;
      const minutosEsperado = 8 * 60; // 08:00
      if (minutosEntrada > minutosEsperado) {
        atraso = minutosEntrada - minutosEsperado;
      }
    }

    let hNorm = 0, hSupl = 0, hExtr = 0;
    if (hora_entrada && hora_salida) {
      const empleado = db.prepare('SELECT sueldo_base FROM empleados WHERE id = ?').get(empleado_id);
      const calc = calcularHoras(hora_entrada, hora_salida, fecha, empleado);
      hNorm = calc.hNorm;
      hSupl = calc.hSupl;
      hExtr = calc.hExtr;
      atraso = calc.atraso;
    }

    db.prepare(
      `INSERT INTO asistencia (empleado_id, fecha, hora_entrada, hora_salida, horas_normales, horas_suplementarias, horas_extraordinarias, atraso_minutos, observacion)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).run(empleado_id, fecha, hora_entrada || null, hora_salida || null, hNorm, hSupl, hExtr, atraso, observacion || null);
  }

  res.redirect(`/asistencia?fecha=${fecha}`);
});

// Eliminar registro
router.post('/:id/eliminar', (req, res) => {
  const reg = db.prepare('SELECT fecha FROM asistencia WHERE id = ?').get(req.params.id);
  db.prepare('DELETE FROM asistencia WHERE id = ?').run(req.params.id);
  res.redirect(`/asistencia?fecha=${reg ? reg.fecha : ''}`);
});

function calcularHoras(horaEntrada, horaSalida, fecha, empleado) {
  const [he, me] = horaEntrada.split(':').map(Number);
  const [hs, ms] = horaSalida.split(':').map(Number);

  const minutosEntrada = he * 60 + me;
  const minutosSalida = hs * 60 + ms;
  const totalMinutos = Math.max(0, minutosSalida - minutosEntrada - 60); // resta 1h almuerzo
  const totalHoras = totalMinutos / 60;

  // Atraso (entrada esperada 08:00)
  const atraso = Math.max(0, minutosEntrada - 480);

  // Determinar si es feriado o fin de semana
  const d = new Date(fecha + 'T12:00:00');
  const diaSemana = d.getDay(); // 0=dom, 6=sab
  const esFinDeSemana = diaSemana === 0 || diaSemana === 6;
  const esHoliday = esFeriado(fecha);

  let hNorm = 0, hSupl = 0, hExtr = 0;

  if (esFinDeSemana || esHoliday) {
    // Todo es extraordinario
    hExtr = totalHoras;
  } else {
    hNorm = Math.min(totalHoras, 8);
    const extra = Math.max(0, totalHoras - 8);
    if (extra > 0) {
      // Suplementarias hasta las 24:00, extraordinarias después
      if (hs <= 24) {
        hSupl = extra;
      } else {
        hSupl = Math.max(0, (24 * 60 - (minutosEntrada + 8 * 60 + 60)) / 60);
        hExtr = extra - hSupl;
      }
    }
  }

  return {
    hNorm: Math.round(hNorm * 100) / 100,
    hSupl: Math.round(hSupl * 100) / 100,
    hExtr: Math.round(hExtr * 100) / 100,
    atraso,
  };
}

module.exports = router;

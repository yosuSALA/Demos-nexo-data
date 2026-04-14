const express = require('express');
const router = express.Router();
const db = require('../config/database');

// =============================================
// CICLOS - LISTADO
// =============================================
router.get('/', (req, res) => {
  const ciclos = db.prepare(`
    SELECT c.*,
      (SELECT COUNT(*) FROM evaluaciones e WHERE e.ciclo_id = c.id) as total_eval,
      (SELECT COUNT(*) FROM evaluaciones e WHERE e.ciclo_id = c.id AND e.completada = 1) as completadas,
      (SELECT COUNT(DISTINCT e.evaluado_id) FROM evaluaciones e WHERE e.ciclo_id = c.id) as total_evaluados
    FROM ciclos_evaluacion c
    ORDER BY c.created_at DESC
  `).all();
  res.render('evaluaciones/index', { ciclos });
});

// =============================================
// NUEVO CICLO - FORMULARIO
// =============================================
router.get('/nuevo-ciclo', (req, res) => {
  const empleados = db.prepare('SELECT id, apellidos, nombres, cargo, departamento FROM empleados WHERE activo = 1 ORDER BY apellidos').all();
  res.render('evaluaciones/ciclo-form', { empleados, error: null });
});

// =============================================
// NUEVO CICLO - GUARDAR
// =============================================
router.post('/ciclo', (req, res) => {
  const { nombre, descripcion, fecha_inicio, fecha_fin, evaluados, criterios_nombre } = req.body;

  try {
    const ciclo = db.prepare(`
      INSERT INTO ciclos_evaluacion (nombre, descripcion, fecha_inicio, fecha_fin, estado)
      VALUES (?, ?, ?, ?, 'Activo')
    `).run(nombre, descripcion || '', fecha_inicio, fecha_fin);
    const cicloId = ciclo.lastInsertRowid;

    // Criterios
    const nombres = Array.isArray(criterios_nombre) ? criterios_nombre : [criterios_nombre];
    const insertCrit = db.prepare('INSERT INTO criterios_evaluacion (ciclo_id, nombre, peso, orden) VALUES (?, ?, 1, ?)');
    nombres.filter(n => n && n.trim()).forEach((n, i) => insertCrit.run(cicloId, n.trim(), i + 1));

    // Evaluados y evaluadores automáticos (jefe + 2 pares + 1 subordinado por evaluado)
    const evalIds = Array.isArray(evaluados) ? evaluados.map(Number) : [Number(evaluados)];
    const insertEval = db.prepare(`
      INSERT INTO evaluaciones (ciclo_id, evaluado_id, tipo_evaluador, token, completada)
      VALUES (?, ?, ?, ?, 0)
    `);
    const tipos = ['Jefe', 'Par', 'Par', 'Subordinado'];
    const genToken = () => Math.random().toString(36).substring(2, 14);

    db.transaction(() => {
      for (const eid of evalIds) {
        for (const tipo of tipos) {
          insertEval.run(cicloId, eid, tipo, genToken());
        }
      }
    })();

    res.redirect('/evaluaciones');
  } catch (err) {
    const empleados = db.prepare('SELECT id, apellidos, nombres, cargo FROM empleados WHERE activo = 1 ORDER BY apellidos').all();
    res.render('evaluaciones/ciclo-form', { empleados, error: err.message });
  }
});

// =============================================
// VER CICLO - DETALLE
// =============================================
router.get('/ciclo/:id', (req, res) => {
  const ciclo = db.prepare('SELECT * FROM ciclos_evaluacion WHERE id = ?').get(req.params.id);
  if (!ciclo) return res.redirect('/evaluaciones');

  const evaluados = db.prepare(`
    SELECT e.evaluado_id,
      emp.apellidos || ' ' || emp.nombres as nombre,
      emp.cargo, emp.departamento,
      COUNT(e.id) as total_eval,
      SUM(e.completada) as completadas
    FROM evaluaciones e
    JOIN empleados emp ON emp.id = e.evaluado_id
    WHERE e.ciclo_id = ?
    GROUP BY e.evaluado_id
    ORDER BY emp.apellidos
  `).all(req.params.id);

  const detalles = db.prepare(`
    SELECT e.id, e.tipo_evaluador, e.completada, e.token, e.fecha_completada
    FROM evaluaciones e WHERE e.ciclo_id = ? ORDER BY e.evaluado_id, e.tipo_evaluador
  `).all(req.params.id);

  res.render('evaluaciones/ciclo-detalle', { ciclo, evaluados, detalles });
});

// =============================================
// FORMULARIO ANÓNIMO DE EVALUACIÓN
// =============================================
router.get('/evaluar/:token', (req, res) => {
  const evaluacion = db.prepare(`
    SELECT e.*, emp.apellidos || ' ' || emp.nombres as evaluado_nombre, emp.cargo as evaluado_cargo,
      c.nombre as ciclo_nombre
    FROM evaluaciones e
    JOIN empleados emp ON emp.id = e.evaluado_id
    JOIN ciclos_evaluacion c ON c.id = e.ciclo_id
    WHERE e.token = ?
  `).get(req.params.token);

  if (!evaluacion) return res.status(404).send('<h2>Enlace de evaluación no válido.</h2>');
  if (evaluacion.completada) return res.render('evaluaciones/ya-completada', { evaluacion });

  const criterios = db.prepare('SELECT * FROM criterios_evaluacion WHERE ciclo_id = ? ORDER BY orden').all(evaluacion.ciclo_id);
  res.render('evaluaciones/evaluar', { evaluacion, criterios, error: null });
});

router.post('/evaluar/:token', (req, res) => {
  const evaluacion = db.prepare('SELECT * FROM evaluaciones WHERE token = ? AND completada = 0').get(req.params.token);
  if (!evaluacion) return res.status(400).send('<h2>Evaluación ya completada o no válida.</h2>');

  const criterios = db.prepare('SELECT * FROM criterios_evaluacion WHERE ciclo_id = ? ORDER BY orden').all(evaluacion.ciclo_id);
  const insertResp = db.prepare('INSERT INTO respuestas_evaluacion (evaluacion_id, criterio_id, puntaje, comentario) VALUES (?, ?, ?, ?)');

  try {
    db.transaction(() => {
      for (const c of criterios) {
        const puntaje = parseInt(req.body[`puntaje_${c.id}`]);
        const comentario = req.body[`comentario_${c.id}`] || '';
        if (!puntaje || puntaje < 1 || puntaje > 5) throw new Error(`Puntaje inválido para: ${c.nombre}`);
        insertResp.run(evaluacion.id, c.id, puntaje, comentario);
      }
      db.prepare("UPDATE evaluaciones SET completada = 1, fecha_completada = datetime('now') WHERE id = ?").run(evaluacion.id);
    })();
    res.render('evaluaciones/gracias', {});
  } catch (err) {
    res.render('evaluaciones/evaluar', { evaluacion, criterios, error: err.message });
  }
});

// =============================================
// REPORTE POR EMPLEADO EN CICLO
// =============================================
router.get('/reporte/:cicloId/:empleadoId', (req, res) => {
  const ciclo = db.prepare('SELECT * FROM ciclos_evaluacion WHERE id = ?').get(req.params.cicloId);
  const empleado = db.prepare('SELECT * FROM empleados WHERE id = ?').get(req.params.empleadoId);
  if (!ciclo || !empleado) return res.redirect('/evaluaciones');

  const criterios = db.prepare('SELECT * FROM criterios_evaluacion WHERE ciclo_id = ? ORDER BY orden').all(req.params.cicloId);

  // Promedios por criterio y tipo de evaluador
  const promedios = db.prepare(`
    SELECT cr.nombre as criterio,
      e.tipo_evaluador,
      ROUND(AVG(r.puntaje), 2) as promedio,
      COUNT(r.id) as respuestas
    FROM respuestas_evaluacion r
    JOIN evaluaciones e ON e.id = r.evaluacion_id
    JOIN criterios_evaluacion cr ON cr.id = r.criterio_id
    WHERE e.ciclo_id = ? AND e.evaluado_id = ? AND e.completada = 1
    GROUP BY cr.id, e.tipo_evaluador
    ORDER BY cr.orden
  `).all(req.params.cicloId, req.params.empleadoId);

  // Promedio global por criterio
  const promedioGlobal = db.prepare(`
    SELECT cr.nombre as criterio, cr.id as criterio_id,
      ROUND(AVG(r.puntaje), 2) as promedio
    FROM respuestas_evaluacion r
    JOIN evaluaciones e ON e.id = r.evaluacion_id
    JOIN criterios_evaluacion cr ON cr.id = r.criterio_id
    WHERE e.ciclo_id = ? AND e.evaluado_id = ? AND e.completada = 1
    GROUP BY cr.id ORDER BY cr.orden
  `).all(req.params.cicloId, req.params.empleadoId);

  // Promedio del ciclo completo (todos los evaluados)
  const promedioGeneral = db.prepare(`
    SELECT cr.nombre as criterio,
      ROUND(AVG(r.puntaje), 2) as promedio
    FROM respuestas_evaluacion r
    JOIN evaluaciones e ON e.id = r.evaluacion_id
    JOIN criterios_evaluacion cr ON cr.id = r.criterio_id
    WHERE e.ciclo_id = ? AND e.completada = 1
    GROUP BY cr.id ORDER BY cr.orden
  `).all(req.params.cicloId);

  const totalCompletadas = db.prepare(
    'SELECT COUNT(*) as n FROM evaluaciones WHERE ciclo_id = ? AND evaluado_id = ? AND completada = 1'
  ).get(req.params.cicloId, req.params.empleadoId).n;

  res.render('evaluaciones/reporte', {
    ciclo, empleado, criterios, promedios, promedioGlobal, promedioGeneral, totalCompletadas
  });
});

module.exports = router;

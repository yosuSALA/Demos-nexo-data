const db = require('../config/database');

function getConfig(clave, anio = 2026) {
  const row = db
    .prepare('SELECT valor FROM configuracion WHERE clave = ? AND anio = ?')
    .get(clave, anio);
  return row ? parseFloat(row.valor) : null;
}

function getConfigStr(clave, anio = 2026) {
  const row = db
    .prepare('SELECT valor FROM configuracion WHERE clave = ? AND anio = ?')
    .get(clave, anio);
  return row ? row.valor : null;
}

function getAllConfig(anio = 2026) {
  return db
    .prepare('SELECT * FROM configuracion WHERE anio = ? ORDER BY clave')
    .all(anio);
}

function updateConfig(clave, valor, anio = 2026) {
  return db
    .prepare(
      "UPDATE configuracion SET valor = ?, updated_at = datetime('now') WHERE clave = ? AND anio = ?"
    )
    .run(valor, clave, anio);
}

function getTablaIR(anio = 2026) {
  return db
    .prepare(
      'SELECT * FROM tabla_ir WHERE anio = ? ORDER BY fraccion_basica ASC'
    )
    .all(anio);
}

function getFeriados(anio = 2026) {
  return db.prepare('SELECT * FROM feriados WHERE anio = ?').all(anio);
}

function esFeriado(fecha) {
  const row = db
    .prepare('SELECT id FROM feriados WHERE fecha = ?')
    .get(fecha);
  return !!row;
}

module.exports = {
  getConfig,
  getConfigStr,
  getAllConfig,
  updateConfig,
  getTablaIR,
  getFeriados,
  esFeriado,
};

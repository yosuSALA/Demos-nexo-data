const express = require('express');
const router = express.Router();
const db = require('../config/database');
const PDFDocument = require('pdfkit');
const { formatMoney } = require('../utils/validators');

// Dashboard de reportes
router.get('/', (req, res) => {
  res.render('reportes/index');
});

// Generar PDF rol de pago individual
router.get('/pdf/rol/:id', (req, res) => {
  const rol = db
    .prepare(
      `SELECT r.*, e.cedula, e.apellidos, e.nombres, e.cargo, e.departamento,
              e.fecha_ingreso, e.cuenta_bancaria, e.banco, e.tipo_cuenta
       FROM roles_pago r
       JOIN empleados e ON r.empleado_id = e.id
       WHERE r.id = ?`
    )
    .get(req.params.id);

  if (!rol) return res.status(404).send('Rol no encontrado');

  const doc = new PDFDocument({ size: 'A4', margin: 40 });
  res.setHeader('Content-Type', 'application/pdf');
  res.setHeader(
    'Content-Disposition',
    `inline; filename=rol_${rol.cedula}_${rol.periodo}.pdf`
  );
  doc.pipe(res);

  // Encabezado
  doc.fontSize(16).text('ROL DE PAGOS', { align: 'center' });
  doc.fontSize(10).text(`Período: ${rol.periodo}`, { align: 'center' });
  doc.moveDown();

  // Datos del empleado
  doc.fontSize(9);
  doc.text(`Cédula: ${rol.cedula}          Nombre: ${rol.apellidos} ${rol.nombres}`);
  doc.text(`Cargo: ${rol.cargo}          Departamento: ${rol.departamento || 'N/A'}`);
  doc.text(`Fecha Ingreso: ${rol.fecha_ingreso}          Banco: ${rol.banco || 'N/A'} - ${rol.cuenta_bancaria || 'N/A'}`);
  doc.moveDown();

  // Tabla de ingresos
  doc.fontSize(11).text('INGRESOS', { underline: true });
  doc.fontSize(9);
  const ingresos = [
    ['Sueldo Base', rol.sueldo_base],
    ['Horas Suplementarias', rol.horas_suplementarias_valor],
    ['Horas Extraordinarias', rol.horas_extraordinarias_valor],
    ['Comisiones', rol.comisiones],
    ['Bonos', rol.bonos],
    ['Otros Ingresos', rol.otros_ingresos],
  ];

  for (const [label, val] of ingresos) {
    if (val > 0) {
      doc.text(`  ${label}:`, 50, doc.y, { continued: true, width: 300 });
      doc.text(`$${val.toFixed(2)}`, 400, doc.y, { align: 'right', width: 100 });
    }
  }
  doc.moveDown(0.5);
  doc.text(`  TOTAL INGRESOS:`, 50, doc.y, { continued: true, width: 300 });
  doc.font('Helvetica-Bold').text(`$${rol.total_ingresos.toFixed(2)}`, 400, doc.y, { align: 'right', width: 100 });
  doc.font('Helvetica');
  doc.moveDown();

  // Tabla de deducciones
  doc.fontSize(11).text('DEDUCCIONES', { underline: true });
  doc.fontSize(9);
  const deducciones = [
    ['Aporte IESS (9.45%)', rol.aporte_iess],
    ['Préstamo Quirografario', rol.prestamo_quirografario],
    ['Préstamo Hipotecario', rol.prestamo_hipotecario],
    ['Anticipo de Sueldo', rol.anticipo_sueldo],
    ['Pensión Alimenticia', rol.pension_alimenticia],
    ['Retención IR', rol.retencion_ir],
    ['Multas/Atrasos', rol.multas],
    ['Otras Deducciones', rol.otras_deducciones],
  ];

  for (const [label, val] of deducciones) {
    if (val > 0) {
      doc.text(`  ${label}:`, 50, doc.y, { continued: true, width: 300 });
      doc.text(`$${val.toFixed(2)}`, 400, doc.y, { align: 'right', width: 100 });
    }
  }
  doc.moveDown(0.5);
  doc.text(`  TOTAL DEDUCCIONES:`, 50, doc.y, { continued: true, width: 300 });
  doc.font('Helvetica-Bold').text(`$${rol.total_deducciones.toFixed(2)}`, 400, doc.y, { align: 'right', width: 100 });
  doc.font('Helvetica');
  doc.moveDown();

  // Neto
  doc.fontSize(13).font('Helvetica-Bold');
  doc.text(`LÍQUIDO A RECIBIR: $${rol.neto_a_recibir.toFixed(2)}`, { align: 'center' });
  doc.font('Helvetica');
  doc.moveDown(2);

  // Firmas
  doc.fontSize(9);
  doc.text('_________________________', 80, doc.y);
  doc.text('_________________________', 350, doc.y - 12);
  doc.text('Firma Empleador', 110, doc.y + 5);
  doc.text('Firma Empleado', 385, doc.y - 7);

  doc.end();
});

// CSV para IESS (archivo plano)
router.get('/csv/iess/:mes/:anio', (req, res) => {
  const { mes, anio } = req.params;

  const roles = db
    .prepare(
      `SELECT r.*, e.cedula, e.apellidos, e.nombres
       FROM roles_pago r
       JOIN empleados e ON r.empleado_id = e.id
       WHERE r.mes = ? AND r.anio = ?
       ORDER BY e.apellidos`
    )
    .all(parseInt(mes), parseInt(anio));

  let csv = 'CEDULA,APELLIDOS,NOMBRES,SUELDO,DIAS_TRABAJADOS,HORAS_SUPL,HORAS_EXTR,TOTAL_INGRESOS,APORTE_PERSONAL,APORTE_PATRONAL,FONDOS_RESERVA\n';

  for (const r of roles) {
    csv += `${r.cedula},${r.apellidos},${r.nombres},${r.sueldo_base.toFixed(2)},30,${r.horas_suplementarias_valor.toFixed(2)},${r.horas_extraordinarias_valor.toFixed(2)},${r.total_ingresos.toFixed(2)},${r.aporte_iess.toFixed(2)},${r.aporte_patronal.toFixed(2)},${r.fondos_reserva_prov.toFixed(2)}\n`;
  }

  res.setHeader('Content-Type', 'text/csv');
  res.setHeader('Content-Disposition', `attachment; filename=planilla_iess_${anio}_${mes}.csv`);
  res.send(csv);
});

// CSV para transferencias bancarias (Cash Management)
router.get('/csv/banco/:mes/:anio', (req, res) => {
  const { mes, anio } = req.params;

  const roles = db
    .prepare(
      `SELECT r.*, e.cedula, e.apellidos, e.nombres, e.cuenta_bancaria, e.banco, e.tipo_cuenta
       FROM roles_pago r
       JOIN empleados e ON r.empleado_id = e.id
       WHERE r.mes = ? AND r.anio = ? AND r.estado = 'Aprobado'
       ORDER BY e.apellidos`
    )
    .all(parseInt(mes), parseInt(anio));

  let csv = 'TIPO_CUENTA,NUMERO_CUENTA,CEDULA,NOMBRES,MONTO,REFERENCIA\n';

  for (const r of roles) {
    const tipoCta = r.tipo_cuenta === 'Ahorros' ? 'AHO' : 'CTE';
    csv += `${tipoCta},${r.cuenta_bancaria || ''},${r.cedula},${r.apellidos} ${r.nombres},${r.neto_a_recibir.toFixed(2)},NOMINA ${r.periodo}\n`;
  }

  res.setHeader('Content-Type', 'text/csv');
  res.setHeader('Content-Disposition', `attachment; filename=transferencias_${anio}_${mes}.csv`);
  res.send(csv);
});

module.exports = router;

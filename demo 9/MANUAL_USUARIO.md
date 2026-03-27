# Manual de Usuario - Sistema de RRHH y Nómina (Ecuador)

Bienvenido al **Sistema de Recursos Humanos y Nómina**, parametrizado estrictamente bajo las directrices del **Código del Trabajo del Ecuador**. Este documento tiene como objetivo explicar el funcionamiento de cada módulo para los usuarios finales (Administradores, RRHH, Contabilidad).

## Índice
1. [Introducción](#introducción)
2. [Dashboard Principal](#dashboard-principal)
3. [Módulo de Empleados](#módulo-de-empleados)
4. [Módulo de Asistencia](#módulo-de-asistencia)
5. [Módulo de Permisos y Vacaciones](#módulo-de-permisos-y-vacaciones)
6. [Módulo de Nómina (Roles de Pago)](#módulo-de-nómina-roles-de-pago)
7. [Préstamos, Anticipos y Utilidades](#préstamos-anticipos-y-utilidades)
8. [Configuración General](#configuración-general)
9. [Reportes](#reportes)

---

## Introducción
El sistema permite la gestión integral del personal, desde el registro de su información básica hasta la generación de sus roles de pago mensuales, provisiones y cálculo de utilidades anuales. Todo se rige bajo los parámetros legales vigentes (IESS, SRI, Ministerio de Trabajo).

## Dashboard Principal
Al ingresar al sistema, visualizará un panel de control con indicadores clave:
* **Total de Empleados Activos:** Muestra cuántas personas laboran actualmente.
* **Costo de Nómina Mensual:** Desglose rápido del total de ingresos a pagar, el valor neto y el aporte patronal del mes en curso.
* **Alertas de Contratos:** Listado de contratos a "Plazo Fijo" que están próximos a vencer (en los próximos 30 días).
* **Permisos Pendientes:** Número de solicitudes de permisos o vacaciones que esperan aprobación.

## Módulo de Empleados
Aquí se gestiona el "kardex" o ficha técnica de cada trabajador.
* **Registro de datos personales:** Cédula, Nombres, Fecha de nacimiento, etc.
* **Datos laborales:** Fecha de ingreso, cargo, departamento, sueldo base, tipo de contrato (Indefinido, Plazo Fijo, etc.), y la región (Sierra/Amazonía o Costa/Galápagos - vital para el cálculo del Décimo Cuarto Sueldo).
* **Cargas Familiares:** Cantidad de hijos/cónyuge para el cálculo de utilidades y deducción del Impuesto a la Renta.
* **Información Bancaria:** Cuenta, banco y tipo de cuenta para las transferencias.

## Módulo de Asistencia
Permite llevar el control del tiempo laborado por los empleados.
* **Registro de Entradas y Salidas:** Permite digitalizar las horas de llegada y salida.
* **Cálculo de Horas:** El sistema automáticamente clasifica las horas en normales, suplementarias (sobretiempo hasta las 24:00) y extraordinarias (fines de semana, feriados o madrugada).
* **Control de Atrasos:** Calcula en minutos las demoras para su respectivo descuento si aplica.

## Módulo de Permisos y Vacaciones
Gestiona las incidencias y ausencias.
* **Tipos de Permisos:** Por calamidad doméstica, enfermedad, maternidad/paternidad, permisos sin remuneración, etc.
* **Aprobación:** Los permisos ingresan en estado "Pendiente" y el administrador debe aprobarlos ("Justificado") o rechazarlos.
* **Descuentos:** Si un permiso no es remunerado, el sistema lo deducirá automáticamente al generar el rol de pagos del mes.

## Módulo de Nómina (Roles de Pago)
Es el corazón del sistema, donde se consolidan todos los ingresos y deducciones para generar el pago mensual.
### Ingresos
* **Sueldo Base proporcial:** Según los días trabajados.
* **Horas Extras:** Calculadas según la asistencia.
* **Comisiones, Bonos y Otros Ingresos.**
### Deducciones
* **Aporte IESS (9.45%):** Calculado automáticamente sobre los ingresos de materia gravada.
* **Préstamos (Quirografarios, Hipotecarios).**
* **Anticipos y Pensiones Alimenticias.**
* **Retención en la Fuente (Impuesto a la Renta - SRI):** Proyectado y retenido según la tabla vigente.
### Provisiones y Beneficios
* **Aporte Patronal (11.15% o 12.15% según el caso).**
* **Décimo Tercer Sueldo:** Provisión mensual (1/12 de todo lo ganado).
* **Décimo Cuarto Sueldo:** Provisión mensual (1/12 del Salario Básico Unificado).
* **Fondos de Reserva:** Calculados a partir del año de trabajo en la empresa (o antes si es que hay solicitud expresa de acumulación).
* **Vacaciones:** Provisión correspondiente.

**Nota:** Los roles inician en estado "Borrador" para validación y luego pueden ser cerrados o aprobados de forma definitiva.

## Préstamos, Anticipos y Utilidades
* **Préstamos de la Empresa:** Se puede otorgar préstamos a los empleados, definiendo cuotas mensuales que se descontarán automáticamente del rol hasta cubrir el saldo.
* **Utilidades Anuales:** El sistema toma la "Utilidad Líquida" reportada por la empresa al final del año fiscal y calcula automáticamente:
  * El 10% dividido para todos los trabajadores según los días laborados.
  * El 5% distribuido en función de las cargas familiares acreditadas.

## Configuración General
Menú dedicado a mantener los parámetros legales actualizados:
* **Variables Anuales:** Salario Básico Unificado (SBU), porcentajes del IESS.
* **Tabla de Impuesto a la Renta SRI:** Permite actualizar anualmente las fracciones básicas, excesos y porcentajes impositivos dictados por el SRI para evitar errores de cálculo en las retenciones.
* **Feriados Nacionales y Locales:** Al alimentar estos días, la asistencia y horas extraordinarias se calculan correctamente cuando un empleado trabaja en dichas fechas.

## Reportes
Módulo de exportación de datos (PDF/CSV):
* Consolidado de nómina mensual.
* Desglose de liquidaciones.
* Reportes de vacaciones pendientes.
* Exportación de formato .CSV listo para el sistema de transferencias del banco ("Cash Management").

---
**Recuerde:** La información ingresada en el sistema tiene impacto legal y contable. Es fundamental revisar los "Borradores" de los roles de pago antes de considerar la información como final o emitir las transferencias.

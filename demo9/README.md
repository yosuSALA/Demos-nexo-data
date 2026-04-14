# Sistema de RRHH y Nomina - Ecuador

Sistema web integral de Recursos Humanos y Nomina parametrizado bajo el Codigo del Trabajo del Ecuador. Desarrollado con Node.js, Express, SQLite y EJS.

---

## Descripcion General

Esta aplicacion permite gestionar el ciclo completo de nomina de una empresa ecuatoriana: registro de empleados, control de asistencia, calculo automatizado de roles de pago, beneficios sociales (decimos, vacaciones, utilidades), permisos, prestamos y generacion de reportes. Todos los porcentajes y parametros legales son configurables desde la interfaz, sin necesidad de modificar codigo.

---

## Arquitectura

El proyecto sigue un patron **MVC (Modelo-Vista-Controlador)** sencillo:

| Capa | Ubicacion | Descripcion |
|------|-----------|-------------|
| **Modelo** | `src/models/` | Esquema DDL de la base de datos (SQLite) |
| **Controlador/Rutas** | `src/routes/` | Logica de cada modulo (empleados, nomina, asistencia, etc.) |
| **Servicios** | `src/services/` | Logica de negocio encapsulada (calculos de IESS, IR, beneficios) |
| **Vistas** | `views/` | Plantillas EJS renderizadas en el servidor |
| **Configuracion** | `src/config/` | Conexion a la base de datos |
| **Utilidades** | `src/utils/` | Funciones auxiliares (validacion de cedula, fechas, moneda) |

**Stack tecnologico:**

- **Backend:** Node.js / Express.js
- **Base de datos:** SQLite3 (via `better-sqlite3`, archivo local en `data/nomina.db`)
- **Frontend:** EJS (server-side rendering) + CSS + JavaScript vanilla
- **PDF:** PDFKit para generacion de recibos de pago
- **Exportacion:** json2csv para reportes bancarios
- **Sesiones:** express-session

---

## Requisitos Previos

- **Node.js** version 14 o superior (recomendada LTS)
- **npm** (incluido con Node.js)
- No se requiere instalar un motor de base de datos externo; SQLite se instala automaticamente como dependencia npm

---

## Instalacion y Ejecucion

### 1. Instalar dependencias

```bash
npm install
```

### 2. Inicializar la base de datos con datos de ejemplo

```bash
npm run seed
```

Este comando ejecuta `src/seed.js`, que crea las tablas y carga:
- Parametros de configuracion 2026 (SBU, porcentajes IESS, recargos de horas extras, etc.)
- Tabla del Impuesto a la Renta del SRI (10 tramos)
- Calendario de feriados nacionales 2026
- 3 empleados de ejemplo con distintos perfiles (contrato indefinido, plazo fijo, diferentes regiones)

### 3. Levantar el servidor de desarrollo

```bash
npm run dev
```

Utiliza `nodemon` para reiniciar automaticamente ante cambios en el codigo.

Para produccion (sin reinicio automatico):

```bash
npm start
```

### 4. Acceder a la aplicacion

Abrir en el navegador:

```
http://localhost:3000
```

---

## Funcionalidades

### Dashboard
- Resumen de empleados activos
- Costo de nomina del mes actual (ingresos, neto, aporte patronal)
- Alertas de contratos por vencer (proximos 30 dias)
- Permisos pendientes de aprobacion

### Gestion de Empleados (`/empleados`)
- Listado, creacion, edicion y desactivacion de empleados
- Datos personales, laborales y bancarios
- Validacion de cedula ecuatoriana (algoritmo modulo 10)
- Clasificacion por region (Sierra/Amazonia o Costa/Galapagos)
- Tipos de contrato: Indefinido, Plazo Fijo

### Control de Asistencia (`/asistencia`)
- Registro de entradas y salidas
- Calculo de horas normales, suplementarias y extraordinarias
- Registro de minutos de atraso

### Nomina y Roles de Pago (`/nomina`)
- Generacion individual o masiva de roles de pago mensuales
- Calculo automatico de ingresos (sueldo base, horas extras, comisiones, bonos)
- Calculo automatico de deducciones (IESS, IR, prestamos, multas, pensiones, anticipos)
- Provisiones mensuales (decimo tercero, decimo cuarto, fondos de reserva, vacaciones, aporte patronal)
- Estados de rol: Borrador, Calculado
- Decimo tercer sueldo (periodo dic-nov)
- Decimo cuarto sueldo (diferenciado por region: Costa marzo, Sierra agosto)
- Vacaciones (calculo de dias y valor monetario)
- Utilidades (15% - distribucion 10% + 5%)

### Permisos y Vacaciones (`/permisos`)
- Solicitud y aprobacion de permisos
- Tipos: Vacaciones, Enfermedad, Calamidad domestica, Maternidad/Paternidad, otros
- Control de dias disponibles vs. tomados

### Prestamos (`/configuracion`)
- Registro de prestamos quirografarios e hipotecarios
- Descuento automatico de cuotas mensuales en el rol de pago

### Configuracion (`/configuracion`)
- Parametros editables desde la interfaz web (SBU, porcentajes, jornada, etc.)
- Tabla del Impuesto a la Renta por tramos
- Catalogo de feriados

### Reportes (`/reportes`)
- Generacion de reportes en PDF y CSV
- Reportes bancarios para transferencias

---

## Estructura de Archivos

```
demo 9/
├── package.json                # Dependencias y scripts del proyecto
├── README.md                   # Este archivo
├── MANUAL_USUARIO.md           # Documentacion funcional para el usuario final
│
├── data/
│   └── nomina.db               # Base de datos SQLite (generada automaticamente)
│
├── src/
│   ├── app.js                  # Punto de entrada: servidor Express
│   ├── seed.js                 # Script de inicializacion de datos
│   │
│   ├── config/
│   │   └── database.js         # Conexion a SQLite (better-sqlite3)
│   │
│   ├── middleware/              # Middlewares de Express (autenticacion, logs)
│   │
│   ├── models/
│   │   └── schema.js           # Definicion DDL de todas las tablas
│   │
│   ├── routes/
│   │   ├── empleados.js        # CRUD de empleados
│   │   ├── asistencia.js       # Registro de asistencia
│   │   ├── nomina.js           # Roles de pago y beneficios
│   │   ├── permisos.js         # Permisos y vacaciones
│   │   ├── configuracion.js    # Parametros y prestamos
│   │   └── reportes.js         # Generacion de reportes
│   │
│   ├── services/
│   │   ├── nominaService.js    # Calculos de nomina (IESS, IR, horas extras, provisiones)
│   │   ├── beneficiosService.js # Decimos, vacaciones, utilidades
│   │   └── configService.js    # Lectura/escritura de parametros, tabla IR, feriados
│   │
│   ├── templates/              # Plantillas auxiliares (HTML base para PDFs)
│   │
│   └── utils/
│       └── validators.js       # Validacion de cedula, calculo de fechas, formato moneda
│
├── views/
│   ├── dashboard.ejs           # Tablero principal
│   ├── partials/
│   │   ├── header.ejs          # Cabecera y menu de navegacion
│   │   └── footer.ejs          # Pie de pagina
│   ├── empleados/
│   │   ├── index.ejs           # Listado de empleados
│   │   ├── form.ejs            # Formulario de creacion/edicion
│   │   └── detalle.ejs         # Ficha del empleado
│   ├── nomina/
│   │   ├── index.ejs           # Listado de roles de pago
│   │   ├── rol.ejs             # Detalle de un rol individual
│   │   ├── decimo-tercero.ejs  # Calculo de decimo tercer sueldo
│   │   ├── decimo-cuarto.ejs   # Calculo de decimo cuarto sueldo
│   │   ├── vacaciones.ejs      # Calculo de vacaciones
│   │   ├── utilidades.ejs      # Calculo y registro de utilidades
│   │   └── utilidades-detalle.ejs # Desglose individual de utilidades
│   ├── asistencia/
│   │   └── index.ejs           # Registro y consulta de asistencia
│   ├── permisos/
│   │   └── index.ejs           # Gestion de permisos
│   ├── configuracion/
│   │   ├── index.ejs           # Parametros del sistema
│   │   └── prestamos.ejs       # Gestion de prestamos
│   └── reportes/
│       └── index.ejs           # Generacion de reportes
│
└── public/
    ├── css/
    │   └── styles.css          # Estilos globales
    └── js/
        └── app.js              # JavaScript del lado del cliente
```

---

## Modelo de Base de Datos

| Tabla | Descripcion |
|-------|-------------|
| `configuracion` | Parametros del sistema (SBU, porcentajes IESS, jornada, etc.) |
| `tabla_ir` | Tramos del Impuesto a la Renta por anio fiscal (SRI) |
| `empleados` | Datos maestros de trabajadores |
| `asistencia` | Registros diarios de entrada, salida, horas extras y atrasos |
| `permisos` | Solicitudes de vacaciones, permisos y licencias |
| `roles_pago` | Cabecera de nomina mensual con todos los rubros |
| `prestamos` | Prestamos quirografarios e hipotecarios activos |
| `utilidades` | Cabecera del reparto anual de utilidades (15%) |
| `utilidades_detalle` | Desglose individual por empleado |
| `feriados` | Catalogo de dias festivos nacionales |

---

## Reglas de Negocio - Legislacion Laboral Ecuatoriana

A continuacion se describen las reglas de calculo implementadas, basadas en el Codigo del Trabajo del Ecuador:

### Salario Basico Unificado (SBU)
- Valor 2026: **$470.00** (configurable)
- Ningun trabajador en relacion de dependencia puede percibir menos del SBU

### Aportes al IESS
- **Aporte personal:** 9.45% sobre el total de ingresos (descuento al empleado)
- **Aporte patronal:** 11.15% sobre el total de ingresos (costo del empleador)
- **Fondos de reserva:** 8.33% del sueldo, aplica a partir del mes 13 de servicio continuo

### Horas Extras
- **Horas suplementarias:** recargo del 50% sobre el valor hora normal (lunes a viernes, despues de la jornada)
- **Horas extraordinarias:** recargo del 100% sobre el valor hora normal (sabados, domingos, feriados)
- Valor hora normal = sueldo base / 240 (30 dias x 8 horas)

### Jornada Laboral
- **Diaria:** 8 horas
- **Semanal:** 40 horas

### Impuesto a la Renta
- Calculo anual proyectado, retenido mensualmente (1/12 del impuesto anual)
- Base imponible = ingreso anual - aporte IESS anual - gastos personales
- Aplicacion de tabla progresiva del SRI con 10 tramos
- Gastos personales deducibles hasta $18,800.00

### Decimo Tercer Sueldo (Bono Navideno)
- Equivale a la doceava parte del total percibido en el periodo
- **Periodo de calculo:** 1 de diciembre del anio anterior al 30 de noviembre del anio actual
- Proporcional si el empleado no completo el periodo

### Decimo Cuarto Sueldo (Bono Escolar)
- Equivale a un SBU, proporcional a los dias trabajados
- **Periodo Costa/Galapagos:** marzo del anio anterior a febrero del anio actual (pago en marzo)
- **Periodo Sierra/Amazonia:** agosto del anio anterior a julio del anio actual (pago en agosto)

### Vacaciones
- **Base:** 15 dias calendario por anio de servicio
- **Dias adicionales:** a partir del 5to anio, se suma 1 dia extra por cada anio adicional (maximo 15 dias adicionales)
- Valor diario = sueldo base / 30

### Utilidades (15%)
- Distribucion obligatoria del 15% de las utilidades liquidas de la empresa
- **10%** se reparte equitativamente entre todos los trabajadores, proporcional a los dias trabajados en el anio
- **5%** se reparte proporcional a las cargas familiares de cada trabajador

### Provisiones Mensuales
El sistema calcula y registra las siguientes provisiones cada mes:
- Decimo tercero: total ingresos / 12
- Decimo cuarto: SBU / 12
- Vacaciones: (sueldo base x 15) / 360
- Fondos de reserva: 8.33% del sueldo (desde el mes 13)
- Aporte patronal: 11.15% del total de ingresos

### Multas por Atraso
- Descuento proporcional al tiempo de atraso
- Valor minuto = (sueldo base / 240) / 60

---

## Datos de Ejemplo (Seed)

El script de inicializacion carga 3 empleados con perfiles variados:

| Cedula | Nombre | Cargo | Sueldo | Contrato | Region |
|--------|--------|-------|--------|----------|--------|
| 1712345678 | Maria Jose Garcia Lopez | Analista de Sistemas | $1,200.00 | Indefinido | Sierra/Amazonia |
| 0912345678 | Carlos Andres Perez Morales | Contador General | $1,800.00 | Indefinido | Costa/Galapagos |
| 1812345678 | Ana Lucia Rodriguez Silva | Asistente Administrativa | $550.00 | Plazo Fijo | Sierra/Amazonia |

---

## Scripts Disponibles

| Comando | Descripcion |
|---------|-------------|
| `npm install` | Instala todas las dependencias |
| `npm run seed` | Inicializa la base de datos con configuracion y datos de ejemplo |
| `npm run dev` | Inicia el servidor con nodemon (reinicio automatico) |
| `npm start` | Inicia el servidor en modo produccion |

---

## Notas Tecnicas

- La base de datos SQLite se almacena en `data/nomina.db` y se crea automaticamente al iniciar la aplicacion.
- Los porcentajes y parametros legales se leen dinamicamente de la tabla `configuracion`, por lo que pueden ajustarse sin modificar codigo cuando cambien las normativas.
- La moneda utilizada es el dolar estadounidense (USD), moneda oficial del Ecuador.
- La validacion de cedula implementa el algoritmo oficial de modulo 10 del Registro Civil ecuatoriano.

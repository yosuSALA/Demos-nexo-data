# Motor Analítico ETL - SuperCías

## Manual de Usuario

**Versión:** 1.0
**Fecha:** Marzo 2026
**Destinatario:** Gerencia Financiera — Trust Fiduciaria S.A.
**Clasificación:** Uso interno

---

## Tabla de Contenidos

1. [Introducción](#1-introducción)
2. [Descripción General del Sistema](#2-descripción-general-del-sistema)
3. [Requisitos Previos](#3-requisitos-previos)
4. [Inicio de la Aplicación](#4-inicio-de-la-aplicación)
5. [Descripción de la Interfaz](#5-descripción-de-la-interfaz)
6. [Instrucciones de Uso](#6-instrucciones-de-uso)
7. [Salida del Sistema — Base de Datos para Power BI](#7-salida-del-sistema--base-de-datos-para-power-bi)
8. [Programación de Ejecución Automática Mensual](#8-programación-de-ejecución-automática-mensual)
9. [Preguntas Frecuentes](#9-preguntas-frecuentes)
10. [Soporte Técnico](#10-soporte-técnico)

---

## 1. Introducción

La Superintendencia de Compañías, Valores y Seguros del Ecuador (Super Cías) publica periódicamente los balances financieros de todas las sociedades bajo su control. Esta información pública, que supera los **15 millones de registros**, constituye una fuente de inteligencia competitiva de alto valor para el sector fiduciario.

Sin embargo, el volumen y formato crudo de estos datos los hace inaccesibles para análisis directo. Descargar, limpiar, filtrar y estructurar esta información de forma manual requeriría semanas de trabajo técnico.

El **Motor Analítico ETL - SuperCías** resuelve este problema. Es una herramienta de escritorio desarrollada específicamente para Trust Fiduciaria S.A. que **automatiza por completo** el proceso de:

- **Extracción** de los archivos de datos públicos de la Super Cías.
- **Transformación** y limpieza de más de 15 millones de registros (normalización de fechas, RUCs, formatos numéricos ecuatorianos y códigos de cuentas NIIF).
- **Filtrado inteligente** que aísla automáticamente las empresas clasificadas como *"Administradora de Fondos y Fideicomisos"*, el sector de interés directo de la firma.
- **Carga** de los datos consolidados en una base de datos analítica optimizada, lista para conectar a Power BI en menos de 2 minutos.

El resultado es un archivo de base de datos compacto y estructurado que permite a la Gerencia Financiera analizar balances, comparar competidores del sector fiduciario, calcular indicadores financieros y generar reportes ejecutivos directamente desde Power BI, sin depender de procesos manuales ni del área de tecnología.

---

## 2. Descripción General del Sistema

El sistema opera en cuatro etapas secuenciales, ejecutadas automáticamente con un solo clic:

| Etapa | Descripción | Duración aprox. |
|-------|-------------|-----------------|
| **1. Extracción** | Lee el archivo de datos de la Super Cías (formato CSV/TSV, millones de filas) en bloques de memoria controlados. | ~20 seg |
| **2. Transformación** | Limpia formatos numéricos ecuatorianos (ej: `1.188.854,66`), normaliza fechas a estándar ISO, valida RUCs de 13 dígitos y clasifica cuentas contables según la jerarquía NIIF. | ~40 seg |
| **3. Filtrado** | Aplica automáticamente el filtro del sector *"Administradora de Fondos y Fideicomisos"* para retener únicamente las empresas relevantes. Opcionalmente, cruza contra el catálogo NIIF de la firma y códigos CIIU específicos. | ~10 seg |
| **4. Carga** | Inserta los datos limpios en una base de datos DuckDB con esquema estrella (Star Schema) optimizado para Power BI. Genera vistas analíticas precalculadas (KPIs, rankings, tendencias). | ~20 seg |

**Tiempo total de ejecución:** inferior a 2 minutos para la carga completa de toda la información histórica.

### Arquitectura del Motor

```
  Archivo Super Cías          Motor ETL              Salida
  (CSV/TSV, 15M+ filas)       (Polars + DuckDB)      (Base de datos .duckdb)

  ┌──────────────┐     ┌──────────────────────┐     ┌─────────────────┐
  │  Datos crudos │────>│  Extracción          │     │  dim_date       │
  │  de la Super  │     │  Transformación      │────>│  dim_company    │
  │  Cías         │     │  Filtrado sector     │     │  dim_account    │
  └──────────────┘     │  fiduciario          │     │  dim_sector     │
                        │  Carga en DuckDB     │     │  financial_fact │
                        └──────────────────────┘     └────────┬────────┘
                                                              │
                                                              v
                                                     ┌─────────────────┐
                                                     │   Power BI      │
                                                     │   Dashboards    │
                                                     └─────────────────┘
```

---

## 3. Requisitos Previos

| Componente | Especificación |
|------------|----------------|
| **Sistema operativo** | Windows 10 u 11 (64 bits) |
| **Memoria RAM** | 8 GB mínimo (16 GB recomendado) |
| **Espacio en disco** | 2 GB libres para los datos procesados |
| **Software adicional** | Power BI Desktop (para visualización de resultados) |
| **Archivo de datos** | Archivo CSV o TSV descargado del portal de la Super Cías |

> **Nota:** La aplicación se entrega como un ejecutable independiente (`ETL_SuperCias.exe`). No requiere instalación de Python ni de ningún componente adicional.

---

## 4. Inicio de la Aplicación

1. Ubique el archivo **`ETL_SuperCias.exe`** en la carpeta de trabajo asignada por el equipo técnico.
2. Haga **doble clic** sobre el archivo para abrir la aplicación.
3. La ventana principal se mostrará con el título:

   **"Controlador ETL — Super Cías — Fiducia Consulting Group"**

4. En la parte superior encontrará indicadores de estado:
   - **Última carga:** fecha del último procesamiento exitoso.
   - **Registros:** cantidad total de registros en la base de datos actual.
   - **DB:** ruta del archivo de base de datos activo.

---

## 5. Descripción de la Interfaz

La interfaz está organizada en cinco secciones verticales, cada una claramente delimitada:

### 5.1 Encabezado

Muestra el nombre del sistema, el logotipo y un selector de **tema visual** (oscuro, claro o del sistema). El tema es una preferencia cosmética que no afecta el funcionamiento.

### 5.2 Rutas de Archivos

Dos campos que definen la entrada y la salida del proceso:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **Archivo de origen (CSV/TSV)** | El archivo de datos descargado del portal de la Super Cías. | `C:\Datos\balances_supercias_2025.tsv` |
| **Base de datos DuckDB** | Ruta donde se guardará (o actualizará) la base de datos de salida. | `output\supercias.duckdb` |

Cada campo tiene un botón **"Explorar"** que abre el explorador de archivos de Windows para seleccionar la ruta de forma visual.

### 5.3 Filtros — Generación de Base Optimizada vs. Completa

Esta sección controla qué datos se incluyen en la base de datos resultante. Se presentan dos opciones excluyentes:

**Opción A — Generar BD Optimizada** *(recomendada para uso diario)*

Produce una base de datos que contiene **únicamente** las empresas del sector fiduciario. El sistema aplica automáticamente el filtro por tipo de entidad *"Administradora de Fondos y Fideicomisos"*. Además, permite refinar el resultado con:

- **Códigos CIIU:** Filtra por actividad económica (ej: `K6511, K6530`). Ingrese los códigos separados por coma.
- **Catálogo de cuentas NIIF:** Seleccione el archivo Excel, YAML o JSON con el catálogo contable de Trust Fiduciaria S.A. El sistema cruzará las cuentas del balance contra este catálogo y retendrá solo las relevantes.

**Opción B — Generar BD Completa**

Procesa **todos** los registros de la Super Cías sin ningún filtro. Esta opción genera un archivo considerablemente más grande y tarda más tiempo. Se recomienda solo para análisis comparativos con sectores fuera del fiduciario.

> **Recomendación:** Para el uso habitual de la Gerencia Financiera, seleccione siempre **"Generar BD Optimizada"**. El archivo resultante será más liviano y las consultas en Power BI responderán más rápido.

### 5.4 Programación — Ejecución Automática Mensual

Permite configurar la ejecución automática del proceso para que se actualice mensualmente sin intervención manual. Se detalla en la [Sección 8](#8-programación-de-ejecución-automática-mensual).

### 5.5 Ejecución Manual

La sección central de operación. Contiene:

- El botón principal **"Ejecutar Actualización Ahora"**.
- Una **barra de progreso** que indica visualmente el avance del proceso.
- Una **etiqueta de estado** que describe la etapa actual (ej: *"Bloque 5/30 — Transformando formatos numéricos..."*).
- Un **cuadro de resumen** que, al finalizar, muestra las métricas de la ejecución.

---

## 6. Instrucciones de Uso

### 6.1 Ejecución Estándar — Actualización Manual

Siga estos pasos para ejecutar una actualización de la base de datos:

**Paso 1 — Seleccionar el archivo de datos**

En la sección *"Rutas de Archivos"*, haga clic en **"Explorar"** junto al campo *"Archivo de origen"*. Navegue hasta la ubicación del archivo CSV o TSV descargado de la Super Cías y selecciónelo.

**Paso 2 — Verificar la ruta de la base de datos**

El campo *"Base de datos DuckDB"* muestra la ruta donde se almacenará el resultado. La ruta predeterminada (`output/supercias.duckdb`) es la correcta para uso normal. Modifíquela solo si el equipo técnico se lo indica.

**Paso 3 — Confirmar el modo de generación**

En la sección *"Filtros"*, confirme que la opción **"Generar BD Optimizada"** esté seleccionada. Esta es la configuración recomendada.

**Paso 4 — Ejecutar**

Pulse el botón azul **"Ejecutar Actualización Ahora"**.

El sistema comenzará a procesar. Observe lo siguiente durante la ejecución:

- El botón cambiará su texto a **"Ejecutando..."** y se deshabilitará para evitar ejecuciones duplicadas.
- La **barra de progreso** avanzará de izquierda a derecha.
- La **etiqueta de estado** mostrará mensajes como:
  - *"Inicializando conexión DuckDB..."*
  - *"Aplicando filtro Regex: Administradora de Fondos y Fideicomisos..."*
  - *"Bloque 5/10 — Cruzando contra catálogo NIIF..."*
  - *"Generando vistas analíticas optimizadas..."*

> **Importante:** La aplicación permanece **completamente funcional** durante el procesamiento. Puede minimizarla o continuar trabajando en otras aplicaciones. El proceso se ejecuta en segundo plano sin bloquear la interfaz.

**Paso 5 — Revisar el resultado**

Al finalizar, el cuadro de resumen mostrará un reporte como el siguiente:

```
══════════════════════════════════════════════════
  RESUMEN DE EJECUCIÓN ETL
══════════════════════════════════════════════════
  Filas leídas      :   15,600,000
  Filas cargadas    :    2,145,320
  Filas descartadas :   13,454,680
  Duración          :         87.3 seg
══════════════════════════════════════════════════
  Fecha: 2026-03-18 09:15:42
```

Los valores clave a verificar:

| Métrica | Significado |
|---------|-------------|
| **Filas leídas** | Total de registros en el archivo de origen. |
| **Filas cargadas** | Registros que pasaron los filtros y fueron almacenados. |
| **Filas descartadas** | Registros de otros sectores, excluidos por el filtro. |
| **Duración** | Tiempo total del procesamiento. |

**Paso 6 — Guardar configuración**

Pulse el botón verde **"Guardar Configuración"** en la parte inferior de la ventana. Esto almacenará todas las rutas y preferencias para que en la próxima ejecución no necesite volver a configurarlas.

### 6.2 Actualización Incremental (Motor de Actualización)

El sistema implementa un mecanismo de **marca de agua alta** (*High-Water Mark*). Esto significa que:

- La primera ejecución carga todos los datos históricos disponibles.
- Las ejecuciones posteriores **solo cargan los datos nuevos** que no existían en la base de datos.
- Los registros duplicados se descartan automáticamente.

No necesita hacer nada especial para activar este comportamiento. El motor detecta automáticamente cuáles datos ya fueron procesados consultando la fecha más reciente registrada en la base.

---

## 7. Salida del Sistema — Base de Datos para Power BI

### 7.1 Archivo Generado

El resultado del proceso es un único archivo con extensión **`.duckdb`**, ubicado en la ruta configurada (por defecto: `output/supercias.duckdb`).

Este archivo es una **base de datos analítica completa** que contiene:

| Componente | Descripción |
|------------|-------------|
| **dim_date** | Dimensión calendario con año fiscal, trimestre, semestre y tipo de período. |
| **dim_company** | Dimensión de empresas con RUC, razón social y sector al que pertenecen. |
| **dim_account** | Dimensión de cuentas contables NIIF con jerarquía completa (clase, grupo, subgrupo). |
| **dim_sector** | Dimensión de sectores económicos con código y nombre. |
| **financial_fact** | Tabla de hechos con cada registro financiero reportado: empresa, cuenta, fecha, período y valor monetario. |

Adicionalmente, el sistema genera **vistas analíticas precalculadas** (marts) que aceleran las consultas más comunes:

| Vista | Contenido |
|-------|-----------|
| **Resumen anual** | Totales por empresa y año. |
| **Activos vs. Pasivos** | Comparación estructural del balance. |
| **Categorías de cuentas** | Agrupación por clase contable NIIF. |
| **Ranking de empresas** | Ordenamiento por tamaño de activos, ingresos o patrimonio. |
| **Indicadores financieros (KPIs)** | Liquidez, endeudamiento, rentabilidad y otros ratios precalculados. |
| **Detección de anomalías** | Identificación de variaciones atípicas entre períodos. |

### 7.2 Conexión con Power BI

Para conectar Power BI al archivo generado:

1. Abra **Power BI Desktop**.
2. Seleccione **Obtener datos** > **Más...** > busque **"DuckDB"**.
   *(Si no aparece el conector nativo, utilice el conector ODBC de DuckDB disponible en duckdb.org).*
3. En la ruta de conexión, ingrese la ruta completa del archivo, por ejemplo:

   ```
   C:\Datos\ETL-Supercias\output\supercias.duckdb
   ```

4. Power BI mostrará las tablas y vistas disponibles. Seleccione las que necesite:
   - Para dashboards de alto nivel: seleccione las vistas analíticas (marts).
   - Para análisis detallado: conecte directamente a `financial_fact` junto con las dimensiones.

5. El modelo estrella ya está optimizado con claves foráneas y jerarquías. Power BI detectará automáticamente las relaciones entre tablas.

### 7.3 Tamaño Estimado del Archivo

| Modo de generación | Registros aprox. | Tamaño en disco |
|--------------------|-------------------|-----------------|
| **BD Optimizada** (sector fiduciario) | ~2 millones | ~150–300 MB |
| **BD Completa** (todos los sectores) | ~15 millones | ~1.2–1.8 GB |

---

## 8. Programación de Ejecución Automática Mensual

La Super Cías actualiza sus datos periódicamente. Para mantener la base de datos al día sin intervención manual, el sistema ofrece dos mecanismos de programación:

### 8.1 Programación desde la Aplicación

En la sección *"Programación — Ejecución Automática Mensual"*:

1. Seleccione el **día del mes** en que desea que se ejecute la actualización (ej: día 5).
2. Ingrese la **hora** en formato HH:MM (ej: `09:00`).
3. Active el interruptor **"Activar programación"**.

El estado cambiará a: **"Activo — Día 5 de cada mes a las 09:00"**.

> **Limitación:** Esta programación solo funciona mientras la aplicación esté abierta. Si cierra la ventana, la ejecución programada no se disparará.

### 8.2 Programación Permanente con Windows Task Scheduler *(recomendada)*

Para garantizar que la actualización se ejecute aunque el equipo esté encendido pero la aplicación cerrada:

1. Configure el día y hora deseados en la sección de programación.
2. Pulse el botón **"Copiar Comando Task Scheduler"**.
3. El sistema copiará al portapapeles un comando listo para usar.
4. Abra una **terminal de Windows como Administrador** (clic derecho sobre el ícono de Símbolo del sistema o PowerShell > "Ejecutar como administrador").
5. Pegue el comando (Ctrl+V) y presione Enter.

Windows creará una tarea programada llamada **"ETL_SuperCias_Mensual"** que se ejecutará automáticamente en la fecha y hora configuradas, incluso si la aplicación no está abierta.

> **Requisito:** El equipo debe estar encendido (no en suspensión) en el momento programado. Coordine con el equipo de sistemas si es necesario.

---

## 9. Preguntas Frecuentes

**P: ¿Qué sucede si ejecuto el proceso dos veces con el mismo archivo de datos?**
R: Nada negativo. El motor detecta registros duplicados y los descarta automáticamente. Solo se cargarán los datos que no existan previamente en la base.

**P: ¿Puedo seguir usando mi computador mientras el proceso se ejecuta?**
R: Sí. El procesamiento se ejecuta en segundo plano. La interfaz permanece funcional y puede minimizar la aplicación sin afectar el proceso.

**P: ¿Qué pasa si el proceso falla o se interrumpe a la mitad?**
R: Los datos cargados hasta el punto de interrupción se conservan en la base de datos. Simplemente vuelva a ejecutar el proceso; el motor retomará donde se quedó gracias al mecanismo de marca de agua alta.

**P: ¿Por qué se descartan tantas filas en modo "BD Optimizada"?**
R: El archivo de la Super Cías contiene datos de **todos** los sectores económicos del Ecuador. El filtro automático retiene únicamente las empresas clasificadas como "Administradora de Fondos y Fideicomisos", que representan una fracción del total. Las filas descartadas corresponden a empresas de otros sectores.

**P: ¿Necesito descargar manualmente el archivo de la Super Cías?**
R: Sí. En esta versión, el archivo de datos debe descargarse previamente desde el portal de la Super Cías y seleccionarse en la aplicación. La descarga automática está planificada para una versión futura.

**P: ¿Cómo sé si mi base de datos ya está actualizada?**
R: En el encabezado de la aplicación, el indicador **"Última carga"** muestra la fecha del dato más reciente almacenado. Compárela con la fecha de publicación del archivo de la Super Cías.

**P: ¿Puedo abrir el archivo .duckdb con Excel?**
R: No directamente. El archivo `.duckdb` es una base de datos analítica diseñada para ser consultada desde Power BI u otras herramientas de BI. Para análisis puntuales en Excel, utilice la funcionalidad de exportación de Power BI.

---

## 10. Soporte Técnico

Para asistencia con el sistema, contacte al equipo de desarrollo:

| Canal | Detalle |
|-------|---------|
| **Soporte de primer nivel** | Equipo de datos — Trust Fiduciaria S.A. |
| **Correo** | *(por definir)* |
| **Horario** | Lunes a viernes, 08:00 a 17:00 |

**Información a incluir al reportar un problema:**

1. Captura de pantalla de la aplicación mostrando el mensaje de error.
2. El archivo de registro `etl.log` ubicado en la carpeta de la aplicación.
3. El nombre y tamaño del archivo de datos utilizado.
4. La fecha y hora en que ocurrió el problema.

---

*Documento elaborado para Trust Fiduciaria S.A. — Marzo 2026*
*Motor Analítico ETL - SuperCías v1.0*

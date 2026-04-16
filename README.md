# NEXO DATA CONSULTING - Catálogo de Demos

Catálogo de demos técnicas y productos automatizados de Nexo Data Consulting para el mercado de Guayaquil, Ecuador (2026).

> **📅 Última actualización:** 13 de Abril de 2026
>
> **Nota:** Todos los avances y la consolidación técnica del catálogo realizados este día fueron iniciados y liderados por **Josue** con el apoyo de **Antigravity**.

## 🌐 Demos en Vivo (Acceso Tailscale)

> Conéctate a la red Tailscale de Nexo Data para acceder a las apps en tiempo real.
> IP del servidor: `100.108.226.8`

| # | Demo | Enlace |
|---|------|--------|
| 4 | Bot de conciliación bancaria | [http://100.108.226.8:8504](http://100.108.226.8:8504) |
| 8 | Monitor de vencimiento de contratos | [http://100.108.226.8:8508](http://100.108.226.8:8508) |
| 9 | Portal de asistencia de empleados (RRHH) | [http://100.108.226.8:3000](http://100.108.226.8:3000) |
| 10 | Cotizador inteligente con IA | [http://100.108.226.8:8505](http://100.108.226.8:8505) |
| 12 | Dashboard de cartera vencida | [http://100.108.226.8:8502](http://100.108.226.8:8502) |
| 13 | Scraper de precios de competencia | [http://100.108.226.8:8503](http://100.108.226.8:8503) |
| 14 | App de evaluación de desempeño 360° | [http://100.108.226.8:3001](http://100.108.226.8:3001) |
| 15 | Chatbot de consultas internas con IA | [http://100.108.226.8:8506](http://100.108.226.8:8506) |

---

## 🚀 Estado del Portafolio de Demos

| # | Demo / Producto | Estado | Responsable |
|---|-----------------|--------|-------------|
| 1 | Bot descarga y cruce SRI | 🟡 En Desarrollo | [CHACHA] / Josue |
| 2 | Dashboard financiero ejecutivo | 🔴 Pendiente | Mathew / Josue |
| 3 | Reporte PDF automático mensual | 🟡 Pulido Final | Josue |
| 4 | Bot de conciliación bancaria | ✅ Hecho | [CHAHCA] / Josue |
| 5 | Dashboard de ventas en tiempo real | 🟡 Falta UI | Mathew / [CHACHA] |
| 6 | Generador automático de ATS (SRI) | ✅ Hecho | Josue |
| 7 | Bot envío masivo de reportes por email | ✅ Hecho | [Amigo BG] (Danilo) / Josue |
| 8 | Monitor de vencimiento de contratos | ✅ Hecho | Mathew / Josue |
| 9 | Portal de asistencia de empleados (RRHH) | ✅ Hecho | Andrés / Josue |
| 10 | Cotizador inteligente con IA | ✅ Hecho | Josue |
| 11 | ETL automático SUPERCIAS + dashboard | ✅ Hecho | Josue / Mathew |
| 12 | Dashboard de cartera vencida | ✅ Hecho | Mathew / Josue |
| 13 | Scraper de precios de competencia | ✅ Hecho | [cHACHA] / Josue |
| 14 | App de evaluación de desempeño 360° | 🟡 En Desarrollo | Andrés |
| 15 | Chatbot de consultas internas con IA | ✅ Hecho | Josue |
| 16 | Predicción de ventas y demanda (ML) | 🔴 Pendiente | Nexo Team |

## 📁 Estructura del Repositorio

- `demo4/`: Bot de conciliación bancaria.
- `demo6/`: Generador Automático de ATS y Anexos SRI.
- `demo7/`: Bot de envío masivo de estados de cuenta/reportes por email.
- `demo8/`: Sistema de monitoreo de contratos y alertas.
- `demo9/`: Portal web de asistencia RRHH con geolocalización.
- `demo10/`: Generador de cotizaciones inteligentes con IA.
- `Demo11/`: Integración con SUPERCIAS y Dashboard sectorial.
- `demo12/`: Análisis visual de morosidad y cartera vencida.
- `demo13/`: Scraper automatizado de precios competitivos.
- `demo15/`: Asistente de consultas internas (RAG) con IA.

## 📋 Asignación de Tareas y Pendientes (Roadmap 2026)

Este listado detalla las responsabilidades inmediatas. **Meta Semana 3:** Eliminar todos los estados en "Rojo". Se debe aplicar la estética **Premium / Dark Mode** en todas las interfaces web.

### 🎯 Josue (Líder / Danilo)
- **[URGENTE] Nexo Hub:** Liderar la implementación de la Landing Page principal.
- **Demo #3 (Reportes PDF):** Estandarizar el motor de plantillas HTML y asegurar que el generador sea multi-empresa.
- **Revisión General:** Auditoría estética de todas las demos antes de presentarlas a clientes C-Level.

### 📊 Mathew (Atraso Crítico - Prioridad Máxima)
- **Demo #2 (Dashboard Ejecutivo):** Crear estructura base en `demo2/app.py`. Debe incluir P&L, Burn Rate y EBITDA (Look Premium).
- **Demo #5 (Ventas):** Finalizar la UI en Streamlit. Los datos ya existen, falta la visualización de alto impacto.
- **Tarea de Revisión:** Auditar la **Demo #12** y actualizar su CSS para que coincida con el nuevo diseño Dark Mode de la Demo 8.

### 🛠️ [CHACHA]
- **Demo #13 (Scraper):** Corregir errores de lógica en la extracción y mejorar el contraste de la tabla comparativa.
- **Demo #1 (Bot SRI):** Modularizar el código para permitir descargas masivas por rango de fechas (con manejo automático de errores).
- **Tarea de Revisión:** Testear la **Demo #6** (SRI/ATS) con datos reales y verificar que el XML generado sea válido en el validador del SRI.

### 👤 Andrés
- **Demo #14 (Evaluación 360°):** Finalizar el módulo de "Resultados Individuales" y la vista de "Radar Chart" para las competencias.
- **Demo #9 (Portal RRHH):** Optimizar la carga del mapa de geolocalización y corregir el responsivo en móviles.
- **Tarea de Revisión:** Revisar todos los `README.md` de las demos técnicas (1, 4, 6, 13) y simplificar el lenguaje para que sea entendible por un gerente no-técnico.

### 🐳 Nexo Team (Infraestructura)
- **Dockerización:** Cada miembro debe crear su `Dockerfile` siguiendo el estándar del equipo.
- **Tailscale:** Asegurar la disponibilidad 24/7 del servidor `100.101.185.36`.

---
**Nexo Data Consulting**
*Conectamos tus datos con decisiones inteligentes.*
Guayaquil, Ecuador · 2026




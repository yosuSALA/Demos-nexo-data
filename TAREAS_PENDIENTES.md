# TAREAS PENDIENTES — Nexo Data Consulting
> Fecha: 2026-04-27 | Meta: Portafolio listo para propuesta a clientes

---

## 🔴 BLOQUEANTES CRÍTICOS (sin esto no hay propuesta)

### Demo #2 — Dashboard Ejecutivo Financiero
- [ ] Crear `demo2/app.py` con estructura base Streamlit
- [ ] Implementar métricas: P&L, Burn Rate, EBITDA
- [ ] Aplicar estética Dark Mode Premium (ver demo8 como referencia)
- **Responsable:** Mathew / Josue  
- **Estado actual:** 🔴 Cero avance

### Demo #14 — Evaluación de Desempeño 360°
- [ ] Finalizar módulo "Resultados Individuales"
- [ ] Implementar vista Radar Chart de competencias
- [ ] Completar flujo de encuestas (inicio → resultados)
- **Responsable:** Andrés  
- **Estado actual:** 🟡 En Desarrollo

---

## 🟡 EN PROGRESO (requieren cierre)

### Demo #1 — Bot de Descarga y Cruce SRI
- [ ] Modularizar código para descargas masivas por rango de fechas
- [ ] Implementar manejo automático de errores
- [ ] Validar autenticación automática con SRI
- **Responsable:** [CHACHA] / Josue

### Demo #3 — Reporte PDF Automático Mensual
- [ ] Estandarizar motor de plantillas HTML
- [ ] Hacer generador multi-empresa (no hardcoded)
- [ ] Prueba final con datos reales de 3 empresas distintas
- **Responsable:** Josue

### Demo #5 — Dashboard de Ventas en Tiempo Real
- [ ] Construir UI en Streamlit (datos ya existen en repo)
- [ ] Agregar visualizaciones de alto impacto (trend, top productos, mapa)
- [ ] Aplicar estética Dark Mode
- **Responsable:** Mathew / [CHACHA]

### Demo #13 — Scraper de Precios de Competencia
- [ ] Corregir errores de lógica en extracción
- [ ] Mejorar contraste y legibilidad de tabla comparativa
- [ ] Prueba con 5 URLs de competidores reales
- **Responsable:** [CHACHA] / Josue

---

## 🔵 PENDIENTE INICIO

### Landing Page — Nexo Hub
- [ ] Implementar según especificaciones en `prompt_landing_page_nexo.md`
- [ ] Estética Premium / Dark Mode
- [ ] Secciones: Hero, Catálogo de demos, Contacto, Casos de uso
- **Responsable:** Josue / Danilo

---

## ✅ REVISIÓN Y PULIDO (demos "hechas" pero necesitan auditoría)

| Demo | Tarea de Revisión | Responsable |
|------|-------------------|-------------|
| #6 (ATS SRI) | Testear con datos reales, validar XML en portal SRI | [CHACHA] |
| #9 (Portal RRHH) | Optimizar carga mapa, corregir responsivo móvil | Andrés |
| #12 (Cartera Vencida) | Actualizar CSS a Dark Mode (referencia: demo8) | Mathew |
| Todos los README | Simplificar lenguaje para gerentes no-técnicos (demos 1,4,6,13) | Andrés |
| Todas las UI web | Auditoría estética Dark Mode Premium antes de presentar a C-Level | Josue |

---

## 🐳 INFRAESTRUCTURA

### Dockerización
- [ ] Crear `Dockerfile` estándar para cada demo (cada responsable lo hace)
- [ ] Definir `docker-compose.yml` en raíz del repo
- [ ] Probar stack completo levantando todos los servicios
- **Responsable:** Nexo Team

### Tailscale (acceso interno)
- [ ] Verificar disponibilidad 24/7 servidor `100.108.226.8`
- [ ] Confirmar que todos los puertos estén activos y accesibles
- **Puertos activos:** 8502, 8503, 8504, 8505, 8506, 8508, 3000, 3001

---

## 🌐 CLOUDFLARE — Acceso Público para Clientes

> **Pendiente hasta que todas las demos estén completas y auditadas.**  
> Activar este paso DESPUÉS de marcar completo el bloque anterior.

### Setup por demo (un tunnel por servicio)

```bash
# Instalar cloudflared en servidor
curl -L https://pkg.cloudflare.dev/cloudflare-repo.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloudflare-main.gpg
# Autenticar con cuenta Nexo Data
cloudflared tunnel login
# Crear tunnel
cloudflared tunnel create nexo-demos
```

| Demo | Puerto local | Subdominio propuesto | Estado |
|------|-------------|----------------------|--------|
| #4 Conciliación bancaria | 8504 | demo4.nexodata.com.ec | ⏳ Pendiente |
| #8 Monitor contratos | 8508 | demo8.nexodata.com.ec | ⏳ Pendiente |
| #9 Portal RRHH | 3000 | demo9.nexodata.com.ec | ⏳ Pendiente |
| #10 Cotizador IA | 8505 | demo10.nexodata.com.ec | ⏳ Pendiente |
| #12 Cartera vencida | 8502 | demo12.nexodata.com.ec | ⏳ Pendiente |
| #13 Scraper precios | 8503 | demo13.nexodata.com.ec | ⏳ Pendiente |
| #14 Evaluación 360° | 3001 | demo14.nexodata.com.ec | ⏳ Pendiente |
| #15 Chatbot IA | 8506 | demo15.nexodata.com.ec | ⏳ Pendiente |

### Checklist antes de publicar cada enlace

- [ ] Demo pasa prueba funcional completa
- [ ] UI auditada (Dark Mode, sin textos cortados, responsivo)
- [ ] README actualizado con lenguaje para no-técnicos
- [ ] Tunnel activo y URL pública confirmada
- [ ] Enlace añadido al README.md principal (reemplazar IPs Tailscale)

---

## 📋 CHECKLIST FINAL — "Listo para propuesta a clientes"

Marcar cuando el portafolio completo esté listo:

- [ ] Demo #2 funcionando con datos reales
- [ ] Demo #14 flujo completo operativo
- [ ] Demo #1 modular y sin errores
- [ ] Demo #3 multi-empresa
- [ ] Demo #5 UI de alto impacto
- [ ] Demo #13 sin fallos visuales ni lógicos
- [ ] Landing Page Nexo Hub publicada
- [ ] Todas las demos auditadas estética Dark Mode
- [ ] Dockerización completa
- [ ] **Tunnels Cloudflare activos** — URLs públicas listas
- [ ] README.md actualizado con nuevos enlaces públicos (no más IPs Tailscale)
- [ ] Catálogo `Catalogo_Demos_Nexo_Data.docx` actualizado con URLs finales

---

> **Regla:** No presentar propuesta a cliente hasta que los ítems del checklist final estén todos marcados.

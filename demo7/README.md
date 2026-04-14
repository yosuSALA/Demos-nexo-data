# Demo 7 — Nexo RRHH: Sistema de Envío Masivo de Reportes 🇪🇨

![Backend](https://img.shields.io/badge/backend-FastAPI%20+%20Python-009688)
![Frontend](https://img.shields.io/badge/frontend-React%20+%20Vite-61DAFB)
![DB](https://img.shields.io/badge/base%20de%20datos-SQLite-orange)
![Auth](https://img.shields.io/badge/auth-JWT%20Bearer-purple)
![Hecho en](https://img.shields.io/badge/hecho%20en-Guayaquil%2C%20Ecuador-FFD700)

---

## ¿Qué es Nexo RRHH?

**Nexo RRHH** es una plataforma de automatización diseñada para departamentos de Recursos Humanos en empresas medianas (50–500 empleados) del Ecuador. El sistema transforma la distribución mensual de documentos críticos — **roles de pago, comprobantes de décimos y certificados laborales** — de un proceso manual propenso a errores en una ejecución automatizada, segura y trazable.

> **El problema que resolvemos:** Un proceso que antes tomaba 3 horas y dependía de que alguien enviara correos uno por uno, ahora se completa en menos de 10 minutos con validación automática, control de roles y registro completo de auditoría.

---

## Funcionalidades Principales

### Sistema de Roles con Permisos Granulares

Control de acceso real basado en la jerarquía de una empresa ecuatoriana:

| Acción | Admin | Supervisor | Operador |
|---|:---:|:---:|:---:|
| Gestionar usuarios y roles | ✅ | ❌ | ❌ |
| Crear / eliminar grupos | ✅ | ❌ | ❌ |
| Asignar miembros a grupos | ✅ | ❌ | ❌ |
| Ver lista completa de usuarios | ✅ | 👁️ Solo lectura | ❌ |
| Ver grupos disponibles | ✅ Todos | ✅ Todos | ✅ Solo los asignados |
| Crear envío masivo | ✅ | ✅ | ✅ |
| Ejecutar envío directamente | ✅ | ✅ | Solo con Modo Confianza |
| Aprobar envío de operador | ✅ | ✅ | ❌ |
| Activar Modo Confianza individual | ✅ | ✅ | ❌ |
| Activar Modo Confianza global | ✅ | ❌ | ❌ |
| Ver historial de envíos | ✅ Todos | ✅ Todos | Solo los propios |
| Importar nómina Excel/CSV | ✅ | ✅ | ❌ |
| Configurar plantillas de email | ✅ | ❌ | ❌ |

### Modo Confianza ⭐ (Feature Estrella)

Permite a Supervisores habilitar el envío directo para operadores de confianza, eliminando el cuello de botella de aprobaciones manuales en los cierres de mes. Un Operador sin Modo Confianza genera un envío en estado `pendiente_aprobacion` que el Supervisor debe despachar.

### Wizard de Envío Masivo en 4 Pasos

1. **Selección de Grupo** — Elige el grupo de empleados destinatarios.
2. **Selección de Destinatarios** — Marca individualmente quién recibirá el correo. Admin/Supervisor puede buscar y agregar usuarios extra.
3. **Configurar Email** — Elige plantilla (Rol de Pagos / Décimo Sueldo / Vacaciones), edita el asunto y el cuerpo con variables mágicas `[nombre]`, `[mes]`, `[empresa]`.
4. **Confirmación y Envío** — Resumen final y ejecución según las reglas de rol.

### Panel de Administración

- **Grupos**: Crear, editar nombre inline y eliminar grupos con confirmación.
- **Usuarios**: Ver todos los usuarios del sistema (Admin puede cambiar roles).
- **Asignar Miembros**: Asignar cualquier usuario a un grupo. Vista en tiempo real de miembros actuales.
- **Empleados**: Tabla completa con filtros, cambio de grupo inline, eliminar, e importar desde Excel/CSV.

### Utilidad de Gestión de BD por Terminal (`admin_db.py`)

Herramienta CLI interactiva con menú de colores para gestionar la base de datos directamente sin acceder al panel web:

- Ver todos los usuarios registrados
- Crear, editar y eliminar usuarios
- Ver grupos disponibles

---

## Stack Tecnológico

| Capa | Tecnología | Rol |
|---|---|---|
| Backend | FastAPI + Python 3.10+ | API REST, lógica de negocio, autenticación |
| Base de datos | SQLite | Persistencia de datos |
| ORM | SQLAlchemy | Modelos y relaciones |
| Autenticación | JWT Bearer Tokens | Sesiones seguras stateless |
| Contraseñas | bcrypt | Hashing seguro |
| Frontend | React + Vite | Interfaz corporativa SPA |
| Estilos | Tailwind CSS | Diseño responsivo |
| HTTP Client | Axios | Llamadas a la API |

---

## Estructura del Proyecto

```
demo7/
├── backend/
│   ├── main.py                        # Punto de entrada de FastAPI
│   ├── admin_db.py                    # CLI de gestión de BD por terminal
│   ├── requirements.txt               # Dependencias Python
│   └── app/
│       ├── api/
│       │   ├── deps.py                # Guardias de autenticación y roles
│       │   └── endpoints/
│       │       ├── auth.py            # Login y registro
│       │       ├── grupos.py          # CRUD de grupos + asignación de miembros
│       │       ├── usuarios.py        # Gestión de usuarios y roles
│       │       ├── empleados.py       # CRUD + importación Excel/CSV
│       │       ├── envios.py          # Lógica de envíos masivos
│       │       ├── configuracion.py   # Config SMTP + Modo Confianza global
│       │       └── admin.py           # Seed de datos demo
│       ├── core/
│       │   └── security.py            # JWT + bcrypt
│       ├── db/
│       │   ├── base_class.py          # Base de SQLAlchemy
│       │   └── session.py             # Conexión a la BD
│       ├── models/
│       │   ├── user.py                # Modelo User + RolEnum + ConfianzaConfig
│       │   ├── empleado.py            # Modelo Empleado, Grupo, OperadorGrupo
│       │   ├── envio.py               # Modelo Envio + PlantillaEmail + LogEnvio
│       │   └── config.py             # Modelo ConfigGlobal (SMTP + Confianza)
│       ├── schemas/                   # Validaciones Pydantic
│       └── services/
│           ├── confianza_service.py   # Lógica del Modo Confianza
│           ├── email_service.py       # Servicio de envío SMTP masivo
│           └── mapping_logic.py       # Motor de mapeo PDF↔Empleado por cédula
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── App.jsx                    # Rutas protegidas por rol
│       ├── main.jsx                   # Entry point
│       ├── context/
│       │   └── AuthContext.jsx        # Estado global de sesión
│       ├── pages/
│       │   ├── Login.jsx              # Pantalla de inicio de sesión
│       │   ├── Register.jsx           # Registro de nuevos usuarios
│       │   ├── NuevoEnvio.jsx         # Wizard de envío en 4 pasos
│       │   └── AdminDashboard.jsx     # Panel de administración + empleados
│       └── components/
│           ├── Navbar.jsx             # Barra de navegación con rol visible
│           └── envios/
│               ├── Paso1Grupo.jsx     # Selección de grupo
│               ├── Paso2Pdfs.jsx      # Selección de destinatarios
│               ├── Paso3Email.jsx     # Configuración de plantilla y correo
│               └── Paso4Confirmar.jsx # Confirmación y ejecución
│
├── docs/
│   └── Demo7_RRHH_RolesConfianza.pdf  # Documentación de roles
│
└── README.md
```

---

## Cómo Ejecutar

### Requisitos Previos

- Python 3.10+
- Node.js 18+
- pip

### PASO 1 — Backend (FastAPI)

```bash
cd demo7/backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Espera a ver `Application startup complete`. Deja la terminal abierta.

### PASO 2 — Frontend (React + Vite)

En **otra terminal**:

```bash
cd demo7/frontend
npm install
npm run dev
```

### PASO 3 — Abrir la App

Navega a:

```
http://localhost:5173
```

### (Opcional) Servidor SMTP de Debug

Para probar el envío real de correos en modo local:

```bash
python -m smtpd -c DebuggingServer -n localhost:1025
```

### (Opcional) Herramienta CLI de BD

```bash
cd demo7/backend
python admin_db.py
```

---

## Credenciales de Prueba

Usa el formulario de **Registro** (`/register`) o la herramienta `admin_db.py` para crear usuarios:

| Rol | Acceso | Al iniciar sesión va a |
|---|---|---|
| `admin` | Control total | Panel de Administración |
| `supervisor` | Aprobaciones + lectura | Panel de Administración |
| `operador` | Solo Wizard de envío | Nuevo Envío |

### Generar Datos de Demo

Después de crear un usuario admin e iniciar sesión, usa el endpoint de seed:

```bash
curl -X POST http://localhost:8000/api/admin/seed \
     -H "Authorization: Bearer <TU_TOKEN>"
```

Esto generará: 1 grupo con 10 empleados, 3 plantillas de email y PDFs simulados.

---

## Modos SMTP

| Modo | Host | Puerto | TLS | Uso |
|------|-----------------|--------|-----|-------------------------------------------|
| LOCAL | localhost | 1025 | No | Servidor de debug (sin autenticación) |
| GMAIL | smtp.gmail.com | 587 | Sí | Producción con Contraseña de Aplicación |

La configuración SMTP se gestiona desde la API (`PATCH /api/configuracion/smtp`) o directamente en la BD.

---

## Roadmap

- [ ] Envío real de correos vía SMTP / SendGrid / Mailgun
- [ ] Historial de envíos con filtro por rol
- [ ] Activación del Modo Confianza individual desde el panel
- [ ] Programación de envíos automáticos (cron)
- [ ] Conexión OAuth2 con Gmail y Outlook
- [ ] Exportación de logs y reportes de auditoría
- [ ] Configuración personalizada de plantillas HTML
- [ ] Migración a PostgreSQL en producción

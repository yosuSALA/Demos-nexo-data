# Nexo RRHH — Sistema de Envío Masivo de Reportes 🇪🇨

![Versión](https://img.shields.io/badge/versión-7.0--RRHH-blue)
![Backend](https://img.shields.io/badge/backend-FastAPI%20%2B%20Python-009688)
![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB)
![DB](https://img.shields.io/badge/base%20de%20datos-SQLite-orange)
![Auth](https://img.shields.io/badge/auth-JWT%20Bearer-purple)
![Hecho en](https://img.shields.io/badge/hecho%20en-Guayaquil%2C%20Ecuador-FFD700)

---

## ¿Qué es Nexo RRHH?

**Nexo RRHH** es una plataforma de automatización diseñada para departamentos de Recursos Humanos en empresas medianas (50–500 empleados) del Ecuador. El sistema transforma la distribución mensual de documentos críticos —**roles de pago, comprobantes de décimos y certificados laborales**— de un proceso manual propenso a errores en una ejecución automatizada, segura y trazable.

> **El problema que resolvemos:** Un proceso que antes tomaba 3 horas y dependía de que alguien enviara correos uno por uno, ahora se completa en menos de 10 minutos con validación automática, control de roles y registro completo de auditoría.

---

## Funcionalidades Principales

### Sistema de Roles con Permisos Granulares

Nexo RRHH implementa un control de acceso real basado en la jerarquía de una empresa ecuatoriana:

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

1. **Selección de Grupo** — Elige el grupo de empleados al que se enviará el correo.
2. **Selección de Destinatarios** — Marca individualmente quién recibirá el correo. Admin/Supervisor puede buscar y agregar usuarios extra.
3. **Configurar Email** — Elige plantilla (Rol de Pagos / Décimo Sueldo / Vacaciones), edita el asunto y el cuerpo con variables mágicas `[nombre]`, `[mes]`, `[empresa]`.
4. **Confirmación y Envío** — Resumen final y ejecución según las reglas de rol.

### Panel de Administración

- **Grupos**: Crear, editar nombre inline y eliminar grupos con confirmación.
- **Usuarios**: Ver todos los usuarios del sistema (Admin puede cambiar roles).
- **Asignar Miembros**: Asignar cualquier usuario (cualquier rol) a un grupo. Vista en tiempo real de miembros actuales con posibilidad de removerlos.

### Utilidad de Gestión de BD por Terminal (`admin_db.py`)

Herramienta CLI con menú interactivo de colores para que el administrador pueda gestionar la base de datos directamente sin acceder al panel web:

- Ver todos los usuarios registrados
- Crear, editar y eliminar usuarios
- Ver grupos disponibles

---

## Stack Tecnológico

| Capa | Tecnología | Rol |
|---|---|---|
| Backend | FastAPI + Python 3.10+ | API REST, lógica de negocio, autenticación |
| Base de datos | SQLite (migración a PostgreSQL disponible) | Persistencia de datos |
| ORM | SQLAlchemy | Modelos y relaciones |
| Autenticación | JWT Bearer Tokens | Sesiones seguras stateless |
| Contraseñas | bcrypt nativo | Hashing seguro |
| Frontend | React + Vite | Interfaz corporativa SPA |
| Estilos | Tailwind CSS | Diseño premium y responsivo |
| HTTP Client | Axios | Llamadas a la API |

---

## Estructura del Proyecto

```
Demo7/
├── backend/
│   ├── main.py                        # Punto de entrada de FastAPI
│   ├── admin_db.py                    # CLI de gestión de BD por terminal
│   ├── requirements.txt               # Dependencias Python
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py                # Guardias de autenticación y roles
│   │   │   └── endpoints/
│   │   │       ├── auth.py            # Login y registro
│   │   │       ├── grupos.py          # CRUD de grupos + asignación de miembros
│   │   │       ├── usuarios.py        # Gestión de usuarios y roles
│   │   │       └── envios.py          # Lógica de envíos masivos
│   │   ├── core/
│   │   │   └── security.py            # JWT + bcrypt
│   │   ├── db/
│   │   │   ├── base_class.py          # Base de SQLAlchemy
│   │   │   └── session.py             # Conexión a la BD
│   │   ├── models/
│   │   │   ├── user.py                # Modelo User + RolEnum
│   │   │   ├── empleado.py            # Modelo Empleado, Grupo, OperadorGrupo
│   │   │   └── envio.py               # Modelo Envio + estados
│   │   ├── schemas/                   # Validaciones Pydantic
│   │   └── services/
│   │       ├── confianza_service.py   # Lógica del Modo Confianza
│   │       ├── email_service.py       # Servicio de envío de correos
│   │       └── mapping_logic.py       # Motor de mapeo PDF-Empleado
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                    # Rutas protegidas por rol
│   │   ├── context/
│   │   │   └── AuthContext.jsx        # Estado global de sesión
│   │   ├── pages/
│   │   │   ├── Login.jsx              # Pantalla de inicio de sesión
│   │   │   ├── Register.jsx           # Registro de nuevos usuarios
│   │   │   ├── NuevoEnvio.jsx         # Wizard de envío en 4 pasos
│   │   │   └── AdminDashboard.jsx     # Panel de admin y supervisor
│   │   └── components/
│   │       ├── Navbar.jsx             # Barra de navegación con rol visible
│   │       └── envios/
│   │           ├── Paso1Grupo.jsx     # Selección de grupo
│   │           ├── Paso2Pdfs.jsx      # Selección de destinatarios
│   │           ├── Paso3Email.jsx     # Configuración de plantilla y correo
│   │           └── Paso4Confirmar.jsx # Confirmación y ejecución
│
└── README.md
```

---

## Cómo Encender la Aplicación

### PASO 1 — Encender el Backend (Python)

Abre un **Símbolo de Sistema (CMD)** y ejecuta línea por línea:

```cmd
cd C:\Users\Daly\OneDrive\Documentos\Demo7\backend
..\.venv_pdf\Scripts\activate.bat
python -m uvicorn main:app --reload
```

Espera a ver `Application startup complete`. **Deja esa ventana minimizada, no la cierres.**

### PASO 2 — Encender el Frontend (React)

Abre **otra ventana de CMD** y ejecuta:

```cmd
cd C:\Users\Daly\OneDrive\Documentos\Demo7\frontend
npm run dev
```

### PASO 3 — Ingresar a la App

Abre tu navegador (Chrome, Edge) y ve a:

```
http://localhost:5174
```

---

## Utilidad de Gestión por Terminal

Para ver, crear, editar o eliminar usuarios directamente en la base de datos sin abrir la app:

> ⚠️ El backend debe estar encendido (Paso 1) antes de ejecutar esto.

```cmd
cd C:\Users\Daly\OneDrive\Documentos\Demo7\backend
..\.venv_pdf\Scripts\activate.bat
python admin_db.py
```

Se abrirá un menú interactivo con colores en la terminal.

---

## Credenciales de Prueba (Demo)

Usa el panel de administración o `admin_db.py` para crear usuarios con los roles necesarios.

| Rol | Acceso | Al iniciar sesión va a |
|---|---|---|
| `admin` | Control total | Panel de Administración |
| `supervisor` | Aprobaciones + lectura | Panel de Administración |
| `operador` | Solo Wizard de envío | Nuevo Envío |

---

## Próximas Funcionalidades (Roadmap)

- [ ] Envío real de correos vía SMTP / SendGrid / Mailgun
- [ ] Importación de nómina desde Excel/CSV
- [ ] Historial de envíos con filtro por rol
- [ ] Activación del Modo Confianza individual desde el panel
- [ ] Programación de envíos automáticos (cron)
- [ ] Conexión OAuth2 con Gmail y Outlook
- [ ] Exportación de logs y reportes de auditoría
- [ ] Configuración personalizada de plantillas HTML
- [ ] Migración a PostgreSQL en producción (Railway / Render)

# Monitor de Vencimiento de Contratos y Obligaciones

Dashboard interactivo construido con **Streamlit** para supervisar el estado de contratos, polizas, garantias y permisos municipales. El sistema clasifica cada obligacion mediante un semaforo de tres colores (Rojo, Amarillo, Verde) segun los dias restantes para su vencimiento, y cuenta con un motor de alertas por correo electronico para notificar a los responsables internos cuando una obligacion se acerca a su fecha limite.

---

## Arquitectura del Sistema

```
+---------------------+       +----------------------+       +-------------------+
|                     |       |                      |       |                   |
|   etl_contratos.py  +------>+  datos_dashboard_    +------>+   dashboard.py    |
|   (Generacion ETL)  |       |  contratos.csv       |       |   (Streamlit UI)  |
|                     |       |                      |       |                   |
+--------+------------+       +----------------------+       +-------------------+
         |                                                          |
         |                                                          |
         v                                                          v
+---------------------+       +----------------------+       +-------------------+
|                     |       |                      |       |                   |
|   scheduler.py      |       |   config.py          |       | alertas_email.py  |
|   (APScheduler      |       |   (.env + variables)  |       | (SMTP / dry_run)  |
|    job diario)      |       |                      |       |                   |
+---------------------+       +----------------------+       +-------------------+
                                                                    |
                                                                    v
                                                             +-------------------+
                                                             |  logs/            |
                                                             |  alertas.log      |
                                                             +-------------------+
```

**Flujo de datos:**

1. `etl_contratos.py` genera datos sinteticos (Faker) y calcula el semaforo por dias restantes.
2. Los datos transformados se persisten en `datos_dashboard_contratos.csv`.
3. `dashboard.py` lee el CSV, aplica filtros interactivos y renderiza graficos con Plotly.
4. `alertas_email.py` filtra obligaciones en umbrales criticos (7, 15 y 30 dias) y envia correos (modo `dry_run` o `live`).
5. `scheduler.py` orquesta la ejecucion automatica diaria del ETL y las alertas mediante APScheduler.

---

## Requisitos Previos

- **Python** 3.10 o superior
- **pip** (gestor de paquetes de Python)
- (Opcional) Cuenta SMTP configurada para envio real de correos

---

## Instalacion

```bash
# 1. Clonar o copiar el proyecto
cd demo8

# 2. Crear entorno virtual (recomendado)
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

### Configuracion de variables de entorno

Crear un archivo `.env` en la raiz del proyecto con las siguientes variables (todas opcionales para modo `dry_run`):

```env
# Modo de email: "dry_run" (solo log) o "live" (envio SMTP real)
EMAIL_MODE=dry_run

# Configuracion SMTP (solo necesario si EMAIL_MODE=live)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_correo@gmail.com
SMTP_PASSWORD=tu_contraseña_de_aplicacion

# Hora de ejecucion del scheduler (formato 24h)
SCHEDULER_HOUR=8
SCHEDULER_MINUTE=0
```

---

## Como Ejecutar

### Dashboard interactivo

```bash
streamlit run dashboard.py
```

El navegador se abrira automaticamente en `http://localhost:8501`.

### ETL independiente (sin dashboard)

```bash
python etl_contratos.py
```

Genera los datos sinteticos, aplica la transformacion y exporta el CSV. Tambien imprime en consola las alertas de los umbrales criticos.

### Scheduler automatico (ejecucion diaria)

```bash
python scheduler.py
```

Ejecuta el ETL y el motor de alertas inmediatamente al iniciar, y luego los reprograma diariamente a la hora configurada en `.env`. Utiliza la zona horaria `America/Santiago`.

---

## Funcionalidades

### Dashboard (Streamlit)

- **KPI Cards**: total de obligaciones, conteo por semaforo (Rojo / Amarillo / Verde) y valor USD en riesgo.
- **Grafico de dona**: distribucion porcentual del semaforo.
- **Grafico de barras horizontales**: obligaciones agrupadas por tipo y estado.
- **Grafico de barras temporales**: vencimientos proyectados en los proximos 90 dias.
- **Indicador de riesgo (gauge)**: porcentaje de obligaciones criticas respecto al total, con umbral de referencia al 20%.
- **Top 5 contratos criticos**: tabla con los contratos en estado Rojo de mayor valor USD.
- **Tabla detallada con filtros**: tabla interactiva con colores de fondo por semaforo, ordenable y filtrable.
- **Descarga CSV**: boton para exportar los datos filtrados a un archivo CSV.

### Filtros del Sidebar

- Estado semaforo (multiseleccion: Rojo, Amarillo, Verde)
- Tipo de obligacion (Contrato de Arriendo, Poliza de Seguro, Garantia, Permiso Municipal)
- Responsable interno

### Sistema de Alertas

- Umbrales configurados a **7, 15 y 30 dias** antes del vencimiento.
- Modo `dry_run`: registra las alertas en `logs/alertas.log` sin enviar correos.
- Modo `live`: envio real via SMTP con plantilla HTML profesional.
- Boton de envio manual integrado en el sidebar del dashboard.

### Semaforo de Estado

| Color      | Condicion             | Significado                  |
|------------|-----------------------|------------------------------|
| Rojo       | Menos de 15 dias      | Critico / Urgente            |
| Amarillo   | Entre 15 y 30 dias    | Alerta / Requiere atencion   |
| Verde      | Mas de 30 dias        | Al dia / Sin riesgo inmediato|

---

## Estructura de Archivos

```
demo8/
├── dashboard.py                   # Aplicacion principal Streamlit (UI)
├── etl_contratos.py               # Pipeline ETL: generacion, transformacion y alertas
├── alertas_email.py               # Motor de alertas por correo (SMTP / dry_run)
├── config.py                      # Configuracion centralizada (lee .env)
├── scheduler.py                   # Scheduler diario con APScheduler
├── requirements.txt               # Dependencias del proyecto
├── datos_dashboard_contratos.csv  # Datos generados por el ETL (100 registros)
├── logs/
│   └── alertas.log                # Log de alertas procesadas
└── README.md                      # Este archivo
```

### Descripcion de cada modulo

| Archivo                | Responsabilidad                                                                                   |
|------------------------|---------------------------------------------------------------------------------------------------|
| `dashboard.py`         | Interfaz visual con Streamlit. Carga datos, aplica filtros, renderiza graficos Plotly y tabla.     |
| `etl_contratos.py`     | Genera datos sinteticos con Faker, calcula dias para vencer, asigna semaforo y exporta CSV.       |
| `alertas_email.py`     | Construye emails HTML y los envia via SMTP o los registra en log segun el modo configurado.       |
| `config.py`            | Lee variables de entorno desde `.env` con python-dotenv. Centraliza rutas y parametros SMTP.      |
| `scheduler.py`         | Orquesta la ejecucion automatica diaria del ETL y alertas usando APScheduler (CronTrigger).       |
| `requirements.txt`     | Lista de dependencias: pandas, faker, streamlit, plotly, apscheduler, python-dotenv.              |

---

## Dependencias Principales

| Paquete         | Version minima | Uso                                      |
|-----------------|----------------|------------------------------------------|
| pandas          | 2.0            | Manipulacion y analisis de datos          |
| faker           | 24.0           | Generacion de datos sinteticos            |
| streamlit       | 1.35           | Framework del dashboard web               |
| plotly          | 5.20           | Graficos interactivos (dona, barras, gauge)|
| apscheduler     | 3.10           | Programacion de tareas periodicas         |
| python-dotenv   | 1.0            | Carga de variables de entorno desde .env  |

---

## Capturas de Pantalla

> _Seccion reservada para capturas de pantalla del dashboard._

### Vista general del dashboard

```
[ Insertar captura: vista completa del dashboard con KPIs y graficos ]
```

### Semaforo y distribucion por tipo

```
[ Insertar captura: grafico de dona y barras horizontales ]
```

### Indicador de riesgo y Top 5 criticos

```
[ Insertar captura: gauge de riesgo global y tabla Top 5 ]
```

### Tabla detallada con filtros aplicados

```
[ Insertar captura: tabla principal con colores por semaforo ]
```

### Sidebar con filtros y alertas

```
[ Insertar captura: panel lateral con filtros y boton de alertas ]
```

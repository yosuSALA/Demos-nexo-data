# Demo 7 -- Bot de Envio Masivo de Estados de Cuenta por Email

## Descripcion

Bot automatizado para la distribucion masiva de estados de cuenta mensuales a clientes, con archivos PDF adjuntos. El sistema lee una lista de clientes desde un archivo CSV, construye correos personalizados con el reporte PDF correspondiente y los envia via SMTP. Incluye validacion de correos, manejo de errores y registro detallado de cada envio.

Adicionalmente cuenta con una interfaz web construida con Streamlit que permite visualizar la lista de clientes, ejecutar la generacion de datos de prueba, enviar reportes y monitorear el estado de cada envio en tiempo real.

## Arquitectura

```
demo7/
├── app.py                  # Interfaz web Streamlit (dashboard)
├── email_bot.py            # Logica principal de envio masivo SMTP
├── setup_mock_data.py      # Generador de datos de prueba (CSV + PDFs)
├── requirements.txt        # Dependencias del proyecto
├── clientes_reportes.csv   # (generado) Lista de clientes
├── reportes_mensuales/     # (generado) PDFs simulados de estados de cuenta
├── envios.log              # (generado) Registro de envios
└── README.md               # Este archivo
```

### Flujo de datos

1. `setup_mock_data.py` genera el CSV de clientes y los PDFs simulados.
2. `email_bot.py` lee el CSV, construye correos MIME con PDF adjunto y los envia via SMTP.
3. `app.py` orquesta ambos modulos desde una interfaz visual interactiva.

### Modos SMTP

| Modo   | Host            | Puerto | TLS | Uso                                       |
|--------|-----------------|--------|-----|-------------------------------------------|
| LOCAL  | localhost       | 1025   | No  | Servidor de debug (sin autenticacion)     |
| GMAIL  | smtp.gmail.com  | 587    | Si  | Produccion con Contrasena de Aplicacion   |

## Como ejecutar

### Requisitos previos

- Python 3.9 o superior
- pip

### Instalacion

```bash
pip install -r requirements.txt
```

### Opcion 1: Interfaz web (recomendado)

```bash
python -m streamlit run app.py
```

La interfaz permite generar datos de prueba, visualizar clientes y enviar reportes desde el navegador.

### Opcion 2: Linea de comandos

```bash
# Paso 1: Generar datos de prueba
python setup_mock_data.py

# Paso 2: Iniciar servidor SMTP de debug (en otra terminal)
python -m smtpd -c DebuggingServer -n localhost:1025

# Paso 3: Ejecutar el bot de envio
python email_bot.py
```

## Capturas de pantalla

### Dashboard principal
![Dashboard principal](screenshots/dashboard.png)

### Tabla de clientes
![Tabla de clientes](screenshots/tabla_clientes.png)

### Resultado del envio
![Resultado del envio](screenshots/resultado_envio.png)

# Demo 6 — Generador Automático de ATS y Anexos SRI

## Descripción

Script modular en Python que automatiza la generación del **Anexo Transaccional Simplificado (ATS)** requerido por el Servicio de Rentas Internas (SRI) de Ecuador. El sistema toma un archivo plano de compras (simulado con datos mock), aplica reglas de validación tributaria, separa los registros erróneos con descripción de motivo y genera el XML final listo para subir al portal del SRI.

## Arquitectura

```
demo6/
├── main.py               # Orquestador del pipeline completo
├── mock_data.py           # Generador de datos de prueba (DataFrame pandas)
├── validador_sri.py       # Motor de validación según reglas del SRI
├── generador_xml.py       # Constructor del XML del ATS (xml.etree)
├── requirements.txt       # Dependencias del proyecto
├── output/                # (generado) Archivos de salida
│   ├── ats_generado_MM_AAAA.xml    # XML del ATS
│   └── errores_ats_MM_AAAA.xlsx    # Errores para revisión contable
└── README.md              # Este archivo
```

### Flujo de datos

```
  ┌──────────────────┐
  │  mock_data.py    │  Genera ~20 registros de compras simulados
  │  (DataFrame)     │  (algunos con errores intencionales)
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ validador_sri.py │  Aplica reglas del SRI:
  │                  │   • RUC = 13 dígitos + termina en "001"
  │                  │   • Retención IVA = monto_iva × porcentaje
  └────┬────────┬────┘
       │        │
   válidos   errores
       │        │
       ▼        ▼
  ┌─────────┐  ┌──────────────────┐
  │ XML ATS │  │ Excel de errores │
  │ (.xml)  │  │ (.xlsx)          │
  └─────────┘  └──────────────────┘
```

### Módulos

| Módulo             | Responsabilidad                                                            |
|--------------------|----------------------------------------------------------------------------|
| `mock_data.py`     | Genera un DataFrame con registros de compras (válidos e inválidos)         |
| `validador_sri.py` | Valida RUC y retenciones IVA; separa válidos de errores con motivo         |
| `generador_xml.py` | Construye el árbol XML `<iva><compras><detalleCompras>...</detalleCompras>` |
| `main.py`          | Orquesta el pipeline y genera reportes en consola + archivos de salida     |

### Reglas de validación implementadas

1. **RUC del proveedor**: exactamente 13 caracteres numéricos, terminados en `001`.
2. **Retención IVA**: `valor_retenido_iva ≈ monto_iva × porcentaje_retencion_iva` (tolerancia de ±$0.02).

## Cómo ejecutar

### Requisitos previos

- Python 3.10 o superior
- pip

### Instalación

```bash
pip install -r requirements.txt
```

### Ejecución

```bash
python main.py
```

Al ejecutar, el script:
1. Genera 20 registros de compras simulados.
2. Valida cada registro con las reglas del SRI.
3. Imprime un reporte de validación con detalle de errores.
4. Genera el XML del ATS en `output/ats_generado_MM_AAAA.xml`.
5. Exporta los errores a `output/errores_ats_MM_AAAA.xlsx`.

### Ejecución por módulo

Cada módulo se puede ejecutar de forma independiente para inspección rápida:

```bash
# Ver datos mock generados
python mock_data.py

# Ver resultado de validación
python validador_sri.py

# Generar solo el XML
python generador_xml.py
```

## Estructura del XML generado

```xml
<?xml version='1.0' encoding='utf-8'?>
<iva>
  <TipoIDInformante>R</TipoIDInformante>
  <IdInformante>1790016919001</IdInformante>
  <razonSocial>EMPRESA DEMO S.A.</razonSocial>
  <Anio>2026</Anio>
  <Mes>03</Mes>
  <compras>
    <detalleCompras>
      <codSustento>01</codSustento>
      <tpIdProv>01</tpIdProv>
      <idProv>1791714350001</idProv>
      <tipoComprobante>01</tipoComprobante>
      <fechaRegistro>15/01/2026</fechaRegistro>
      <establecimiento>042</establecimiento>
      <puntoEmision>087</puntoEmision>
      <secuencial>012345678</secuencial>
      <autorizacion>1234567890</autorizacion>
      <baseNoGraIva>100.00</baseNoGraIva>
      <baseImponible>5000.00</baseImponible>
      <baseImpGrav>5000.00</baseImpGrav>
      <montoIva>600.00</montoIva>
      <valRetBien10>0.00</valRetBien10>
      <valRetServ20>0.00</valRetServ20>
      <valorRetBienes>180.00</valorRetBienes>
      <valRetServ50>0.00</valRetServ50>
      <valorRetServicios>0.00</valorRetServicios>
      <valRetServ100>0.00</valRetServ100>
      <valorRetRenta>100.00</valorRetRenta>
    </detalleCompras>
    <!-- ... más registros ... -->
  </compras>
</iva>
```

## Tecnologías

- **Python 3.10+**
- **pandas** — Manipulación de DataFrames
- **openpyxl** — Exportación a Excel
- **xml.etree.ElementTree** — Generación de XML (stdlib)

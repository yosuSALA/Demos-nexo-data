"""
admin.py — Endpoint de seed de datos demo
==========================================
Pobla la base de datos con un conjunto realista de empleados, grupos
y plantillas de email para poder probar el flujo completo sin datos reales.
También genera PDFs simulados en uploads/{grupo_id}/ para el envío con adjunto.

Solo accesible para usuarios con rol 'admin'.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_admin
from app.models.user import User
from app.models.empleado import Empleado, Grupo, EmpleadoEstado
from app.models.envio import PlantillaEmail
from app.services.email_service import UPLOADS_DIR

router = APIRouter()

# ---------------------------------------------------------------------------
# Datos de demo
# ---------------------------------------------------------------------------

EMPLEADOS_DEMO = [
    # (cedula, nombre, apellido, email, departamento, cargo)
    ("0901234567", "Carlos",    "Herrera",    "carlos.herrera@demo-nexo.com",    "Planta",    "Operador de Línea"),
    ("0902345678", "María",     "Fernández",  "maria.fernandez@demo-nexo.com",   "Planta",    "Supervisora de Línea"),
    ("0903456789", "Andrés",    "Martínez",   "andres.martinez@demo-nexo.com",   "RRHH",      "Analista RRHH"),
    ("0904567890", "Lucía",     "Ramírez",    "lucia.ramirez@demo-nexo.com",     "Finanzas",  "Contadora Senior"),
    ("0905678901", "Miguel",    "Torres",     "miguel.torres@demo-nexo.com",     "TI",        "Desarrollador Backend"),
    ("0906789012", "Valeria",   "Gómez",      "valeria.gomez@demo-nexo.com",     "Ventas",    "Ejecutiva de Cuentas"),
    ("0907890123", "Ricardo",   "López",      "ricardo.lopez@demo-nexo.com",     "Planta",    "Técnico Mecánico"),
    ("0908901234", "Daniela",   "Vargas",     "daniela.vargas@demo-nexo.com",    "Logística", "Jefa de Bodega"),
    ("0909012345", "Sebastián", "Castro",     "sebastian.castro@demo-nexo.com",  "TI",        "DevOps Engineer"),
    # Fila sin email → demuestra manejo de errores en el envío
    ("0910123456", "Natalia",   "Moreno",     "",                                "Ventas",    "Asistente Comercial"),
]

PLANTILLAS_DEMO = [
    (
        "Rol de Pagos",
        "Rol de Pagos – [mes] | [empresa]",
        "Estimado/a [nombre],\n\nAdjuntamos tu Rol de Pagos correspondiente al período [mes].\n\n"
        "Encontrarás el detalle de tu remuneración, descuentos y aportes al IESS.\n\n"
        "Atentamente,\nDepartamento de RRHH – [empresa]",
    ),
    (
        "Décimo Sueldo",
        "Acreditación Décimo Sueldo – [mes] | [empresa]",
        "Estimado/a [nombre],\n\nTe informamos que el Décimo Sueldo correspondiente a [mes] "
        "ha sido acreditado en tu cuenta bancaria registrada.\n\n"
        "Atentamente,\nDepartamento de RRHH – [empresa]",
    ),
    (
        "Vacaciones",
        "Confirmación de Vacaciones Aprobadas | [empresa]",
        "Estimado/a [nombre],\n\nConfirmamos el período de vacaciones aprobado para [mes]. "
        "Por favor coordina con tu supervisor la entrega de pendientes antes de tu salida.\n\n"
        "Atentamente,\nDepartamento de RRHH – [empresa]",
    ),
]

# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/seed")
def seed_demo_data(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Genera datos de demostración completos:
    - 1 grupo 'Planta Guayaquil Demo' con 10 empleados (1 sin email para test de error)
    - 3 plantillas de email: Rol de Pagos, Décimo Sueldo, Vacaciones
    - PDFs simulados en uploads/{grupo_id}/ (texto plano con .pdf)

    Es idempotente: omite duplicados sin error.
    """

    # 1. Grupo demo
    grupo = db.query(Grupo).filter(Grupo.nombre == "Planta Guayaquil Demo").first()
    if not grupo:
        grupo = Grupo(
            nombre="Planta Guayaquil Demo",
            descripcion="Grupo generado por seed de demo – 10 empleados de prueba",
            created_by=admin.id,
        )
        db.add(grupo)
        db.commit()
        db.refresh(grupo)

    # 2. Empleados
    insertados = 0
    for cedula, nombre, apellido, email, depto, cargo in EMPLEADOS_DEMO:
        if not db.query(Empleado).filter(Empleado.cedula == cedula).first():
            emp = Empleado(
                cedula=cedula,
                nombre=nombre,
                apellido=apellido,
                email=email or None,
                departamento=depto,
                cargo=cargo,
                grupo_id=grupo.id,
                estado=EmpleadoEstado.activo,
            )
            db.add(emp)
            insertados += 1
    db.commit()

    # 3. Plantillas de email
    plantillas_insertadas = 0
    for nombre_p, asunto_p, cuerpo_p in PLANTILLAS_DEMO:
        if not db.query(PlantillaEmail).filter(PlantillaEmail.nombre == nombre_p).first():
            db.add(PlantillaEmail(nombre=nombre_p, asunto=asunto_p, cuerpo_html=cuerpo_p))
            plantillas_insertadas += 1
    db.commit()

    # 4. PDFs simulados en uploads/{grupo_id}/
    pdf_dir = UPLOADS_DIR / str(grupo.id)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdfs_creados = 0
    for cedula, nombre, apellido, *_ in EMPLEADOS_DEMO:
        ruta = pdf_dir / f"nomina_{cedula}_demo.pdf"
        if not ruta.exists():
            ruta.write_text(
                f"NÓMINA DEMO — Nexo Data S.A.\n"
                f"{'=' * 35}\n"
                f"Empleado : {nombre} {apellido}\n"
                f"Cédula   : {cedula}\n"
                f"Período  : [Generado por seed de demo]\n\n"
                f"[Contenido de nómina simulado]\n",
                encoding="utf-8",
            )
            pdfs_creados += 1

    return {
        "msg": "Datos de demo generados correctamente.",
        "grupo_id": grupo.id,
        "grupo_nombre": grupo.nombre,
        "empleados_insertados": insertados,
        "plantillas_insertadas": plantillas_insertadas,
        "pdfs_simulados": pdfs_creados,
        "nota": (
            f"Los PDFs están en uploads/{grupo.id}/. "
            "Puedes enviar a este grupo directamente con plantilla_id=1 (Rol de Pagos)."
        ),
    }

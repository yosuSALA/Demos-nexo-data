from sqlalchemy.orm import Session
from app.models.envio import Envio

def send_resumen_supervisor(envio_id: int, db: Session) -> None:
    """
    Simula el envío de correo de auditoría "POST-ENVÍO" para los supervisores RRHH.
    Este modelo es síncrono por la arquitectura temporal, pero la base está lista.
    """
    # En la realidad usaremos smtp.lib() acá
    envio = db.query(Envio).filter(Envio.id == envio_id).first()
    if not envio:
        return
        
    try:
        operador_nombre = envio.creador.nombre if envio.creador else "Desconocido"
        grupo_nombre = envio.grupo.nombre if envio.grupo else "Grupo Desconocido"
        
        print("\n\n" + "="*50)
        print("MOCK - ENVIANDO CORREO AL SUPERVISOR")
        print(f"Asunto: Resumen de Envío Modo Confianza [{envio.nombre}]")
        print(f"Operador Ejecutivo: {operador_nombre}")
        print(f"Grupo Procesado: {grupo_nombre}")
        print(f"Cédulas encontradas y procesadas: {envio.total}")
        print(f"Éxitos: {envio.enviados_ok}  |  Fallos: {envio.enviados_fallo}")
        print(f"Verifica el historial completo en el Log de Nexo.")
        print("="*50 + "\n\n")
    except Exception as e:
        print(f"Error generando resumen: {e}")

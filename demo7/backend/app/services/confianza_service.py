from sqlalchemy.orm import Session
from app.models.user import ConfianzaConfig
from app.models.config import ConfigGlobal

def check_modo_confianza(operador_id: int, db: Session) -> bool:
    """
    Retorna True si:
    - El campo ConfianzaGlobal en la tabla Config es True, O
    - Existe un registro ConfianzaConfig para ese operador con activo=True
    Retorna False en cualquier otro caso.
    """
    try:
        # Chequeo Global
        config_global = db.query(ConfigGlobal).first()
        if config_global and config_global.modo_confianza_global:
            return True
        
        # Chequeo Individual
        confianza_individual = db.query(ConfianzaConfig).filter(ConfianzaConfig.operador_user_id == operador_id).first()
        if confianza_individual and confianza_individual.activo:
            return True
            
        return False
    except Exception:
        # Falla de forma segura: al mínimo error asume False (requerir revisión)
        return False

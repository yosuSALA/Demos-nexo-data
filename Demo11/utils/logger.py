import sys
from loguru import logger


def setup_logger(log_file: str = "etl.log", level: str = "INFO") -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> — {message}",
        colorize=True,
    )
    logger.add(
        log_file,
        level=level,
        rotation="50 MB",
        retention="7 days",
        compression="gz",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{line} — {message}",
    )

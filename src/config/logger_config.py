import logging
import sys
from pathlib import Path
from typing import Optional
import functools

class LoggerSetup:
    _instance: Optional['LoggerSetup'] = None
    _configured = False
    
    def __new__(cls) -> 'LoggerSetup':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def setup_logger(self, name: str, log_level: str = "INFO") -> logging.Logger:
        """Configuración centralizada de logger."""
        if self._configured:
            return logging.getLogger(name)
            
        # Crear directorio de logs
        log_dir = Path("../docs/reports/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar logger raíz
        logger = logging.getLogger()
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Limpiar handlers existentes
        logger.handlers.clear()
        
        # Handler para archivo
        file_handler = logging.FileHandler(log_dir / "proyecto.log")
        file_handler.setLevel(logging.DEBUG)
        
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        self._configured = True
        return logging.getLogger(name)

# Decorador
def log_execution(func_name: Optional[str] = None):
    """Decorador robusto para logging de funciones."""
    def decorator(func):
        name = func_name or func.__name__
        logger = logging.getLogger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"Iniciando: {name}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"Completado: {name}")
                return result
            except Exception as e:
                logger.error(f"Error en {name}: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator
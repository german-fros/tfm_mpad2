import logging
import sys
from pathlib import Path
from typing import Optional
import functools
import locale

# Configurar encoding del sistema
if sys.platform.startswith('win'):
    locale.setlocale(locale.LC_ALL, 'Spanish_Spain.utf8')
# else:
#     locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')


def find_project_root():
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "setup.py").exists() or (parent / "requirements.txt").exists():
            return parent
    return current


class LoggerSetup:
    _instance: Optional['LoggerSetup'] = None
    _configured = False
    
    def __new__(cls) -> 'LoggerSetup':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def setup_logger(self, name: str, log_level: str = "INFO") -> logging.Logger:
        """Configuración centralizada de logger."""
        
        # Configurar logger raíz solo si no tiene handlers
        root_logger = logging.getLogger()

        if not root_logger.handlers:

            # Obtener el path absoluto de /logs
            PROJECT_ROOT = find_project_root()
            log_dir = PROJECT_ROOT / "docs" / "reports" / "logs"

            # Crear directorio de logs
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Configurar logger raíz
            root_logger.setLevel(logging.DEBUG)
            
            # Crear log único por ejecución con timestamp
            from datetime import datetime
            import glob
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"proyecto_{timestamp}.log"
            
            # Limpiar logs antiguos (mantener solo los 3 más recientes)
            existing_logs = sorted(glob.glob(str(log_dir / "proyecto_*.log")))
            if len(existing_logs) >= 3:
                # Eliminar los más antiguos, dejando espacio para el nuevo
                logs_to_delete = existing_logs[:-2]  # Mantener solo 2, el nuevo será el 3ro
                for old_log in logs_to_delete:
                    try:
                        Path(old_log).unlink()
                    except (PermissionError, OSError) as e:
                        # Archivo en uso por otro proceso, continuar sin eliminar
                        pass
            
            # Handler para archivo único por ejecución
            file_handler = logging.FileHandler(log_dir / log_filename, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            
            # Formato
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            root_logger.addHandler(file_handler)
            
            # SILENCIAR LOGGERS RUIDOSOS
            logging.getLogger('matplotlib').setLevel(logging.WARNING)
            logging.getLogger('matplotlib.pyplot').setLevel(logging.WARNING)
            logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
            logging.getLogger('PIL').setLevel(logging.WARNING)
            logging.getLogger('urllib3').setLevel(logging.WARNING)
        
        # Obtener logger específico del módulo - heredará configuración del root
        module_logger = logging.getLogger(name)
        module_logger.setLevel(logging.DEBUG)  # Habilitado para desarrollo
        
        self._configured = True
        return module_logger


# Decorador
def log_function(func_name: Optional[str] = None):
    """Decorador robusto para logging de funciones."""
    def decorator(func):
        name = func_name or func.__name__
        logger = logging.getLogger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"=== Iniciando: {name} ===")
            try:
                result = func(*args, **kwargs)
                logger.info(f"=== Completado: {name} ===")
                return result
            except Exception as e:
                logger.error(f"Error en {name}: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator
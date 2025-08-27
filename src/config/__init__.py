import sys
import os
import locale

import matplotlib
import matplotlib.font_manager as fm

# Configuración más robusta para caracteres especiales
matplotlib.rcParams['font.sans-serif'] = [
    'Arial Unicode MS', 
    'DejaVu Sans', 
    'Liberation Sans',
    'Segoe UI',
    'Tahoma'
]
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['font.family'] = 'sans-serif'

# Forzar recarga de cache de fuentes si es necesario
try:
    fm._get_fontconfig_fonts.cache_clear()
except:
    pass

# Configuración global automática al importar config
if sys.platform.startswith('win'):
    try:
        locale.setlocale(locale.LC_ALL, 'Spanish_Spain.utf8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
        except:
            pass  # Si falla, continuar sin configurar locale

    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Solo reconfigurar si está disponible (no en Jupyter)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

from .logger_config import LoggerSetup, log_function, find_project_root

__all__ = ["LoggerSetup", "log_function", "find_project_root"]
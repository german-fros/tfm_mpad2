"""
Módulo de configuración del proyecto.
"""
from .logger_config import LoggerSetup, log_execution

__all__ = ["LoggerSetup", "log_execution"]  # Controla qué se importa cuando uso import *
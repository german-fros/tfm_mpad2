"""
APLICACIÓN PRINCIPAL - ROUTER MLS 2024

Router principal que maneja autenticación y redirección directa al dashboard.

PROPÓSITO:
- Verificar autenticación de usuarios
- Redireccionar inmediatamente a src/pages/1_Home.py tras login exitoso
- Proporcionar formularios de login/registro cuando sea necesario

FLUJO:
- Usuario accede -> Verificación auth -> Redirección directa a Home
- Sin pantallas intermedias, experiencia fluida
"""

import streamlit as st
import sys
from pathlib import Path
from typing import Optional

from src.config import LoggerSetup, log_function
from src.utils import require_authentication, get_current_user

# Configurar logger
logger_setup = LoggerSetup()
logger = logger_setup.setup_logger(__name__)

# Configuración de la página principal
st.set_page_config(
    page_title="MLS 2024 | Player Analysis",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="collapsed"
)


@log_function("apply_auth_styling")
def _apply_auth_styling() -> None:
    """
    Aplicar estilos mínimos para formularios de autenticación.
    """
    st.markdown(
        """
        <style>
            .stApp {
                background-color: #1A78CF;
                color: #FFFFFF;
            }
            
            .stDeployButton {
                display: none;
            }
            
            #MainMenu {
                visibility: hidden;
            }
            
            footer {
                visibility: hidden;
            }
        </style>
        """,
        unsafe_allow_html=True
    )


@log_function("redirect_to_home")
def _redirect_to_home() -> None:
    """
    Redireccionar inmediatamente a la página principal Home.
    """
    current_user = get_current_user()
    logger.info(f"Usuario autenticado {current_user}, redirigiendo a Home")
    st.switch_page("pages/1_Home.py")


@log_function("main")
def main() -> None:
    """
    Función principal que maneja autenticación y redirección directa.
    
    Flujo simple: autenticación -> redirección inmediata a Home
    """
    try:
        # Aplicar estilos mínimos para auth
        _apply_auth_styling()
        
        # Verificar autenticación
        if not require_authentication():
            logger.info("Usuario no autenticado, mostrando formulario de login")
            return
        
        # Usuario autenticado: redireccionar inmediatamente
        _redirect_to_home()
        
    except Exception as e:
        logger.error(f"Error en router principal: {str(e)}")
        st.error("Error al cargar la aplicación. Por favor, recarga la página.")


if __name__ == "__main__":
    main()
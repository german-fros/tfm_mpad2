import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from src.config import LoggerSetup, log_function, find_project_root
from src.utils import (
    require_authentication, 
    get_current_user, 
    get_user_info,
    load_players_season_stats
)

logger_setup = LoggerSetup()
logger = logger_setup.setup_logger(__name__)

# Configuración de la página
st.set_page_config(
    page_title="Home",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="collapsed"
)

@log_function("load_team_stats_optimized")
def load_team_stats_optimized() -> Optional[Dict[str, Any]]:
    """
    Cargar estadísticas básicas del equipo usando el data loader optimizado.
    
    Returns:
        Diccionario con estadísticas clave o None si hay error.
    """
    
    try:
        # Usar el data loader optimizado con solo las columnas necesarias
        essential_columns = ['player_name', 'goals', 'assists', 'games_played', 'team_name']
        df = load_players_season_stats(columns=essential_columns, use_summary=True)
        
        if df.empty:
            logger.warning("No se cargaron datos de jugadores")
            return None
            
        # Calcular estadísticas básicas
        stats = {
            'total_players': len(df),
            'total_goals': df['goals'].sum() if 'goals' in df.columns else 0,
            'total_assists': df['assists'].sum() if 'assists' in df.columns else 0,
            'games_played': df['games_played'].max() if 'games_played' in df.columns else 0,
            'top_scorer': df.loc[df['goals'].idxmax()]['player_name'] if 'goals' in df.columns and len(df) > 0 and df['goals'].sum() > 0 else "N/A"
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error cargando estadísticas del equipo: {str(e)}")
        return None


@log_function("main")
def main() -> None:
    """
    Función principal que orquesta la página de inicio.
    """

    st.markdown(
    """
    <style>
        /* Fondo general */
        .stApp {
            background-color: #001F5B;
            color: #FFFFFF; /* texto principal en blanco */
        }

        /* Encabezados */
        h1, h2, h3, h4, h5, h6 {
            color: #FFFFFF; /* todos los títulos en blanco */
        }

        /* Links */
        a {
            color: #FFD700; /* dorado para destacar enlaces */
        }

        /* Tablas y textos destacados */
        .stMarkdown, .stDataFrame, .stText {
            color: #FFFFFF;
        }

        /* Expander completo */
        details {
            border: none;
        }

        /* Header del expander (summary) */
        summary {
            background-color: #a11d16 !important;
            color: a11d16 !important;
            font-weight: bold;
            border-radius: 5px;
            padding: 6px;
        }

        /* Contenido interno del expander */
        details > div {
            background-color: #001F5B;
            color: white !important;
            padding: 10px;
            border-radius: 0 0 5px 5px;
        }

        button[data-testid="stBaseButton-secondary"] {
            background-color: #FFFFFF !important;
            color: #001F5B !important;
            border: 2px solid #001F5B !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            padding: 0.5em 1em !important;
        }

        button[data-testid="stBaseButton-secondary"]:hover {
            background-color: #001F5B !important;
            color: #FFFFFF !important;
            border: 2px solid #FFFFFF !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)
    
    # Verificar autenticación
    if not require_authentication():
        return
    
    # Obtener información del usuario para personalización
    current_user = get_current_user()
    user_info = get_user_info(current_user) if current_user else None
    
    # Si full_name está vacío o es None, usar current_user como fallback
    display_name = None
    if user_info:
        full_name = user_info.get('full_name', '').strip()
        display_name = full_name if full_name else current_user
    else:
        display_name = current_user
    
    st.markdown("<h1>Análisis Avanzado de Rendimiento</h1>",
                    unsafe_allow_html=True)
    col1, col2 = st.columns(spec=[0.7,0.3])
    with col1:
        st.markdown("<h2>Major League Soccer 23/24</h2>",
                    unsafe_allow_html=True)
    with col2:
        st.image("src/assets/mls_logo.png", width=100)

    st.markdown("---")

    col1,col2,col3 = st.columns(3)
    with col2:
        if st.button("⚽ COMENZAR ANÁLISIS", help="Análisis comparativo entre jugadores por posición", use_container_width=True):
            st.switch_page("pages/2_Players.py")

    st.markdown("<h3>Descripción</h3>",
                unsafe_allow_html=True)
    st.write("Esta aplicación ofrece diferentes visualizaciones comparativas entre jugadores de la misma posición, facilitando evaluaciones relevantes entre perfiles similares.")
    
    col1, col2 = st.columns(2)
    with col1:
        with st.expander('Métricas Básicas Comparativas'):
            st.write('''
                     Gráficos de barras horizontales que contrastan estadísticas generales, proporcionando una primera aproximación cuantitativa al rendimiento.''')
        with st.expander('Mapas de Calor'):
            st.write('''
                     Visualizaciones del campo que muestran las zonas de mayor participación de cada jugador, revelando patrones de movimiento y áreas de influencia que complementan las estadísticas tradicionales con información espacial.''')
        
    
    with col2:
        with st.expander('Análisis Radar'):
            st.write('''
                     Pizza charts que presentan métricas específicas normalizadas por 90 minutos según la posición seleccionada, ofreciendo una vista integral de las fortalezas y debilidades de cada jugador en múltiples dimensiones.''')
        with st.expander('Clustering por Perfiles'):
            st.write('''
                     Scatterplot que agrupa jugadores en clusters mediante técnicas de machine learning, identificando arquetipos dentro de cada posición y permitiendo descubrir jugadores con perfiles similares que podrían no ser evidentes mediante análisis convencional.''')
        
    
    # Separador
    st.markdown("---")
    
    # Footer
    st.markdown("""
                <div style='text-align: center; color: #666;'>
                <p>MLS Analysis Dashboard - Desarrollado con Streamlit</p>
                <p>Máster en Python Avanzado Aplicado al Deporte - Germán Fros</p>
                <p>2025</p></div>""",
                unsafe_allow_html=True)

if __name__ == "__main__":
    main()
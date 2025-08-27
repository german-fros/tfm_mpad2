import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Usar backend no-interactivo para evitar conflictos de visualización
import matplotlib.pyplot as plt
plt.ioff()  # Desactivar modo interactivo para prevenir sombras duplicadas
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.config.logger_config import LoggerSetup, log_function, find_project_root

from src.utils import (
    require_authentication, 
    get_current_user, 
    get_user_info,
    load_players_season_stats,
    load_all_events_data,
    get_team_names,
    get_players_for_team_and_position
)

logger_setup = LoggerSetup()
logger = logger_setup.setup_logger(__name__)


# Traducciones de métricas al español
METRIC_TRANSLATIONS = {
    # General metrics
    "games_played": "Partidos jugados",
    "appearances": "Apariciones",
    "goals": "Goles",
    "assists": "Asistencias",
    "goal_assists": "Asistencias de gol",
    
    # Shooting metrics
    "goals_p90": "Goles p/90",
    "total_shots_p90": "Disparos totales p/90",
    "shots_on_target_p90": "Disparos al arco p/90",
    "total_touches_in_opposition_box_p90": "Toques en área rival p/90",
    
    # Passing metrics
    "total_successful_passes_p90": "Pases exitosos p/90",
    "key_passes_p90": "Pases clave p/90",
    "assists_p90": "Asistencias p/90",
    
    # Dribbling metrics
    "successful_dribbles_p90": "Regates exitosos p/90",
    
    # Defensive metrics
    "interceptions_p90": "Intercepciones p/90",
    "recoveries_p90": "Recuperaciones p/90",
    "tackles_won_p90": "Entradas ganadas p/90",
    "aerial_duels_won_p90": "Duelos aéreos ganados p/90",
    "ground_duels_won_p90": "Duelos terrestres ganados p/90",
    "duels_won_p90": "Duelos ganados p/90",
    "total_fouls_conceded_p90": "Faltas cometidas p/90",
    
    # Goalkeeper metrics
    "saves_made_p90": "Paradas realizadas p/90",
    "penalties_saved_p90": "Penales atajados p/90",
    "goals_conceded_p90": "Goles recibidos p/90",
    "clean_sheets_p90": "Vallas invictas p/90",
    "gk_successful_distribution_p90": "Distribución exitosa p/90"
}

# Métricas específicas por posición para pizza charts
POSITION_METRICS = {
    "Goalkeeper": [
        "games_played",
        "saves_made_p90",
        "penalties_saved_p90", 
        "goals_conceded_p90",
        "clean_sheets_p90",
        "gk_successful_distribution_p90"
    ],
    "Defender": [
        "games_played",
        "total_successful_passes_p90",
        "interceptions_p90",
        "recoveries_p90",
        "ground_duels_won_p90",
        "aerial_duels_won_p90",
        "total_fouls_conceded_p90",
        "tackles_won_p90"
    ],
    "Midfielder": [
        "games_played",
        "key_passes_p90",
        "successful_dribbles_p90",
        "recoveries_p90",
        "goal_assists_p90",
        "assists_p90",
        "duels_won_p90",
        "total_successful_passes_p90",
        "goals_p90",
        "total_shots_p90"
    ],
    "Forward": [
        "games_played",
        "goals_p90",
        "total_successful_passes_p90",
        "successful_dribbles_p90",
        "shots_on_target_p90",
        "goal_assists_p90",
        "key_passes_p90",
        "total_touches_in_opposition_box_p90",
        "total_shots_p90",
    ]
}


# Configuración de la página
st.set_page_config(
    page_title="Comparación de Jugadores - MLS",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)


@log_function("create_team_player_filters_for_position")
def _create_team_player_filters_for_position(position: str, tab_key: str) -> Dict[str, Any]:
    """
    Crear filtros para selección de equipos y jugadores para una posición específica.
    
    Args:
        position: Posición específica para filtrar jugadores.
        tab_key: Clave única para el tab para evitar conflictos de session state.
    
    Returns:
        Diccionario con las selecciones de equipos y jugadores.
    """
    position_dict ={
        "Forward": 'Delanteros',
        "Midfielder": 'Mediocampistas',
        "Defender": 'Defensores',
        "Goalkeeper": 'Porteros'
    }
    
    col1, col2, col3 = st.columns([0.25,0.5,0.25])
    with col2:
        st.markdown(f"""
                    <div style='text_allign: center'>
                    <h3 >🔍 Selecciona {position_dict[position]} para comparar</h3>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Obtener equipos disponibles
    team_names = get_team_names()
    
    if not team_names:
        st.error("No se encontraron equipos disponibles")
        return {}
    
    # Crear columnas para los filtros
    col1, col2, col3, col4 = st.columns([0.2,0.4,0.4,0.2])
    
    with col2:
        st.markdown("**Equipo 1:**")
        team1 = st.selectbox(
            "Selecciona el primer equipo",
            options=team_names,
            index=0,
            key=f'team1_filter_{tab_key}',
            label_visibility="collapsed"
        )
    
        st.markdown("**Jugador 1:**")
        if team1:
            players1 = get_players_for_team_and_position(team1, position)
            if players1:
                player1 = st.selectbox(
                    "Selecciona el primer jugador",
                    options=players1,
                    index=0,
                    key=f'player1_filter_{tab_key}',
                    label_visibility="collapsed"
                )
            else:
                st.warning(f"No hay {position.lower()}s disponibles en este equipo")
                player1 = None
        else:
            player1 = None
    
    with col3:
        st.markdown("**Equipo 2:**")
        # Filtrar para que no sea el mismo equipo que team1
        available_teams2 = [team for team in team_names if team != team1]
        if available_teams2:
            team2 = st.selectbox(
                "Selecciona el segundo equipo",
                options=available_teams2,
                index=0,
                key=f'team2_filter_{tab_key}',
                label_visibility="collapsed"
            )
        else:
            st.error("No hay otros equipos disponibles")
            team2 = None
    
        st.markdown("**Jugador 2:**")
        if team2:
            players2 = get_players_for_team_and_position(team2, position)
            if players2:
                player2 = st.selectbox(
                    "Selecciona el segundo jugador",
                    options=players2,
                    index=0,
                    key=f'player2_filter_{tab_key}',
                    label_visibility="collapsed"
                )
            else:
                st.warning(f"No hay {position.lower()}s disponibles en este equipo")
                player2 = None
        else:
            player2 = None
    
    return {
        'team1': team1,
        'position': position,
        'player1': player1,
        'team2': team2,
        'player2': player2
    }


@log_function("create_basic_metrics_section_for_position")
def _create_basic_metrics_section_for_position(position: str, selections: Dict[str, Any]) -> None:
    """
    Crear sección con gráfico de métricas básicas de comparación para una posición específica.
    
    Args:
        position: Posición específica de los jugadores.
        selections: Diccionario con selecciones de equipos y jugadores.
    """
    # Usar placeholder para evitar duplicación de contenido
    metrics_placeholder = st.empty()
    with metrics_placeholder.container():
        if not all([selections.get('team1'), selections.get('player1'), 
                    selections.get('team2'), selections.get('player2')]):
            st.info("Selecciona jugadores de ambos equipos para ver la comparación de métricas básicas")
        else:
            try:
                # Cargar datos de jugadores
                all_players_stats = load_players_season_stats()
                
                # Crear gráfico de métricas básicas
                from src.utils.visualizations import create_basic_metrics_comparison_chart
                
                fig_metrics = create_basic_metrics_comparison_chart(
                    player1_name=selections['player1'],
                    player1_team=selections['team1'],
                    player2_name=selections['player2'],
                    player2_team=selections['team2'],
                    all_players_stats=all_players_stats
                )
                
                st.pyplot(fig_metrics, use_container_width=True)
                plt.close(fig_metrics)  # Limpiar figura para evitar sombras duplicadas
                
            except Exception as e:
                logger.error(f"Error creando gráfico de métricas básicas para {position}: {str(e)}")
                st.error(f"Error generando comparación de métricas: {str(e)}")


@log_function("create_pizza_comparison_section_for_position")
def _create_pizza_comparison_section_for_position(position: str, selections: Dict[str, Any]) -> None:
    """
    Crear sección con pizza plot de comparación para una posición específica.
    
    Args:
        position: Posición específica de los jugadores.
        selections: Diccionario con selecciones de equipos y jugadores.
    """
    # Usar placeholder para evitar duplicación de contenido
    pizza_placeholder = st.empty()
    with pizza_placeholder.container():
        if not all([selections.get('team1'), selections.get('player1'), 
                    selections.get('team2'), selections.get('player2')]):
            st.info("Selecciona jugadores de ambos equipos para ver la comparación")
        else:
            try:
                # Cargar datos de jugadores
                all_players_stats = load_players_season_stats()
                
                # Crear pizza plot
                from src.utils.visualizations import create_pizza_comparison
                
                fig_pizza = create_pizza_comparison(
                    player1_name=selections['player1'],
                    player1_team=selections['team1'],
                    player1_position=position,
                    player2_name=selections['player2'],
                    player2_team=selections['team2'],
                    player2_position=position,
                    all_players_stats=all_players_stats,
                    position_metrics=POSITION_METRICS,
                    metric_translations=METRIC_TRANSLATIONS
                )
                
                st.pyplot(fig_pizza, use_container_width=True)
                plt.close(fig_pizza)  # Limpiar figura para evitar sombras duplicadas
                
            except Exception as e:
                logger.error(f"Error creando pizza plot para {position}: {str(e)}")
                st.error(f"Error generando comparación: {str(e)}")


@log_function("create_heatmap_comparison_section_for_position") 
def _create_heatmap_comparison_section_for_position(position: str, selections: Dict[str, Any]) -> None:
    """
    Crear sección con mapas de calor de comparación para una posición específica.
    
    Args:
        position: Posición específica de los jugadores.
        selections: Diccionario con selecciones de equipos y jugadores.
    """
    # Usar placeholder para evitar duplicación de contenido
    heatmap_placeholder = st.empty()
    with heatmap_placeholder.container():
        if not all([selections.get('player1'), selections.get('player2')]):
            st.info("Selecciona jugadores de ambos equipos para ver los mapas de calor")
        else:
            try:
                # Cargar datos de eventos optimizados solo para los jugadores seleccionados
                all_events_data = load_all_events_data(
                    columns=['playerName', 'x', 'y'],
                    player_names=[selections['player1'], selections['player2']]
                )
                
                # Crear heatmap comparison
                from src.utils.visualizations import create_heatmap_comparison
                
                fig_heatmap = create_heatmap_comparison(
                    player1_name=selections['player1'],
                    player2_name=selections['player2'],
                    events_data=all_events_data
                )
                
                # Mostrar el gráfico
                st.pyplot(fig_heatmap, use_container_width=False)
                plt.close(fig_heatmap)  # Limpiar figura para evitar sombras duplicadas
                
            except Exception as e:
                logger.error(f"Error creando heatmap comparison para {position}: {str(e)}")
                st.error(f"Error generando mapas de calor: {str(e)}")


@log_function("create_clustering_analysis_section_for_position")
def _create_clustering_analysis_section_for_position(position: str, selections: Dict[str, Any]) -> None:
    """
    Crear sección con análisis de clustering para jugadores de una posición específica.
    
    Args:
        position: Posición específica de los jugadores.
        selections: Diccionario con selecciones de equipos y jugadores.
    """
    # Usar placeholder para evitar duplicación de contenido
    clustering_placeholder = st.empty()
    with clustering_placeholder.container():
        if not all([selections.get('player1'), selections.get('player2')]):
            st.info("Selecciona jugadores de ambos equipos para ver el análisis de clustering")
        else:
            try:
                # Cargar datos de jugadores
                all_players_stats = load_players_season_stats()

                # Preparar dataset
                from src.utils.modelling import prep_data_modelling

                prepared_data, players_name = prep_data_modelling(all_players_stats)
                
                # Crear visualización de clustering con jugadores destacados
                from src.utils.visualizations import create_player_clustering_visualization
                
                fig_clustering, cluster_info = create_player_clustering_visualization(
                    position=position,
                    player1_name=selections['player1'],
                    player2_name=selections['player2'],
                    prepared_data=prepared_data,
                    players_name=players_name
                )
                
                # Mostrar el gráfico
                st.pyplot(fig_clustering, use_container_width=False)
                plt.close(fig_clustering)  # Limpiar figura para evitar sombras duplicadas
                
            except Exception as e:
                logger.error(f"Error creando análisis de clustering para {position}: {str(e)}")
                st.error(f"Error generando clustering: {str(e)}")


@log_function("create_position_tab_content")
def _create_position_tab_content(position: str, position_emoji: str) -> None:
    """
    Crear contenido completo para un tab de posición específica.
    
    Args:
        position: Nombre de la posición (ej. "Goalkeeper", "Defender", etc.).
        position_emoji: Emoji representativo de la posición.
    """
    try:
        # Crear clave única para el tab
        tab_key = position.lower()
        
        # Crear filtros específicos para esta posición con placeholder para evitar duplicación
        filter_placeholder = st.empty()
        with filter_placeholder.container():
            # Crear espacios laterales para centrar el contenido
            left_space, filter_col, right_space = st.columns([1, 3, 1])
            with filter_col:
                selections = _create_team_player_filters_for_position(position, tab_key)
        
        # Crear visualizaciones si se han seleccionado jugadores
        if selections and all([selections.get('player1'), selections.get('player2')]):

            position_dict ={
                "Forward": 'Delanteros',
                "Midfielder": 'Mediocampistas',
                "Defender": 'Defensores',
                "Goalkeeper": 'Porteros'
            }

            st.markdown("---")
            
            col1, col2, col3, col4, col5 = st.columns([0.1,0.25,0.35,0.25,0.1], gap='small')
            with col2:
                with st.container(border=True):
                    st.markdown(f"""
                        <h3 style='font-size: 30px; font-weight: bold; text-align: center; margin: 20px 0; color: white; background-color: #BE322B; padding: 5px; border-radius: 5px'>{selections.get('player1').upper()}</h3>
                        """, unsafe_allow_html=True
                    )
                    st.image('src/assets/player_shadow.png', width=300)
            with col3:
                _create_basic_metrics_section_for_position(position, selections)
            with col4:
                with st.container(border=True):
                    st.markdown(f"""
                        <h3 style='font-size: 30px; font-weight: bold; text-align: center; margin: 20px 0; color: white; background-color: #1A78CF; padding: 5px; border-radius: 5px'>{selections.get('player2').upper()}</h3>
                        """, unsafe_allow_html=True
                    )
                    st.image('src/assets/player_shadow.png', width=300)

            col1, col2, col3, col4, col5 = st.columns([0.02,0.3,0.3,0.3,0.02], gap='small')

            with col2:
                st.markdown(f"""
                    <div style='text_allign: center'>
                    <h3 >Métricas por 90 minutos</h3>
                    </div>
                    """, unsafe_allow_html=True)
                
                _create_pizza_comparison_section_for_position(position, selections)
                
            with col3:
                _create_heatmap_comparison_section_for_position(position, selections)

            with col4:
                st.markdown(f"""
                    <div style='text_allign: center; padding:-10'>
                    <h3 >Clustering | Perfiles de {position_dict.get(position)}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                
                _create_clustering_analysis_section_for_position(position, selections)
                
            st.markdown("---")
                
        else:
            st.info(f"Completa la selección de {position.lower()}s para ver las comparaciones")

        # Centrar botón de PDF
        pdf_col1, pdf_col2, pdf_col3 = st.columns([1, 2, 1])
        with pdf_col2:
            if st.button("📄 Generar Comparación PDF", 
                        key=f"pdf_export_{tab_key}",
                        help=f"Descargar comparación completa de {position.lower()}s en formato PDF",
                        use_container_width=True):
                
                # Generar visualizaciones para PDF con manejo aislado
                with st.spinner("Generando PDF..."):
                    try:
                        # Crear contenedor aislado para PDF evitando interferencias UI
                        pdf_generation_container = st.empty()
                        
                        visualizations = _capture_visualizations_for_pdf(position, selections)
                        
                        # Importar función de PDF
                        from src.utils.streamlit import create_pdf_download_button
                        
                        # Crear botón de descarga en contenedor aislado
                        with pdf_generation_container.container():
                            create_pdf_download_button(
                                position=position,
                                player1_name=selections['player1'],
                                player1_team=selections['team1'],
                                player2_name=selections['player2'],  
                                player2_team=selections['team2'],
                                visualizations=visualizations
                            )
                        
                    except Exception as e:
                        logger.error(f"Error generando PDF para {position}: {str(e)}")
                        st.error(f"Error generando PDF: {str(e)}")
        
        st.markdown("---")
            
    except Exception as e:
        logger.error(f"Error en tab de {position}: {str(e)}")
        st.error(f"Error cargando datos para {position}: {str(e)}")
        st.info("Verifica que todos los archivos de datos estén disponibles")


@log_function("capture_visualizations_for_pdf")
def _capture_visualizations_for_pdf(position: str, selections: Dict[str, Any]) -> Dict[str, Any]:
    """
    Capturar todas las visualizaciones de un tab para incluir en PDF.
    
    Args:
        position: Posición específica de los jugadores.
        selections: Diccionario con selecciones de equipos y jugadores.
        
    Returns:
        Diccionario con las figuras de matplotlib capturadas.
    """
    import matplotlib
    visualizations = {}
    
    # Usar backend no-interactivo para evitar artifacts durante captura
    original_backend = matplotlib.get_backend()
    matplotlib.use('Agg')
    
    try:
        # Cargar datos necesarios
        all_players_stats = load_players_season_stats()
        all_events_data = load_all_events_data(
            columns=['playerName', 'x', 'y'],
            player_names=[selections['player1'], selections['player2']]
        )
        
        # 1. Capturar Basic Metrics Comparison
        try:
            from src.utils.visualizations import create_basic_metrics_comparison_chart
            fig_metrics = create_basic_metrics_comparison_chart(
                player1_name=selections['player1'],
                player1_team=selections['team1'],
                player2_name=selections['player2'],
                player2_team=selections['team2'],
                all_players_stats=all_players_stats
            )
            visualizations['Métricas Básicas de Comparación'] = fig_metrics
        except Exception as e:
            logger.error(f"Error capturando métricas básicas: {str(e)}")
            visualizations['Métricas Básicas de Comparación'] = None
        
        # 2. Capturar Pizza Plot
        try:
            from src.utils.visualizations import create_pizza_comparison
            fig_pizza = create_pizza_comparison(
                player1_name=selections['player1'],
                player1_team=selections['team1'],
                player1_position=position,
                player2_name=selections['player2'],
                player2_team=selections['team2'],
                player2_position=position,
                all_players_stats=all_players_stats,
                position_metrics=POSITION_METRICS,
                metric_translations=METRIC_TRANSLATIONS,
                pdf=True
            )
            visualizations['Comparación Pizza Plot'] = fig_pizza
        except Exception as e:
            logger.error(f"Error capturando pizza plot: {str(e)}")
            visualizations['Comparación Pizza Plot'] = None
        
        # 3. Capturar Heatmap
        try:
            from src.utils.visualizations import create_heatmap_comparison
            fig_heatmap = create_heatmap_comparison(
                player1_name=selections['player1'],
                player2_name=selections['player2'],
                events_data=all_events_data
            )
            visualizations['Mapa de Calor de Posiciones'] = fig_heatmap
        except Exception as e:
            logger.error(f"Error capturando heatmap: {str(e)}")
            visualizations['Mapa de Calor de Posiciones'] = None
        
        # 4. Capturar Clustering Analysis
        try:
            from src.utils.modelling import prep_data_modelling
            from src.utils.visualizations import create_player_clustering_visualization
            
            prepared_data, players_name = prep_data_modelling(all_players_stats)
            fig_clustering, cluster_info = create_player_clustering_visualization(
                position=position,
                player1_name=selections['player1'],
                player2_name=selections['player2'],
                prepared_data=prepared_data,
                players_name=players_name
            )
            visualizations['Análisis de Clustering'] = fig_clustering
        except Exception as e:
            logger.error(f"Error capturando clustering: {str(e)}")
            visualizations['Análisis de Clustering'] = None
        
        return visualizations
        
    except Exception as e:
        logger.error(f"Error capturando visualizaciones para PDF: {str(e)}")
        return {}
    
    finally:
        # Restaurar backend original para evitar problemas posteriores
        matplotlib.use(original_backend)


@log_function()
def main() -> None:
    """
    Función principal que orquesta la página de comparación de jugadores con tabs por posición.
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
    
    # Crear header de bienvenida
    
    try:
        st.markdown("<h1>Análisis Avanzado de Rendimiento</h1>",
                    unsafe_allow_html=True)
        col1, col2 = st.columns(spec=[0.7,0.3])
        with col1:
            st.markdown("<h2>Major League Soccer 23/24</h2>",
                        unsafe_allow_html=True)
        with col2:
            st.image("src/assets/mls_logo.png", width=100)
        
        # Crear tabs para cada posición
        forward_tab, midfielder_tab, defender_tab, goalkeeper_tab = st.tabs([
            "🎯 Delanteros",
            "⚽ Centrocampistas",
            "🛡️ Defensores", 
            "🥅 Porteros"
        ])

        # Contenido del tab de Delanteros
        with forward_tab:
            _create_position_tab_content("Forward", "🎯")

        # Contenido del tab de Centrocampistas
        with midfielder_tab:
            _create_position_tab_content("Midfielder", "⚽")

        # Contenido del tab de Defensores    
        with defender_tab:
            _create_position_tab_content("Defender", "🛡️")

        # Contenido del tab de Porteros
        with goalkeeper_tab:
            _create_position_tab_content("Goalkeeper", "🥅")
            
    except Exception as e:
        logger.error(f"Error en página de comparación: {str(e)}")
        st.error(f"Error cargando datos: {str(e)}")
        st.info("Verifica que todos los archivos de datos estén disponibles")

    # Footer
    st.markdown("""
                <div style='text-align: center; color: white;'>
                <p>MLS Analysis Dashboard - Desarrollado con Streamlit</p>
                <p>Máster en Python Avanzado Aplicado al Deporte - Germán Fros</p>
                <p>2025</p>""",
                unsafe_allow_html=True)


if __name__ == "__main__":
    main()
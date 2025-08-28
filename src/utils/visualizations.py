from mplsoccer import Pitch, VerticalPitch
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import matplotlib
matplotlib.use('Agg')  # Usar backend no-interactivo para evitar conflictos
import matplotlib.pyplot as plt
plt.ioff()  # Desactivar modo interactivo
from matplotlib import colormaps
import seaborn as sns

from src.config.logger_config import LoggerSetup, log_function, find_project_root

# Configuración de logger inicial
logger_setup = LoggerSetup()
logger = logger_setup.setup_logger(__name__)


@log_function("create_pizza_comparison")
def create_pizza_comparison(
    player1_name: str, 
    player1_team: str, 
    player1_position: str, 
    player2_name: str, 
    player2_team: str, 
    player2_position: str, 
    all_players_stats: pd.DataFrame, 
    position_metrics: Dict[str, List[str]],
    metric_translations: Optional[Dict[str, str]] = None,
    pdf: bool = False
    ) -> plt.Figure:
    """
    Crear pizza plot de comparación entre dos jugadores usando mplsoccer con métricas específicas por posición.
    
    Args:
        player1_name: Nombre del primer jugador.
        player1_team: Equipo del primer jugador.
        player1_position: Posición del primer jugador.
        player2_name: Nombre del segundo jugador.
        player2_team: Equipo del segundo jugador.
        player2_position: Posición del segundo jugador.
        all_players_stats: DataFrame con estadísticas de todos los jugadores.
        position_metrics: Diccionario con métricas específicas por posición.
        metric_translations: Diccionario opcional con traducciones de métricas al español.
        pdf: True para que el color del texto sea negro para el PDF de descarga.
        
    Returns:
        Figura con el pizza plot de comparación.
    """
    from mplsoccer import PyPizza, FontManager

    font_normal = FontManager('https://raw.githubusercontent.com/googlefonts/roboto/main/'
                          'src/hinted/Roboto-Regular.ttf')
    font_italic = FontManager('https://raw.githubusercontent.com/googlefonts/roboto/main/'
                            'src/hinted/Roboto-Italic.ttf')
    font_bold = FontManager('https://raw.githubusercontent.com/google/fonts/main/apache/robotoslab/'
                            'RobotoSlab[wght].ttf')

    # Obtener estadísticas de los jugadores
    player1_stats = all_players_stats[
        (all_players_stats['player_name'] == player1_name) & 
        (all_players_stats['team_name'] == player1_team)
    ]
    
    player2_stats = all_players_stats[
        (all_players_stats['player_name'] == player2_name) & 
        (all_players_stats['team_name'] == player2_team)
    ]
    
    # Determinar métricas basadas en las posiciones de los jugadores
    # Si ambos jugadores son de la misma posición, usar esas métricas
    # Si no, usar métricas generales o de la primera posición
    if player1_position == player2_position and player1_position in position_metrics:
        metrics = position_metrics[player1_position]
    elif player1_position in position_metrics:
        metrics = position_metrics[player1_position]
    elif player2_position in position_metrics:
        metrics = position_metrics[player2_position]
    else:
        # Métricas por defecto si no se encuentra la posición
        metrics = [
            'goals', 'assists', 'total_shots', 'passes_%',
            'key_passes', 'tackles', 'interceptions', 'recoveries'
        ]

    min_range = []
    max_range = []

    for metric in metrics:
        min = 0
        max = all_players_stats[metric].max()

        min_range.append(min)
        max_range.append(max)

    # Obtener primera fila de cada jugador
    p1_stats = player1_stats.iloc[0]
    p2_stats = player2_stats.iloc[0]

    # Extraer valores de métricas específicas para cada jugador
    p1_values = []
    p2_values = []
    
    for metric in metrics:
        # Obtener valor del jugador 1
        p1_val = p1_stats.get(metric, 0) if metric in p1_stats.index else 0
        p2_val = p2_stats.get(metric, 0) if metric in p2_stats.index else 0
        
        p1_values.append(p1_val)
        p2_values.append(p2_val)

    # Traducir nombres de métricas para mostrar en el pizza plot
    if metric_translations:
        translated_metrics = [metric_translations.get(metric, metric) for metric in metrics]
    else:
        translated_metrics = metrics

    # Crear el pizza plot con valores originales
    baker = PyPizza(
        params=translated_metrics,
        background_color="#001F5B", 
        straight_line_color="#FFFFFF",
        last_circle_color="#FFFFFF", 
        last_circle_lw=1.5, 
        other_circle_lw=0,
        other_circle_color="#FFFFFF", 
        straight_line_lw=0.7,
        min_range=min_range,
        max_range=max_range
    )

    text_color = '#F2F2F2'
    
    if pdf:
        text_color = '000000'


    # Crear la pizza
    fig, ax = baker.make_pizza(
        p1_values,                    # valores jugador 1
        compare_values=p2_values,     # valores jugador 2
        figsize=(3, 4),             # tamaño de la figura
        color_blank_space="same",     # usar mismo color para espacios en blanco
        blank_alpha=0.4,              # transparencia para espacios en blanco
        param_location=110,           # ubicación de los parámetros
        kwargs_slices=dict(
            facecolor="#1A78CF", edgecolor="#1A78CF",
            zorder=1, linewidth=1
        ),                            # estilo para jugador 1
        kwargs_compare=dict(
            facecolor="#BE322B", edgecolor="#BE322B", 
            zorder=3, linewidth=1
        ),                            # estilo para jugador 2
        kwargs_params=dict(
            color=text_color, fontsize=6, zorder=5,
            fontproperties=font_normal.prop, va="center"
        ),                          # values to be used when adding parameter
        kwargs_values=dict(
            color="#000000", fontsize=6,
            fontproperties=font_normal.prop, zorder=3,
            bbox=dict(
                edgecolor="#000000", facecolor="#1A78CF",
                boxstyle="round,pad=0.2", lw=1, alpha=0
            ), alpha=0
        ),                           # values to be used when adding parameter-values
        kwargs_compare_values=dict(
            color="#000000", fontsize=6,
            fontproperties=font_normal.prop, zorder=3,
            bbox=dict(
                edgecolor="#000000", facecolor="#BE322B",
                boxstyle="round,pad=0.2", lw=1, alpha=0
            ), alpha=0
        )                            # values to be used when adding comparison-values
    )
    
    # Configurar el fondo y eliminar bordes
    fig.set_facecolor('#001F5B')
    ax.set_facecolor('#001F5B')
    fig.subplots_adjust(left=0.05, right=0.95)
    
    # # Añadir leyenda con colores que coincidan con el pizza plot
    # legend_elements = [
    #     plt.Line2D([0], [0], marker='o', color='#1A78CF', markerfacecolor='#1A78CF', 
    #                markersize=5, label=f'{player1_name}'),
    #     plt.Line2D([0], [0], marker='o', color='#ff9300', markerfacecolor='#ff9300', 
    #                markersize=5, label=f'{player2_name}')
    # ]
    
    # ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1.1), 
    #           frameon=False, labelcolor='white', fontsize=6, alignment='left')
    plt.tight_layout()
    
    logger.info(f"Pizza plot creado exitosamente para {player1_name} vs {player2_name}")
    return fig


@log_function("create_heatmap_comparison")
def create_heatmap_comparison(player1_name: str, player2_name: str, 
                            events_data: pd.DataFrame) -> plt.Figure:
    """
    Crear mapas de calor duales para comparar posiciones de dos jugadores.
    
    Args:
        player1_name: Nombre del primer jugador.
        player2_name: Nombre del segundo jugador.
        events_data: DataFrame con datos de eventos de toda la temporada.
        
    Returns:
        Figura con dos campos de fútbol lado a lado con mapas de calor.
    """
    # Filtrar eventos por jugador
    p1_events = events_data[events_data['playerName'] == player1_name].copy()
    p2_events = events_data[events_data['playerName'] == player2_name].copy()
    
    # Limpiar coordenadas (remover NaN)
    p1_events = p1_events.dropna(subset=['x', 'y'])
    p2_events = p2_events.dropna(subset=['x', 'y'])
    
    # Crear figura con dos subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    fig.set_facecolor('#001F5B')
    
    # Crear pitches
    pitch1 = VerticalPitch(
        pitch_type='opta',
        pitch_color='#0e1117',
        line_color='white',
        linewidth=2
    )
    
    pitch2 = VerticalPitch(
        pitch_type='opta',
        pitch_color='#0e1117',
        line_color='white',
        linewidth=2
    )
    
    # Dibujar pitches
    pitch1.draw(ax=ax1)
    pitch2.draw(ax=ax2)
    
    # Configurar fondo sin bordes
    for ax in [ax1, ax2]:
        ax.set_facecolor('black')
        ax.set_position([ax.get_position().x0, ax.get_position().y0, 
                        ax.get_position().width, ax.get_position().height])
    
    fig.subplots_adjust(left=0.05, right=0.4, top=0.9, bottom=0.1, wspace=0.1)
    
    # Heatmap para jugador 1
    if not p1_events.empty:
        pitch1.kdeplot(
            x=p1_events['x'], y=p1_events['y'], 
            ax=ax1,
            cmap='inferno',
            fill=True,
            alpha=0.7,
            levels=15,
            thresh=0.1,
            cut = 8
        )
        # ax1.set_title(f'{player1_name}', color='white', fontsize=12, weight='bold', pad=10)
    else:
        ax1.text(50, 50, f'Sin datos de posición\npara {player1_name}',
                ha='center', va='center', color='white', fontsize=12, weight='bold')
        ax1.set_title(f'{player1_name}', 
                     color='white', fontsize=12, pad=10)
    
    # Heatmap para jugador 2
    if not p2_events.empty:
        pitch2.kdeplot(
            x=p2_events['x'], y=p2_events['y'], 
            ax=ax2,
            cmap='inferno',
            fill=True,
            alpha=0.7,
            levels=15,
            thresh=0.1,
            cut = 8
        )
        # ax2.set_title(f'{player2_name}', color='white', fontsize=12, pad=10)
    else:
        ax2.text(50, 50, f'Sin datos de posición\npara {player2_name}',
                ha='center', va='center', color='white', fontsize=12, weight='bold')
        ax2.set_title(f'{player2_name}\nHeatmap de Posiciones', 
                     color='white', fontsize=14, weight='bold', pad=20)
    
    # Añadir flechas de dirección de ataque para ambos campos
    for ax in [ax1, ax2]:
        ax.arrow(-2, 30, 0, 40, head_width=1, head_length=0.9, 
                color='gray', linewidth=1, alpha=0.7, zorder=10, 
                length_includes_head=True)
        ax.arrow(102, 30, 0, 40, head_width=1, head_length=0.9, 
                color='gray', linewidth=1, alpha=0.7, zorder=10, 
                length_includes_head=True)
    
    return fig


@log_function("create_basic_metrics_comparison_chart")
def create_basic_metrics_comparison_chart(
    player1_name: str, 
    player1_team: str,
    player2_name: str, 
    player2_team: str,
    all_players_stats: pd.DataFrame
) -> plt.Figure:
    """
    Crear gráfico de barras horizontal para comparación básica de métricas entre dos jugadores.
    
    Args:
        player1_name: Nombre del primer jugador.
        player1_team: Equipo del primer jugador.
        player2_name: Nombre del segundo jugador.
        player2_team: Equipo del segundo jugador.
        all_players_stats: DataFrame con estadísticas de todos los jugadores.
        
    Returns:
        Figura con gráfico de barras horizontal de comparación.
    """
    # Métricas básicas a comparar
    basic_metrics = ['appearances', 'goals', 'goal_assists', 'passes_%', 'dribble_%', 'duels_%'][::-1]
    metric_labels = ['Partidos', 'Goles', 'Asistencias', 'Pases %', 'Dribbles %', 'Duelos %'][::-1]
    
    # Obtener estadísticas de los jugadores
    player1_stats = all_players_stats[
        (all_players_stats['player_name'] == player1_name) & 
        (all_players_stats['team_name'] == player1_team)
    ]
    
    player2_stats = all_players_stats[
        (all_players_stats['player_name'] == player2_name) & 
        (all_players_stats['team_name'] == player2_team)
    ]
    
    if player1_stats.empty or player2_stats.empty:
        # Crear figura vacía con mensaje de error
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.set_facecolor('#001F5B')
        ax.set_facecolor('#001F5B')
        ax.text(0.5, 0.5, 'No se encontraron datos para los jugadores seleccionados',
                ha='center', va='center', color='white', fontsize=14, weight='bold')
        ax.axis('off')
        return fig
    
    # Obtener primera fila de cada jugador
    p1_stats = player1_stats.iloc[0]
    p2_stats = player2_stats.iloc[0]
    
    # Extraer valores para cada métrica usando las columnas pre-calculadas
    p1_values = []
    p2_values = []
    
    for metric in basic_metrics:
        p1_val = p1_stats.get(metric, 0)
        p2_val = p2_stats.get(metric, 0)
        p1_values.append(p1_val)
        p2_values.append(p2_val)
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.set_facecolor('#001F5B')
    ax.set_facecolor('#001F5B')
    
    # Configuración de colores
    player1_color = "#BE322B"  # Orange
    player2_color = '#1A78CF'  # Blue
    
    # Configurar barras
    bar_height = 0.6
    y_positions = np.arange(len(basic_metrics))
    
    # Para cada métrica, crear barra horizontal dividida
    for i, (p1_val, p2_val, label) in enumerate(zip(p1_values, p2_values, metric_labels)):
        y = y_positions[i]
        
        # Manejar caso donde ambos valores son 0
        if p1_val == 0 and p2_val == 0:
            total = 1  # Evitar división por cero
            p1_ratio = 0.5
            p2_ratio = 0.5
        else:
            total = p1_val + p2_val
            if total == 0:
                p1_ratio = 0.5
                p2_ratio = 0.5
            else:
                p1_ratio = p1_val / total
                p2_ratio = p2_val / total
        
        # Dibujar barra del jugador 1 (izquierda)
        ax.barh(y, p1_ratio, height=bar_height, left=0, 
                color=player1_color, alpha=0.8, edgecolor='white', linewidth=1)
        
        # Dibujar barra del jugador 2 (derecha)  
        ax.barh(y, p2_ratio, height=bar_height, left=p1_ratio,
                color=player2_color, alpha=0.8, edgecolor='white', linewidth=1)
        
        # Añadir valores fuera de las barras
        # Valor jugador 1 (izquierda, fuera de la barra)
        if '%' in label:
            p1_text = f"{int(p1_val)}%"
        elif isinstance(p1_val, float) and 'e-' not in str(p1_val):
            p1_text = f"{p1_val:.1f}"
        else:
            p1_text = f"{p1_val:.0f}"
            
        ax.text(-0.02, y, p1_text, ha='right', va='center', 
                color='white', fontweight='bold', fontsize=18)
        
        # Valor jugador 2 (derecha, fuera de la barra)
        if '%' in label:
            p2_text = f"{int(p2_val)}%"
        elif isinstance(p2_val, float) and 'e-' not in str(p2_val):
            p2_text = f"{p2_val:.1f}"
        else:
            p2_text = f"{p2_val:.0f}"
            
        ax.text(1.02, y, p2_text, ha='left', va='center', 
                color='white', fontweight='bold', fontsize=18)
        
        # Añadir etiqueta de métrica en el centro de la barra
        ax.text(0.5, y, label, ha='center', va='center', 
                color='black', fontweight='bold', fontsize=18, 
                bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.9))
    
    # Configurar ejes
    ax.set_xlim(-0.15, 1.15)
    ax.set_ylim(-0.5, len(basic_metrics) - 0.5)
    ax.set_yticks([])
    ax.set_xticks([])
    
    # Remover spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    plt.tight_layout()
    
    logger.info(f"Gráfico de métricas básicas creado exitosamente para {player1_name} vs {player2_name}")
    return fig


@log_function("create_player_clustering_visualization")
def create_player_clustering_visualization(
    position: str,
    player1_name: str,
    player2_name: str,
    prepared_data: pd.DataFrame,
    players_name: pd.Series
) -> Tuple[plt.Figure, Dict[str, Any]]:
    """
    Crear visualización de clustering con destacado de jugadores seleccionados.
    
    Args:
        position: Posición de los jugadores para el clustering.
        player1_name: Nombre del primer jugador a destacar.
        player2_name: Nombre del segundo jugador a destacar.
        prepared_data: DataFrame con datos preparados para clustering.
        players_name: Serie con nombres de jugadores y posiciones.
        
    Returns:
        Tupla con figura del scatter plot y diccionario con información de clusters.
    """
    from utils.modelling import fit_clusters, optimal_pca_components
    
    # Filtrar jugadores por posición
    X = prepared_data[prepared_data['position'] == position].drop('position', axis=1)

    
    players_name = players_name[players_name['position'] == position]

    # Configuración por posición basada en notebook
    position_clusters = {
        "Forward": 5,
        "Midfielder": 4, 
        "Defender": 3,
        "Goalkeeper": 3
    }
    
    # Obtener configuración para la posición
    n_clusters = position_clusters.get(position)
    
    # Realizar clustering
    try:
        df_clusters, pipeline = fit_clusters(
            X,
            pca_components=optimal_pca_components(X),
            n_clusters=n_clusters,
            random_state=42
        )

        logger.debug(f"PCA optimo para {position}: {optimal_pca_components(X)}")
        
        # Obtener transformación PCA para visualización 2D
        X_transformed = pipeline["scaler"].transform(X)
        X_pca = pipeline["pca"].transform(X_transformed)
        
        # Encontrar jugadores seleccionados en el dataset
        player1_idx = players_name[players_name['player_name'] == player1_name].index
        player2_idx = players_name[players_name['player_name'] == player2_name].index
        
        # Crear figura para scatter plot único
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.set_facecolor('#001F5B')
        
        # Scatter plot PCA
        ax.set_facecolor('#001F5B')
        
        # Colores para clusters
        cluster_colors = ["#fca327", "#FA34D9", "#32ff62", "#12e9f8", "#f8d468"][:n_clusters]
        
        # Plotear todos los jugadores
        for cluster_id in range(n_clusters):
            cluster_mask = df_clusters['cluster'] == cluster_id
            cluster_data = X_pca[cluster_mask]
            
            if len(cluster_data) > 0:
                ax.scatter(cluster_data[:, 0], cluster_data[:, 1], 
                           c=cluster_colors[cluster_id], alpha=0.8, s=40, 
                           label=f'Cluster {cluster_id}')
        
        # Destacar jugadores seleccionados
        if len(player1_idx) > 0:
            p1_idx_in_clean = X.index.get_loc(player1_idx[0])
            p1_cluster = df_clusters.loc[player1_idx[0], 'cluster']
            ax.scatter(X_pca[p1_idx_in_clean, 0], X_pca[p1_idx_in_clean, 1], 
                       c=cluster_colors[p1_cluster], s=100, marker='o', 
                       edgecolors='white', linewidth=3, zorder=10)
            ax.annotate(player1_name, 
                        (X_pca[p1_idx_in_clean, 0], X_pca[p1_idx_in_clean, 1]),
                        xytext=(10, 10), textcoords='offset points',
                        color='white', fontsize=8, fontweight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor=cluster_colors[p1_cluster], alpha=0.8))
        
        if len(player2_idx) > 0:
            p2_idx_in_clean = X.index.get_loc(player2_idx[0])
            p2_cluster = df_clusters.loc[player2_idx[0], 'cluster']
            ax.scatter(X_pca[p2_idx_in_clean, 0], X_pca[p2_idx_in_clean, 1], 
                       c=cluster_colors[p2_cluster], s=100, marker='s', 
                       edgecolors='white', linewidth=3, zorder=10)
            ax.annotate(player2_name, 
                        (X_pca[p2_idx_in_clean, 0], X_pca[p2_idx_in_clean, 1]),
                        xytext=(10, -20), textcoords='offset points',
                        color='white', fontsize=8, fontweight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor=cluster_colors[p2_cluster], alpha=0.8))
        
        plt.tight_layout()
        
        # Preparar información de retorno
        cluster_info = {
            "player1_cluster": df_clusters.loc[player1_idx[0], 'cluster'] if len(player1_idx) > 0 else None,
            "player2_cluster": df_clusters.loc[player2_idx[0], 'cluster'] if len(player2_idx) > 0 else None,
            "n_clusters": n_clusters,
            "cluster_sizes": df_clusters['cluster'].value_counts().to_dict(),
            "position": position
        }
        
        logger.info(f"Visualización de clustering creada exitosamente para {position}s")

        ax.set_xticks([])
        ax.set_yticks([])
        # Quitar spines superior y derecho
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Ajustar color de los restantes
        ax.spines["bottom"].set_linewidth(2)
        ax.spines["left"].set_linewidth(2)
        ax.spines["bottom"].set_color("white")
        ax.spines["left"].set_color("white")

        return fig, cluster_info
        
    except Exception as e:
        logger.error(f"Error en clustering: {str(e)}")
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')
        ax.text(0.5, 0.5, f'Error en análisis de clustering: {str(e)}',
                ha='center', va='center', color='white', fontsize=14, weight='bold')
        ax.axis('off')
        return fig, {}
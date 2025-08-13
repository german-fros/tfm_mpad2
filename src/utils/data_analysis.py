import pandas as pd
from typing import List, Dict, Any, Optional
from functools import lru_cache
from config.logger_config import LoggerSetup, log_function
from utils.data_processing import find_project_root
import matplotlib.pyplot as plt
import seaborn as sns

# Configurar logger al inicio del módulo
logger_setup = LoggerSetup()
logger = logger_setup.setup_logger(__name__)


# ===  ANÁLISIS EXPLORATORIO ===

@log_function()
def exploratory_analysis(df: pd.DataFrame) -> None:
    """
    Realiza un análisis exploratorio básico del DataFrame.
    
    Args:
        df: DataFrame a analizar.
    
    Returns:
        None
    """
    print("=== Información del Dataset ===")
    print(df.info(verbose=True, memory_usage='deep'))

    print("\n=== Dimensiones ===")
    print(f"Filas: {df.shape[0]}  |  Columnas: {df.shape[1]}")

    duplicados = df[df['id'].duplicated()].shape[0]
    print(f"\n=== Registros duplicados: {duplicados} ===")

    nulos = df.isnull().sum().sort_values(ascending=False)
    nulos = nulos[nulos > 0]
    print(f"\n=== Columnas con valores faltantes: {nulos.shape[0]} ===")
    if not nulos.empty:
        print(nulos)

        # Obtener porcentaje de nulos por columna
        null_stats = pd.DataFrame({
       'column': df.columns,
       'null_count': df.isnull().sum(),
       'null_percentage': (df.isnull().sum() / len(df)) * 100
       })
   
        null_stats = null_stats.sort_values('null_percentage', ascending=False)  # Ordenar por porcentaje descendente
        null_stats = null_stats.reset_index(drop=True)

        print(f"\n=== Media de valores faltantes por columna: {null_stats[['null_percentage']].describe().T['mean'][0]:.1f} ===")
        print(f"\n=== El 75% de las columnas tiene {null_stats[['null_percentage']].describe().T['25%'][0]:.2f} o más de valores nulos ===")
    else:
        print("No hay valores nulos.")

    print("\n=== Tipos de variables: ===")
    print(df.dtypes.value_counts())

    print(f"\n=== Eventos únicos: {len(pd.unique(df['eventTypeName']))} ===")
    print(pd.unique(df['eventTypeName']))


# === VISUALIZACIONES INICIALES ===

    ## === VISUALIZACIÓN 1 ===
def _analyze_event_distribution(df: pd.DataFrame, save_plot: bool = True) -> dict:
    """
    Analiza la distribución de tipos de eventos.
    
    Args:
        df: DataFrame con eventos.
        save_plots: Si guardar los gráficos generados.
        
    Returns:
        Diccionario con estadísticas de la distribución.
    """
    
    # Verificar que existe la columna eventTypeName
    if 'eventTypeName' not in df.columns:
        raise ValueError("Columna 'eventTypeName' no encontrada en el dataset")
    
    # Contar eventos por tipo
    event_counts = df['eventTypeName'].value_counts()
    total_events = len(df)
    
    # Estadísticas básicas
    results = {
        'total_events': total_events,
        'unique_event_types': len(event_counts),
        'most_common_event': event_counts.index[0],
        'most_common_count': event_counts.iloc[0],
        'most_common_percentage': (event_counts.iloc[0] / total_events) * 100,
        'top_5_events': event_counts.head().to_dict()
    }
    
    # Configurar estilo para gráficos
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Crear figura con subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
    
    # 1. Gráfico de barras - Top 15 eventos más frecuentes
    top_15_events = event_counts.head(15)
    
    bars = ax1.bar(range(len(top_15_events)), top_15_events.values, 
                   color=sns.color_palette("husl", len(top_15_events)))
    
    ax1.set_title('Top 15 Tipos de Eventos Más Frecuentes - Inter Miami CF', 
                  fontsize=16, fontweight='bold', pad=20)
    ax1.set_ylabel('Número de Eventos', fontsize=12)
    ax1.set_xticks(range(len(top_15_events)))
    ax1.set_xticklabels(top_15_events.index, rotation=45, ha='right')
    
    # Agregar valores en las barras
    for i, bar in enumerate(bars):
        height = bar.get_height()
        percentage = (height / total_events) * 100
        ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{int(height)}\n({percentage:.1f}%)',
                ha='center', va='bottom', fontsize=9)
    
    ax1.grid(axis='y', alpha=0.3)
    
    # 2. Histograma de frecuencias (log scale para ver eventos raros)
    ax2.hist(event_counts.values, bins=20, color='skyblue', alpha=0.7, edgecolor='black')
    ax2.set_title('Distribución de Frecuencias de Tipos de Evento (Escala Log)', 
                  fontsize=16, fontweight='bold', pad=20)
    ax2.set_xlabel('Número de Eventos por Tipo', fontsize=12)
    ax2.set_ylabel('Cantidad de Tipos de Evento', fontsize=12)
    ax2.set_yscale('log')
    ax2.grid(alpha=0.3)
    
    # Agregar líneas de referencia
    median_freq = event_counts.median()
    mean_freq = event_counts.mean()
    
    ax2.axvline(median_freq, color='red', linestyle='--', 
                label=f'Mediana: {median_freq:.0f}')
    ax2.axvline(mean_freq, color='orange', linestyle='--', 
                label=f'Media: {mean_freq:.0f}')
    ax2.legend()
    
    plt.tight_layout()
    
    # Guardar gráfico
    if save_plot:
        PROJECT_ROOT = find_project_root()
        output_dir = PROJECT_ROOT / "docs" / "reports" / "figures"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        plt.savefig(output_dir / "distribucion_tipos_eventos.png", 
                    dpi=300, bbox_inches='tight', facecolor='white')
        logger.info(f"Figura 1 guardada en: {output_dir / "distribucion_tipos_eventos.png"}")
        
    plt.show()
    
    # Análisis adicional: detectar eventos raros (< 1% del total)
    rare_events = event_counts[event_counts < (total_events * 0.01)]
    results['rare_events_count'] = len(rare_events)
    results['rare_events_list'] = rare_events.to_dict()
    
    # Análisis adicional: concentración (top 5 vs resto)
    top_5_percentage = (event_counts.head().sum() / total_events) * 100
    results['top_5_concentration'] = top_5_percentage
    
    return results


    ## === VISUALIZACIÓN 2 ===
def _temporal_distribution_analysis(df: pd.DataFrame, save_plot: bool = True) -> dict:
    """
    Analiza la distribución temporal de eventos (timeMin).
    
    Args:
        df: DataFrame con eventos del Inter Miami.
        save_plot: Si guardar la figura generada.
        
    Returns:
        Diccionario con estadísticas temporales.
    """
    
    if 'timeMin' not in df.columns:
        raise ValueError("Columna 'timeMin' no encontrada")
    
    logger.info("Generando análisis de distribución temporal")
    
    # Estadísticas básicas
    stats = df['timeMin'].describe()
    results = {'temporal_stats': stats.to_dict()}
    
    # Crear figura
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Boxplot principal
    box_plot = ax1.boxplot(df['timeMin'].dropna(), patch_artist=True, 
                          boxprops=dict(facecolor='lightblue', alpha=0.7),
                          medianprops=dict(color='red', linewidth=2))
    
    ax1.set_title('Distribución de Eventos por Minuto - Inter Miami CF', 
                  fontsize=14, fontweight='bold')
    ax1.set_ylabel('Tiempo (minutos)', fontsize=12)
    ax1.grid(axis='y', alpha=0.3)
    
    # Agregar estadísticas en el gráfico
    ax1.text(0.7, stats['75%'], f"Q3: {stats['75%']:.0f}'", 
            fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
    ax1.text(0.7, stats['50%'], f"Mediana: {stats['50%']:.0f}'", 
            fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor="orange", alpha=0.7))
    ax1.text(0.7, stats['25%'], f"Q1: {stats['25%']:.0f}'", 
            fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.7))
    
    # Histograma complementario
    ax2.hist(df['timeMin'].dropna(), bins=20, color='skyblue', alpha=0.7, edgecolor='black')
    ax2.axvline(stats['mean'], color='red', linestyle='--', linewidth=2, label=f"Media: {stats['mean']:.1f}'")
    ax2.axvline(stats['50%'], color='orange', linestyle='--', linewidth=2, label=f"Mediana: {stats['50%']:.1f}'")
    
    ax2.set_title('Histograma de Distribución Temporal', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Tiempo (minutos)', fontsize=12)
    ax2.set_ylabel('Frecuencia de Eventos', fontsize=12)
    ax2.legend()
    ax2.grid(alpha=0.3)
    
    plt.tight_layout()
    
    # Guardar figura
    if save_plot:
        PROJECT_ROOT = find_project_root()
        output_dir = PROJECT_ROOT / "docs" / "reports" / "figures"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        plt.savefig(output_dir / "distribucion_temporal.png", 
                   dpi=300, bbox_inches='tight', facecolor='white')
        logger.info(f"Figura 2 guardada en: {output_dir / 'distribucion_temporal.png'}")
    
    plt.show()
    
    logger.info(f"Análisis temporal completado")

    return results


    ## === VISUALIZACIÓN 3 ===
def _events_per_match_analysis(df: pd.DataFrame, save_plots: bool = True) -> dict:
    """
    Analiza la distribución de eventos por partido (histograma + boxplot).
    
    Args:
        df: DataFrame con eventos del Inter Miami.
        save_plots: Si guardar las figuras generadas.
        
    Returns:
        Diccionario con estadísticas de eventos por partido.
    """
    
    if 'match_id' not in df.columns:
        raise ValueError("Columna 'match_id' no encontrada")
    
    logger.info("Generando análisis de eventos por partido")
    
    # Calcular eventos por partido
    eventos_por_partido = df.groupby('match_id').size()
    results = {'events_per_match_stats': eventos_por_partido.describe().to_dict()}
    
    # Configurar directorio de salida
    if save_plots:
        PROJECT_ROOT = find_project_root()
        output_dir = PROJECT_ROOT / "docs" / "reports" / "figures"
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # FIGURA 2: Histograma de eventos por partido
    plt.figure(figsize=(10, 6))
    plt.hist(eventos_por_partido, bins=30, color='lightcoral', alpha=0.7, edgecolor='black')
    plt.title('Distribución de Eventos por Partido - Inter Miami CF', 
             fontsize=14, fontweight='bold')
    plt.xlabel('Eventos por Partido', fontsize=12)
    plt.ylabel('Frecuencia', fontsize=12)
    plt.grid(alpha=0.3)
    
    # Agregar línea de media
    mean_events = eventos_por_partido.mean()
    plt.axvline(mean_events, color='red', linestyle='--', linewidth=2, 
               label=f'Media: {mean_events:.1f} eventos')
    plt.legend()
    
    plt.tight_layout()
    
    if save_plots:
        plt.savefig(output_dir / "eventos_por_partido_hist.png", 
                   dpi=300, bbox_inches='tight', facecolor='white')
        logger.info(f"Figura 3 guardada en: {output_dir / 'eventos_por_partido_hist.png'}")
    
    plt.show()
    
    # FIGURA 3: Boxplot de eventos por partido
    plt.figure(figsize=(8, 6))
    box_plot = plt.boxplot(eventos_por_partido.values, vert=True, patch_artist=True,
                          boxprops=dict(facecolor='lightgreen', alpha=0.7),
                          medianprops=dict(color='red', linewidth=2))
    
    plt.title('Eventos por Partido - Inter Miami CF', fontsize=14, fontweight='bold')
    plt.ylabel('Número de Eventos', fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    
    # Agregar estadísticas
    match_stats = eventos_por_partido.describe()
    plt.text(1.2, match_stats['75%'], f"Q3: {match_stats['75%']:.0f}", 
            fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
    plt.text(1.2, match_stats['50%'], f"Mediana: {match_stats['50%']:.0f}", 
            fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor="orange", alpha=0.7))
    plt.text(1.2, match_stats['25%'], f"Q1: {match_stats['25%']:.0f}", 
            fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.7))
    
    plt.tight_layout()
    
    if save_plots:
        plt.savefig(output_dir / "eventos_por_partido_box.png", 
                   dpi=300, bbox_inches='tight', facecolor='white')
        logger.info(f"Figura 4 guardada en: {output_dir / 'eventos_por_partido_box.png'}")
    
    plt.show()
    
    logger.info(f"Análisis por partido completado.")
    
    return results


    ## === VISUALIZACIÓN 4 ===
def _spatial_distribution_analysis(df: pd.DataFrame, save_plot: bool = True) -> dict:
    """
    Analiza la distribución espacial de eventos con detección de outliers.
    
    Args:
        df: DataFrame con eventos del Inter Miami.
        save_plot: Si guardar la figura generada.
        
    Returns:
        Diccionario con estadísticas espaciales y outliers.
    """
    
    required_cols = ['x', 'y', 'eventTypeName']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Columnas faltantes: {missing_cols}")
    
    logger.info("Generando análisis de distribución espacial")
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Separar datos dentro y fuera del rango [0-100]
    mask_normal = (df['x'].between(0, 100)) & (df['y'].between(0, 100))
    mask_outliers = ~mask_normal
    
    # Datos normales y outliers
    normal_data = df[mask_normal]
    outlier_data = df[mask_outliers]
    
    results = {
        'spatial_analysis': {
            'normal_events': len(normal_data),
            'outlier_events': len(outlier_data),
            'outlier_percentage': (len(outlier_data) / len(df)) * 100
        }
    }
    
    # Scatterplot datos normales
    ax.scatter(normal_data['x'], normal_data['y'], 
              c='blue', alpha=0.6, s=20, label=f'Normal ({len(normal_data)} eventos)')
    
    # Scatterplot outliers
    ax.scatter(outlier_data['x'], outlier_data['y'], 
              c='red', alpha=0.8, s=40, label=f'Outliers ({len(outlier_data)} eventos)')
    
    # Etiquetas para outliers (limitadas para evitar saturación)
    outlier_sample = outlier_data.head(20) if len(outlier_data) > 20 else outlier_data
    for idx, row in outlier_sample.iterrows():
        ax.annotate(row['eventTypeName'], 
                   xy=(row['x'], row['y']),
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=8, ha='left',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
    
    # Líneas de referencia para el campo [0-100]
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax.axhline(y=100, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(x=100, color='gray', linestyle='--', alpha=0.5)
    
    # Configuración del gráfico
    ax.set_title('Distribución Espacial de Eventos - Inter Miami CF\n(Outliers fuera del rango 0-100)', 
                fontsize=14, fontweight='bold')
    ax.set_xlabel('Coordenada X', fontsize=12)
    ax.set_ylabel('Coordenada Y', fontsize=12)
    ax.legend()
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    
    # Guardar figura
    if save_plot:
        PROJECT_ROOT = find_project_root()
        output_dir = PROJECT_ROOT / "docs" / "reports" / "figures"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        plt.savefig(output_dir / "distribucion_espacial.png", 
                   dpi=300, bbox_inches='tight', facecolor='white')
        logger.info(f"Figura 5 guardada en: {output_dir / 'distribucion_espacial.png'}")
    
    plt.show()
    
    # Análisis de outliers espaciales
    if len(outlier_data) > 0:
        outlier_summary = outlier_data['eventTypeName'].value_counts()
        results['outlier_events_by_type'] = outlier_summary.to_dict()
        
        print("\n=== Eventos con outliers espaciales: ===")

        for event_type, count in outlier_summary.items():
            print(f"{event_type}: {count} eventos")
    
    logger.info(f"Análisis espacial completado.")
    
    return results


    ## === FUNCIÓN COORDENADORA GENERAL ===
@log_function()
def comprehensive_data_exploration(df: pd.DataFrame, save_plots: bool = True) -> dict:
    """
    Ejecuta exploración completa de datos llamando a todas las funciones específicas.
    
    Args:
        df: DataFrame con eventos del Inter Miami.
        save_plots: Si guardar las figuras generadas.
        
    Returns:
        Diccionario con todos los resultados del análisis.
    """
    
    logger.info("Iniciando exploración completa de datos")

    # Verificar columnas básicas
    basic_cols = ['timeMin', 'match_id', 'x', 'y', 'eventTypeName']
    missing_cols = [col for col in basic_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Columnas básicas faltantes: {missing_cols}")
    
    # Inicializar resultados
    all_results = {
        'dataset_summary': {
            'total_events': len(df),
            'unique_matches': df['match_id'].nunique(),
            'unique_event_types': df['eventTypeName'].nunique(),
            'date_range': f"{df['timeMin'].min():.0f} - {df['timeMin'].max():.0f} min"
        }
    }
    
    try:
        # Ejecutar análisis de distribución de eventos
        logger.info("Ejecutando análisis de distribución de eventos...")
        distribution_results = _analyze_event_distribution(df, save_plots)
        all_results.update(distribution_results)

        # Ejecutar análisis temporal
        logger.info("Ejecutando análisis temporal...")
        temporal_results = _temporal_distribution_analysis(df, save_plots)
        all_results.update(temporal_results)
        
        # Ejecutar análisis por partido
        logger.info("Ejecutando análisis por partido...")
        match_results = _events_per_match_analysis(df, save_plots)
        all_results.update(match_results)
        
        # Ejecutar análisis espacial
        logger.info("Ejecutando análisis espacial...")
        spatial_results = _spatial_distribution_analysis(df, save_plots)
        all_results.update(spatial_results)
        
        if save_plots:
            PROJECT_ROOT = find_project_root()
            output_dir = PROJECT_ROOT / "docs" / "reports" / "figures"
            print(f"\nTodas las figuras guardadas en: {output_dir}")
        
        logger.info("Exploración completa de datos finalizada exitosamente")
        
    except Exception as e:
        raise e(f"Error durante la exploración: {str(e)}")

    return all_results


if __name__ == "__main__":
    pass
import numpy as np
import pandas as pd
import json
from typing import List, Dict, Any, Optional
from functools import lru_cache
from src.config.logger_config import LoggerSetup, log_function, find_project_root

# Configurar logger al inicio del módulo
logger_setup = LoggerSetup()
logger = logger_setup.setup_logger(__name__)


@log_function("feature_engineering")
def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica ingeniería de características al DataFrame de estadísticas de jugadores.

    Args:
        df: DataFrame con estadísticas de jugadores.

    Returns:
        DataFrame con características adicionales calculadas.
    """
    df_features = df.copy()

    df_features['g/a'] = (df_features['goals'] + df_features['goal_assists'])

    int_cols = df_features.drop(columns='time_played').select_dtypes(include=["int"]).columns.to_list()

    for col in int_cols:
        df_features[f'{col}_p90'] = (df_features[col] / df_features['time_played']) * 90

    # Crear porcentajes y ratios
    df_features['tackles_%'] = ((df_features['tackles_won'] / df_features['total_tackles']).fillna(0) * 100)

    df_features['aerial_duels_%'] = ((df_features['aerial_duels_won'] / df_features['aerial_duels']).fillna(0) * 100)
    df_features['ground_duels_%'] = ((df_features['ground_duels_won'] / df_features['ground_duels']).fillna(0) * 100)
    df_features['duels_%'] = ((df_features['duels_won'] / df_features['duels']).fillna(0) * 100)

    df_features['short_passes_%'] = ((df_features['successful_short_passes'] / 
                                    (df_features['successful_short_passes'] + df_features['unsuccessful_short_passes'])).fillna(0) * 100)
    df_features['long_passes_%'] = ((df_features['successful_long_passes'] / 
                                (df_features['successful_long_passes'] + df_features['unsuccessful_long_passes'])).fillna(0) * 100)
    df_features['forward_passes_ratio'] = (df_features['forward_passes'] / df_features['total_passes']).fillna(0)
    df_features['passes_%'] = ((df_features['total_successful_passes'] / df_features['total_passes']).fillna(0) * 100)
    df_features['crossing_%'] = ((df_features['successful_crosses_&_corners'] / 
                                (df_features['successful_crosses_&_corners'] + df_features['unsuccessful_crosses_&_corners'])).fillna(0) * 100)

    df_features['dribble_%'] = ((df_features['successful_dribbles'] / 
                            (df_features['successful_dribbles'] + df_features['unsuccessful_dribbles'])).fillna(0) * 100)

    df_features['shots_%'] = ((df_features['shots_on_target'] / df_features['total_shots']).fillna(0) * 100)
    df_features['goal_shot_ratio'] = (df_features['goals'] / df_features['total_shots']).fillna(0)
    df_features['goals_from_outside_box_ratio'] = (df_features['goals_from_outside_box'] / df_features['goals']).fillna(0)

    
    df_features['penalty_goals_ratio'] = (df_features['penalty_goals'] / df_features['goals']).fillna(0)

    df_features['saves_ratio'] = (df_features['saves_made'] / df_features['goals_conceded']).fillna(0)
    df_features['penalties_saves_ratio'] = (df_features['penalties_saved'] / df_features['penalty_goals_conceded']).fillna(0)

    # Eliminar infinitos que puedan quedar
    df_features = df_features.replace([np.inf, -np.inf], 0)

    float_cols = df_features.select_dtypes(include=["float"]).columns.to_list()
    df_features[float_cols] = df_features[float_cols].apply(lambda x: round(x, 2))

    current = find_project_root()
    path = current / "data" / "processed"

    # Exportar DataFrame tratado
    df_features.to_csv(f"{path}/players_stats_mls24.csv", index=False)
    
    logger.info("DataFrame limpio y con nuevas features guardado correctamente!")

    return df_features


@log_function("clean_stats_data")
def clean_stats_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y procesa los datos de estadísticas de jugadores.

    Args:
        df: DataFrame con estadísticas de jugadores sin procesar.

    Returns:
        DataFrame limpio y procesado.
    """
    df_clean = df.copy()

    df_clean = df_clean[df_clean['time_played'] > df_clean['time_played'].quantile(.25)]

    float_cols = df_clean.select_dtypes(include=["float"]).columns.to_list()

    for col in float_cols:
        df_clean[col] = df_clean[col].astype(int)

    for str_col in ['season', 'shirt_number']:
        df_clean[str_col] = df_clean[str_col].astype(str)

    df_clean.rename(columns={
        'total_unsuccessful_passes_(_excl_crosses_&_corners_)': 'total_unsuccessful_passes', 
        'total_successful_passes_(_excl_crosses_&_corners_)_': 'total_successful_passes', 
        'shots_on_target_(_inc_goals_)': 'shots_on_target',
        'shots_off_target_(inc_woodwork)': 'shots_off_target',
        'corners_taken_(incl_short_corners)': 'corners_taken',
        'assists_(intentional)': 'assists',
        'key_passes_(attempt_assists)': 'key_passes'}, inplace=True)

    return df_clean


@log_function("clean_events_data")
def clean_events_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y convierte tipos de datos del DataFrame de eventos.
    
    Args:
        df: DataFrame con datos de eventos deportivos.
        
    Returns:
        DataFrame limpio con tipos de datos corregidos.
    """
    df_clean = df.copy()
    
    # Conversión de fechas
    date_columns = ['timeStamp', 'lastModified', 'Goal shot timestamp']
    for col in date_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
    
    # Conversión de enteros
    integer_cols = ['Minutes', 'timeMin', 'timeSec', 'periodId', 'outcome']
    for col in integer_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype('Int32')

    str_cols = ['season', 'shirt_number']
    for col in str_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype('str')
    
    # Eliminar eventos borrados
    initial_rows = len(df_clean)
    df_clean = df_clean[df_clean['eventTypeName'] != 'Deleted event'].copy()
    deleted_events = initial_rows - len(df_clean)
    
    logger.info(f"Eventos eliminados (Deleted event): {deleted_events}")
    logger.info(f"Filas restantes: {len(df_clean)}")

    current = find_project_root()
    path = current / "data" / "processed"

    # Exportar DataFrame tratado
    df_clean.to_csv(f"{path}/all_mls24_events.csv", index=False)
    
    logger.info("DataFrame limpio guardado correctamente!")
    
    return df_clean


@log_function("add_position_to_events")
def add_position_to_events(df_events: pd.DataFrame, path: Optional[str] = None) -> pd.DataFrame:
    """
    Añade información de posición a df_events desde squad_info.json.
    
    Args:
        df_events: DataFrame con eventos de partidos
        path: Ruta al archivo squad_info.json
        
    Returns:
        DataFrame con columna 'position' añadida
    """
    if not path:
        current = find_project_root()
        path = current / "data" / "pre_raw" / "squad_info.json"

    # Cargar squad_info.json
    with open(path, 'r', encoding='utf-8') as f:
        squad_data = json.load(f)
    
    # Crear diccionario de mapeo playerId -> position
    position_mapping = {}
    for team in squad_data['squad']:
        for person in team['person']:
            if person['type'] == 'player':
                position_mapping[person['id']] = person['position']
    
    # Añadir columna position usando map
    df_events['position'] = df_events['playerId'].map(position_mapping)
    
    logger.info(f"Añadida columna 'position'. {df_events['position'].notna().sum()} jugadores con posición asignada")
    
    return df_events


# Ejemplo de uso
if __name__ == "__main__":
    pass
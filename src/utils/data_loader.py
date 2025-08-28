import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, date
import os
import time

from src.config.logger_config import LoggerSetup, log_function, find_project_root

logger_setup = LoggerSetup()
logger = logger_setup.setup_logger(__name__)


# Data type optimization mappings
CATEGORICAL_COLUMNS = {
    'events': ['contestant_name', 'eventTypeName', 'playerName', 'position', 'Zone'],
    'players': ['team_name', 'player_name', 'position', 'primary_zone'],
    'teams': ['team_name', 'result']
}

ESSENTIAL_COLUMNS = {
    'events_summary': ['match_id', 'contestant_name', 'eventTypeName', 'playerName', 'timeMin'],
    'players_summary': ['player_name', 'team_name', 'position', 'goals', 'assists', 'games_played']
}


@log_function("optimize_dataframe_dtypes")
def _optimize_dataframe_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimizar tipos de datos del DataFrame para reducir uso de memoria.
    
    Args:
        df: DataFrame a optimizar.
        data_type: Tipo de datos para aplicar optimizaciones específicas.
        
    Returns:
        DataFrame con tipos de datos optimizados.
    """
    try:
        # Optimizar enteros y float
        for col in df.select_dtypes(include=['int64']).columns:
            if df[col].min() >= 0:
                if df[col].max() < 255:
                    df[col] = df[col].astype('uint8')
                elif df[col].max() < 65535:
                    df[col] = df[col].astype('uint16')
                else:
                    df[col] = df[col].astype('uint32')
            else:
                if df[col].min() > -128 and df[col].max() < 127:
                    df[col] = df[col].astype('int8')
                elif df[col].min() > -32768 and df[col].max() < 32767:
                    df[col] = df[col].astype('int16')
                else:
                    df[col] = df[col].astype('int32')
        
        # Optimizar float
        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')
            
    except Exception as e:
        logger.warning(f"Error optimizando tipos de datos: {str(e)}")
    
    return df


@log_function("read_csv_optimized")
def _read_csv_optimized(file_path: Path, columns: Optional[List[str]] = None, player_names: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Leer archivo CSV con optimizaciones de memoria y tipos de datos.
    
    Args:
        file_path: Ruta al archivo CSV.
        columns: Columnas específicas a cargar. Si None, carga todas.
        player_names: Lista de jugadores específicos a filtrar. Si None, carga todos.
        
    Returns:
        DataFrame optimizado con tipos de datos apropiados.
        
    Raises:
        ValueError: Si no se puede leer el archivo.
    """
    
    encodings = ['utf-8', 'latin-1', 'windows-1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            # Si se especifican columnas y hay filtro de jugadores, incluir playerName
            usecols = None
            if columns:
                usecols = columns.copy()
                if player_names and 'playerName' not in usecols:
                    usecols.append('playerName')
            
            df = pd.read_csv(file_path, encoding=encoding, usecols=usecols)
            
            # Filtrar por jugadores si se especifica
            if player_names and 'playerName' in df.columns:
                df = df[df['playerName'].isin(player_names)]
                logger.info(f"Datos filtrados para jugadores: {player_names}")
            
            # Optimizar tipos de datos
            df = _optimize_dataframe_dtypes(df)
            
            logger.info(f"Archivo {file_path.name} leído exitosamente con codificación {encoding}")
            return df
            
        except UnicodeDecodeError as e:
            logger.debug(f"Falló codificación {encoding} para {file_path.name}: {str(e)}")
            continue
        except ValueError as e:
            if 'usecols' in str(e).lower() or 'columns' in str(e).lower():
                logger.warning(f"Error de columnas en {file_path.name}: {str(e)}")
                logger.info("Reintentando carga sin filtro de columnas...")
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    if player_names and 'playerName' in df.columns:
                        df = df[df['playerName'].isin(player_names)]
                    df = _optimize_dataframe_dtypes(df)
                    return df
                except Exception:
                    continue
            else:
                logger.debug(f"Error leyendo {file_path.name} con {encoding}: {str(e)}")
                continue
        except Exception as e:
            logger.debug(f"Error leyendo {file_path.name} con {encoding}: {str(e)}")
            continue
    
    raise ValueError(f"No se pudo leer {file_path.name} con ninguna codificación soportada: {encodings}")


# ===== OPTIMIZED DATA LOADING FUNCTIONS =====

@st.cache_data(show_spinner="Cargando eventos de la MLS...")
def _load_all_events_data_from_file(columns: Optional[List[str]] = None, player_names: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Función optimizada para cargar todos los eventos de la MLS.
    
    Args:
        columns: Lista de columnas específicas a cargar. Si None, carga todas.
        player_names: Lista de jugadores específicos a filtrar. Si None, carga todos.
    
    Returns:
        DataFrame con eventos de la MLS optimizados.
        
    Raises:
        FileNotFoundError: Si el archivo de datos no existe.
    """
    project_root = find_project_root()
    events_file = project_root / "data" / "processed" / "all_mls24_events.csv"
    
    if not events_file.exists():
        raise FileNotFoundError(f"Archivo de eventos MLS no encontrado: {events_file}")
    
    # Cargar desde CSV optimizado con filtros
    df = _read_csv_optimized(events_file, columns=columns, player_names=player_names)
    
    logger.info(f"Eventos MLS cargados: {len(df)} registros")
    return df


@log_function("load_all_events_data")
def load_all_events_data(columns: Optional[List[str]] = None, player_names: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Cargar todos los eventos de la MLS con optimizaciones de rendimiento.
    
    Args:
        columns: Lista de columnas específicas a cargar. Si None, carga todas.
        player_names: Lista de jugadores específicos a filtrar. Si None, carga todos.
        
    Returns:
        DataFrame con eventos de la MLS optimizados.
    """
    
    return _load_all_events_data_from_file(columns=columns, player_names=player_names)


@st.cache_data(show_spinner="Cargando estadísticas de jugadores...")
def _load_players_season_stats_from_file() -> pd.DataFrame:
    """
    Función optimizada para cargar estadísticas de temporada de jugadores.
    
    Args:
        columns: Lista de columnas específicas a cargar.
        use_parquet: Usar formato parquet si está disponible.
    
    Returns:
        DataFrame con estadísticas de jugadores optimizadas.
        
    Raises:
        FileNotFoundError: Si el archivo de datos no existe.
    """
    project_root = find_project_root()
    stats_file = project_root / "data" / "processed" / "players_stats_mls24.csv"
    
    if not stats_file.exists():
        raise FileNotFoundError(f"Archivo de estadísticas de jugadores no encontrado: {stats_file}")
    
    # Cargar desde CSV optimizado
    df = _read_csv_optimized(stats_file)
    
    logger.info(f"Estadísticas de jugadores cargadas: {len(df)} registros")

    return df


@log_function("load_players_season_stats")
def load_players_season_stats() -> pd.DataFrame:
    """
    Cargar estadísticas de temporada de jugadores con optimizaciones.
    
    Args:
        refresh: Forzar recarga desde archivo, ignorando cache.
        columns: Lista de columnas específicas a cargar.
        use_summary: Usar solo columnas esenciales para mejor rendimiento.
        
    Returns:
        DataFrame con estadísticas de jugadores optimizadas.
    """
    
    return _load_players_season_stats_from_file()


@st.cache_data(show_spinner="Cargando estadísticas de equipo...")
def _load_team_season_stats_from_file() -> pd.DataFrame:
    """
    Función optimizada para cargar estadísticas de temporada de equipos.
    
    Args:
        columns: Lista de columnas específicas a cargar.
        use_parquet: Usar formato parquet si está disponible.
    
    Returns:
        DataFrame con estadísticas de equipos optimizadas.
        
    Raises:
        FileNotFoundError: Si el archivo de datos no existe.
    """
    project_root = find_project_root()

    # Buscar archivo de estadísticas de equipos
    file_path = project_root / "data" / "processed" / "team_stats_mls24.csv"
    
    if file_path.exists():
        stats_file = file_path
    else:
        raise FileNotFoundError(f"Archivo de estadísticas de equipo no encontrado en: {file_path}")
    
    # Cargar desde CSV optimizado
    df = _read_csv_optimized(stats_file)
    
    logger.info(f"Estadísticas de equipos cargadas: {len(df)} registros")

    return df


@log_function("load_team_season_stats")
def load_team_season_stats() -> pd.DataFrame:
    """
    Cargar estadísticas de temporada de equipos con optimizaciones.
    
    Args:
        refresh: Forzar recarga desde archivo, ignorando cache.
        columns: Lista de columnas específicas a cargar.
        
    Returns:
        DataFrame con estadísticas de equipos optimizadas.
    """
    return _load_team_season_stats_from_file()


@log_function("get_team_names")
def get_team_names() -> List[str]:
    """
    Obtener lista de nombres de todos los equipos disponibles.
    
    Returns:
        Lista ordenada de nombres de equipos.
    """
    # Usar modo resumen para carga más rápida
    teams_data = load_players_season_stats()
    team_names = sorted(teams_data['team_name'].unique().tolist())
    logger.debug(f"Equipos disponibles: {len(team_names)}")
    return team_names


@log_function("get_players_for_team_and_position")
def get_players_for_team_and_position(team_name: str, position: str) -> List[str]:
    """
    Obtener lista de jugadores para un equipo y posición específicos.
    
    Args:
        team_name: Nombre del equipo.
        position: Posición del jugador.
        
    Returns:
        Lista ordenada de nombres de jugadores del equipo en la posición especificada.
    """
    # Cargar solo columnas necesarias
    columns = ['player_name', 'team_name', 'position']
    players_data = load_players_season_stats()
    filtered_players = players_data[
        (players_data['team_name'] == team_name) & 
        (players_data['position'] == position)
    ]
    player_names = sorted(filtered_players['player_name'].unique().tolist())
    logger.debug(f"Jugadores de {team_name} en posición {position}: {len(player_names)}")
    return player_names
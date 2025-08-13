import pandas as pd
import logging
from typing import List, Optional
import functools
from config.logger_config import LoggerSetup, log_function

# Configurar logger
logger_setup = LoggerSetup()
logger = logger_setup.setup_logger(__name__)


@log_function()
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
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
    
    # Eliminar eventos borrados
    initial_rows = len(df_clean)
    df_clean = df_clean[df_clean['eventTypeName'] != 'Deleted event'].copy()
    deleted_events = initial_rows - len(df_clean)

    # Filtrar por solamente temporada regular
    df_clean = df_clean[df_clean['match_stage'] == 'Regular Season']
    
    logger.info(f"Eventos eliminados (Deleted event): {deleted_events}")
    logger.info(f"Filas restantes: {len(df_clean)}")
    
    return df_clean


if __name__ == "__main__":
    pass
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from functools import lru_cache
from config.logger_config import LoggerSetup, log_function, find_project_root

# Configurar logger al inicio del módulo
logger_setup = LoggerSetup()
logger = logger_setup.setup_logger(__name__)


@log_function()
def build_initial_dataframe(team: str = None) -> pd.DataFrame:
    """
    Ejecuta las diferentes funciones que componen la etapa de creación del DataFrame inicial.
    Exporta el DataFrame.

    Args:
        team: Nombre del equipo del cual obtener los eventos (si es None obtendrá todos los partidos).

    Returns:
        DataFrame con los eventos con sus columnas renombradas adecuadamente.
    """
    
    # Cargar los jsons
    data = _load_team_jsons(team)

    # Concatenarlos en un DataFrame
    df_inicial = _concat_matches(data)

    # Mapear las columnas y renombrarlas
    df_inicial = _map_column_names(df_inicial)

    # Exportar DataFrame
    if team:
        df_inicial.to_csv(f"../data/raw/{team}_mls24_events.csv", index=False)
    else:
        df_inicial.to_csv("../data/raw/all_mls24_events.csv", index=False)

    return df_inicial


@log_function()
def _load_team_jsons(team:str = None) -> List[Dict]:
    """
    Carga los json de eventing de los partidos seleccionados y los almacena en una lista.

    Args:
        path: Ruta al directorio que contiene los archivos JSON.

    Returns:
        Lista con los diccionarios de los eventing de los partidos seleccionados.

    Raises:
        FileNotFoundError: Si el directorio no existe.
        ValueError: Si no se encuentran archivos JSON.
    """
    # Obtener el path absoluto
    PROJECT_ROOT = find_project_root()
    path = PROJECT_ROOT / "data" / "pre_raw" / "jsons"

    
    # Verificar directorio
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Directorio {path} no encontrado")

    # Buscar todos los archivos JSON
    json_files = list(path.glob("*.json"))
    if not json_files:
        raise ValueError(f"No se encontraron archivos JSON en {path}")
    
    logger.info(f"Encontrados {len(json_files)} archivos JSON en {path}")
    
    jsons = []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data['matchInfo']['contestant']:  # Solo agregar si hay datos válidos
                if team:
                    if (data['matchInfo']['contestant'][0]['name'] == team or 
                    data['matchInfo']['contestant'][1]['name'] == team):  # Solo agregar partidos del equipo especificado
                        jsons.append(data)
                else:
                    jsons.append(data)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON inválido en {json_file.name}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error leyendo {json_file.name}: {str(e)}")
        except Exception as e:
            raise e(f"Error procesando {json_file.name}: {e}")
    
    # Crear DataFrame
    if not jsons:
        raise ValueError("No se pudieron cargar datos de ningún archivo")
    
    return jsons


@log_function()
def _concat_matches(matches: List[Dict]) -> pd.DataFrame:
   """
   Procesa y concatena eventos de múltiples partidos en un DataFrame único.

   Args:
       matches: Lista de diccionarios con datos JSON de partidos.

   Returns:
       DataFrame con todos los eventos concatenados incluyendo

   Raises:
       KeyError: Si la estructura JSON no contiene las claves esperadas.
       ValueError: Si la lista de matches está vacía.
       TypeError: Si matches no es una lista o contiene elementos inválidos.
   """
   
   if not isinstance(matches, list):
       raise TypeError("El parámetro 'matches' debe ser una lista")
   
   if not matches:
       raise ValueError("La lista de matches no puede estar vacía")
   
   logger.info(f"Procesando {len(matches)} partidos")
   
   matches_events = []
   
   for i, match in enumerate(matches):
       try:
           logger.debug(f"Procesando partido {i+1}/{len(matches)}")
           
           # Validar estructura del match
           if not isinstance(match, dict):
               raise TypeError(f"Match {i+1} no es un diccionario válido")
           
           # Extraer información del partido
           match_info = match.get('matchInfo', {})
           live_data = match.get('liveData', {})
           
           if not match_info or not live_data:
               logger.warning(f"Match {i+1}: estructura incompleta, saltando")
               continue
           
           match_id = match_info.get('id')
           match_stage = match_info.get('stage', {}).get('name', 'Unknown')
           
           # Validar contestants
           contestants_data = match_info.get('contestant', [])
           if len(contestants_data) < 2:
               logger.warning(f"Match {i+1}: datos de contestants insuficientes")
               continue
               
           contestants = {
               contestants_data[0].get('id'): contestants_data[0].get('name', 'Unknown'),
               contestants_data[1].get('id'): contestants_data[1].get('name', 'Unknown')
           }
           
           # Procesar eventos
           events = live_data.get('event', [])
           if not events:
               logger.warning(f"Match {i+1}: sin eventos, saltando")
               continue
               
           logger.debug(f"Match {i+1}: procesando {len(events)} eventos")
           
           match_events = []
           for j, event in enumerate(events):
               try:
                   # Convertir a DataFrame principal
                   match_event = pd.json_normalize(event, sep='_')
                   
                   # Eliminar qualifier si existe
                   if 'qualifier' in match_event.columns:
                       match_event = match_event.drop('qualifier', axis=1)

                   # Expandir qualifiers
                   qualifiers_pivot = pd.DataFrame()
                   if 'qualifier' in event and event['qualifier']:
                       qualifiers_match_event = pd.json_normalize(event['qualifier'])
                       if 'value' in qualifiers_match_event.columns and not qualifiers_match_event.empty:
                           qualifiers_pivot = qualifiers_match_event.pivot_table(
                               values='value', 
                               columns='qualifierId', 
                               aggfunc='first'
                           ).add_prefix('qualifier_')

                   # Reset índices para concatenación
                   match_event.reset_index(drop=True, inplace=True)
                   qualifiers_pivot.reset_index(drop=True, inplace=True)

                   # Combinar DataFrames
                   if not qualifiers_pivot.empty:
                       match_event_concat = pd.concat([match_event, qualifiers_pivot], axis=1)
                   else:
                       match_event_concat = match_event.copy()
                   
                   # Agregar metadatos
                   match_event_concat['match_id'] = match_id
                   match_event_concat['match_stage'] = match_stage
                   
                   # Mapear contestant_name si existe contestantId
                   if 'contestantId' in match_event_concat.columns:
                       match_event_concat['contestant_name'] = match_event_concat['contestantId'].map(contestants)
                   
                   match_events.append(match_event_concat)
                   
               except Exception as e:
                   logger.error(f"Error procesando evento {j+1} del match {i+1}: {str(e)}")
                   continue
           
           if match_events:
               try:
                   match_events_concat = pd.concat(match_events, ignore_index=True)
                   matches_events.append(match_events_concat)
                   logger.debug(f"Match {i+1}: {len(match_events)} eventos procesados exitosamente")
               except Exception as e:
                   logger.error(f"Error concatenando eventos del match {i+1}: {str(e)}")
                   continue
           else:
               logger.warning(f"Match {i+1}: no se procesaron eventos válidos")
               
       except Exception as e:
           logger.error(f"Error procesando match {i+1}: {str(e)}")
           continue
   
   if not matches_events:
       raise ValueError("No se pudieron procesar eventos de ningún partido")
   
   try:
       df_concat = pd.concat(matches_events, ignore_index=True)
       df_concat = df_concat.sort_values('timeStamp')
       logger.info(f"Concatenación exitosa: {len(df_concat)} eventos totales de {len(matches_events)} partidos")

       return df_concat
       
   except Exception as e:
       raise e(f"Error en concatenación final: {str(e)}")


@log_function()
def _map_column_names(team_matches_events: pd.DataFrame) -> pd.DataFrame:
   """
   Mapea nombres de columnas usando diccionarios de tipos de eventos y qualifiers de OPTA.
   
   Args:
       team_matches_events: DataFrame con eventos de partidos que contiene columnas 'qualifier_X' y 'typeId' para mapear.

   Returns:
       DataFrame con columnas renombradas y nueva columna 'eventTypeName'

   Raises:
       FileNotFoundError: Si no se encuentran los archivos JSON de mapeo.
       KeyError: Si el DataFrame no contiene las columnas esperadas.
       ValueError: Si el DataFrame está vacío.
       TypeError: Si team_matches_events no es un DataFrame.
   """
   
   # Validaciones de entrada
   if not isinstance(team_matches_events, pd.DataFrame):
       raise TypeError("team_matches_events debe ser un pandas DataFrame")
   
   if team_matches_events.empty:
       raise ValueError("El DataFrame no puede estar vacío")
   
   if 'typeId' not in team_matches_events.columns:
       raise KeyError("El DataFrame debe contener la columna 'typeId'")
   
   logger.info(f"Mapeando nombres de columnas para DataFrame con {len(team_matches_events)} filas y {len(team_matches_events.columns)} columnas")
   
   try:
       # Obtener el path absoluto
       PROJECT_ROOT = find_project_root()
       path = PROJECT_ROOT / "data" / "pre_raw"
       
       if not path.exists():
           raise FileNotFoundError(f"El directorio {path} no existe")
       
       # Cargar archivos de mapeo
       opta_events_file = path / "opta_events_type.json"
       opta_qualifiers_file = path / "opta_qualifiers_type.json"
       
       if not opta_events_file.exists():
           raise FileNotFoundError(f"No se encuentra el archivo: {opta_events_file}")
       
       if not opta_qualifiers_file.exists():
           raise FileNotFoundError(f"No se encuentra el archivo: {opta_qualifiers_file}")
       
       logger.debug("Cargando archivos de mapeo OPTA")
       
       with open(opta_events_file, 'r', encoding='utf-8') as f:
           opta_events_type = json.load(f)
       
       with open(opta_qualifiers_file, 'r', encoding='utf-8') as f:
           opta_qualifiers_type = json.load(f)
       
       logger.debug(f"Cargados {len(opta_events_type)} tipos de eventos y {len(opta_qualifiers_type)} qualifiers")
       
   except json.JSONDecodeError as e:
       logger.error(f"Error decodificando archivos JSON: {str(e)}")
       raise
   except Exception as e:
       logger.error(f"Error cargando archivos de mapeo: {str(e)}")
       raise
   
   try:
       team_matches_events = team_matches_events.copy()
       
       # Crear mapeo de nombres de columnas
       column_mapping = {}
       qualifier_columns_found = 0
       
       logger.debug("Creando mapeo de columnas")
       
       for col in team_matches_events.columns:
           if col.startswith('qualifier_'):
               # Extraer el número del qualifier
               qualifier_id = col.replace('qualifier_', '')
               
               if qualifier_id in opta_qualifiers_type:
                   new_name = opta_qualifiers_type[qualifier_id]
                   column_mapping[col] = new_name
                   qualifier_columns_found += 1
                   logger.debug(f"Mapeando {col} -> {new_name}")
               else:
                   # Mantener nombre original si no se encuentra mapeo
                   column_mapping[col] = col
                   logger.warning(f"No se encontró mapeo para qualifier_id: {qualifier_id}")
           elif col == 'typeId':
               # Mantener typeId sin cambio
               column_mapping[col] = col
           else:
               # Mantener las demás columnas sin cambio
               column_mapping[col] = col
       
       logger.info(f"Se mapearon {qualifier_columns_found} columnas de qualifiers")
       
       # Aplicar el mapeo
       team_matches_events = team_matches_events.rename(columns=column_mapping)
       
       # Agregar columna con nombre del evento
       logger.debug("Agregando columna eventTypeName")
       
       # Validar que todos los typeId tengan mapeo
       unique_type_ids = team_matches_events['typeId'].astype(str).unique()
       unmapped_ids = [tid for tid in unique_type_ids if tid not in opta_events_type]
       
       if unmapped_ids:
           logger.warning(f"TypeIds sin mapeo encontrados: {unmapped_ids}")
       
       team_matches_events['eventTypeName'] = team_matches_events['typeId'].astype(str).map(opta_events_type)
       
       # Verificar si hay valores NaN en eventTypeName
       nan_count = team_matches_events['eventTypeName'].isna().sum()
       if nan_count > 0:
           logger.warning(f"Se encontraron {nan_count} eventos sin nombre de tipo")
       
       columns = team_matches_events.columns.tolist()
       
       if 'eventTypeName' in columns:
           columns.remove('eventTypeName')
           
           # Insertar 'eventTypeName' en 4ta posición
           insert_position = min(3, len(columns))
           columns.insert(insert_position, 'eventTypeName')
           
           team_matches_events = team_matches_events[columns]
           logger.debug(f"eventTypeName insertado en posición {insert_position + 1}")
       
       logger.info(f"Mapeo completado exitosamente. DataFrame final: {len(team_matches_events)} filas, {len(team_matches_events.columns)} columnas")
       
       return team_matches_events
       
   except Exception as e:
       logger.error(f"Error durante el mapeo de columnas: {str(e)}")
       raise
   

@log_function()
def agregate_players_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforma eventos individuales en estadísticas agregadas por jugador.
    Filtra solo jugadores de Inter Miami.
    
    Args:
        df: DataFrame con eventos individuales.
        
    Returns:
        DataFrame con estadísticas por jugador de Inter Miami.
    """
    
    # Filtrar solo eventos de Inter Miami con playerName válido
    df_players = df[
        (df['playerName'].notna()) & 
        (df['contestant_name'] == 'Inter Miami')
    ].copy()
    
    logger.info(f"Procesando eventos de {df_players['playerName'].nunique()} jugadores de Inter Miami")
    
    # Información básica del jugador
    player_info = df_players.groupby('playerName').agg({
        'contestant_name': 'first',      # Equipo
        'match_id': 'nunique',          # Partidos jugados
        'timeMin': 'count'              # Total de eventos/acciones
    }).rename(columns={
        'contestant_name': 'team',
        'match_id': 'matches_played', 
        'timeMin': 'total_actions'
    })
    
    # Estadísticas de disparos DETALLADAS
    shot_events = ['Goal', 'Attempt Saved']
    shot_stats = df_players[
        df_players['eventTypeName'].isin(shot_events)
    ].groupby(['playerName', 'eventTypeName']).size().unstack(fill_value=0)
    
    # Renombrar columnas de disparos
    shot_columns_map = {
        'Goal': 'goals',
        'Attempt Saved': 'shots_saved'
    }
    if not shot_stats.empty:
        shot_stats = shot_stats.rename(columns=shot_columns_map)
    
    # Calcular totales de disparos (incluye todos los tipos de disparo)
    all_shot_events = ['Goal', 'Miss', 'Attempt Saved', 'Post']
    shot_totals = df_players[
        df_players['eventTypeName'].isin(all_shot_events)
    ].groupby('playerName').agg({
        'eventTypeName': 'count'
    }).rename(columns={
        'eventTypeName': 'shots_total'
    })
    
    # Combinar estadísticas de disparos
    if not shot_stats.empty:
        shot_stats = shot_stats.merge(shot_totals, left_index=True, right_index=True, how='outer')
        # Calcular shots_on_target como suma de goals + shots_saved
        shot_stats['shots_on_target'] = shot_stats.get('goals', 0) + shot_stats.get('shots_saved', 0)
    else:
        shot_stats = shot_totals
        if not shot_stats.empty:
            shot_stats['shots_on_target'] = 0

    shot_stats.drop(columns='shots_saved', inplace=True)
    
    # Estadísticas de pases
    pass_stats = df_players[df_players['eventTypeName'] == 'Pass'].groupby('playerName').agg({
        'eventTypeName': 'count',
        'outcome': 'sum',
        'Length': 'mean',
        'Assist': lambda x: (x == 16).sum(),
        'keyPass': lambda x: x.fillna(0).sum()
    }).rename(columns={
        'eventTypeName': 'passes_attempted',
        'outcome': 'passes_completed',
        'Length': 'avg_pass_distance',
        'Assist': 'assists',
        'keyPass': 'key_passes'
    })
    
    # Calcular % de pases completados por tipo
    pass_stats['pass_completion_rate'] = (
        pass_stats['passes_completed'] / pass_stats['passes_attempted']
    ).round(3)
    
    # Estadísticas defensivas
    defensive_events = ['Tackle', 'Interception', 'Clearance', 'Block']
    available_defensive = [event for event in defensive_events if event in df_players['eventTypeName'].values]
    
    if available_defensive:
        defensive_stats = df_players[
            df_players['eventTypeName'].isin(available_defensive)
        ].groupby('playerName').agg({
            'eventTypeName': 'count'
        }).rename(columns={'eventTypeName': 'defensive_actions'})
    else:
        defensive_stats = pd.DataFrame(index=player_info.index, columns=['defensive_actions']).fillna(0)
    
    # Disciplina
    card_stats = df_players[
        df_players['eventTypeName'].isin(['Yellow Card', 'Red Card'])
    ].groupby(['playerName', 'eventTypeName']).size().unstack(fill_value=0)
    
    if not card_stats.empty:
        if 'Yellow Card' in card_stats.columns:
            card_stats = card_stats.rename(columns={'Yellow Card': 'yellow_cards'})
        if 'Red Card' in card_stats.columns:
            card_stats = card_stats.rename(columns={'Red Card': 'red_cards'})
    
    # Estadísticas de posición en el campo
    position_stats = df_players.groupby('playerName').agg({
        'x': 'mean',
        'y': 'mean',
        'Zone': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Unknown'
    }).rename(columns={
        'x': 'avg_x_position',
        'y': 'avg_y_position', 
        'Zone': 'primary_zone'
    })
    
    # Métricas avanzadas
    advanced_stats = df_players.groupby('playerName').agg({
        'timeMin': lambda x: x.max() - x.min()
    }).rename(columns={'timeMin': 'minutes_played_approx'})
    
    # Combinar todas las estadísticas
    final_stats = player_info
    
    stats_to_merge = [pass_stats, shot_stats, defensive_stats, 
                     card_stats, position_stats, advanced_stats]
    
    for stats_df in stats_to_merge:
        if not stats_df.empty:
            final_stats = final_stats.merge(stats_df, left_index=True, right_index=True, how='left')
    
    # Rellenar valores faltantes
    final_stats = final_stats.fillna(0)
    
    # Calcular métricas por partido
    final_stats['goals_per_match'] = (final_stats['goals'] / final_stats['matches_played']).round(3)
    final_stats['assists_per_match'] = (final_stats['assists'] / final_stats['matches_played']).round(3)
    final_stats['shots_per_match'] = (final_stats['shots_total'] / final_stats['matches_played']).round(3)
    
    # Eficiencia de finalización por tipo de disparo
    final_stats['shot_conversion_rate'] = (
        final_stats['goals'] / final_stats['shots_total'].replace(0, 1)
    ).round(3)
    
    # Porcentaje de disparos a puerta
    if 'shots_on_target' in final_stats.columns:
        final_stats['shots_on_target_rate'] = (
            final_stats['shots_on_target'] / final_stats['shots_total'].replace(0, 1)
        ).round(3)
    
    # Transformar columnas 'float' a 'int'
    int_cols = ['key_passes', 'goals', 'shots_total', 'shots_on_target', 'defensive_actions']
    for col in int_cols:
        final_stats[col] = final_stats[col].astype('int32')

    final_stats = final_stats.reset_index()
    
    logger.info(f"Estadísticas calculadas para {len(final_stats)} jugadores de Inter Miami")

    # Obtener el path absoluto
    PROJECT_ROOT = find_project_root()
    path = PROJECT_ROOT / "data" / "processed" / "players_stats_mls24.csv"

    # Exportar DataFrame
    final_stats.to_csv(path, index=False)
    logger.info(f"{path.name} guardado correctamente en {path}")
    
    return final_stats


@log_function()
def agregate_players_stats_per_match(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula estadísticas completas por jugador por partido (mismas métricas que stats globales).
    Filtra solo jugadores de Inter Miami.
    
    Args:
        df: DataFrame con eventos de fútbol.
        
    Returns:
        DataFrame con estadísticas jugador-partido de Inter Miami.
    """
    
    # Filtrar solo eventos de Inter Miami con playerName válido
    df_players = df[
        (df['playerName'].notna()) & 
        (df['contestant_name'] == 'Inter Miami')
    ].copy()
    
    logger.info(f"Procesando estadísticas por partido para jugadores de Inter Miami")
    
    # Información básica por partido
    match_info = df_players.groupby(['playerName', 'match_id']).agg({
        'contestant_name': 'first',
        'timeMin': ['count', 'min', 'max']
    })
    match_info.columns = ['team', 'total_actions', 'min_minute', 'max_minute']
    match_info['minutes_played_approx'] = match_info['max_minute'] - match_info['min_minute']
    match_info['matches_played'] = 1  # Siempre 1 por definición (es por partido)
    
    # Estadísticas de disparos DETALLADAS por partido
    shot_events = ['Goal', 'Attempt Saved']
    shot_stats = df_players[
        df_players['eventTypeName'].isin(shot_events)
    ].groupby(['playerName', 'match_id', 'eventTypeName']).size().unstack(fill_value=0)
    
    # Renombrar columnas de disparos
    shot_columns_map = {
        'Goal': 'goals',
        'Attempt Saved': 'shots_saved'
    }
    if not shot_stats.empty:
        shot_stats = shot_stats.rename(columns=shot_columns_map)
    
    # Calcular totales de disparos por partido (incluye todos los tipos de disparo)
    all_shot_events = ['Goal', 'Miss', 'Attempt Saved', 'Post']
    shot_totals = df_players[
        df_players['eventTypeName'].isin(all_shot_events)
    ].groupby(['playerName', 'match_id']).agg({
        'eventTypeName': 'count'
    }).rename(columns={
        'eventTypeName': 'shots_total'
    })
    
    # Combinar estadísticas de disparos
    if not shot_stats.empty:
        shot_stats = shot_stats.merge(shot_totals, left_index=True, right_index=True, how='outer')
        # Calcular shots_on_target como suma de goals + shots_on_target
        shot_stats['shots_on_target'] = shot_stats.get('goals', 0) + shot_stats.get('shots_saved', 0)
    else:
        shot_stats = shot_totals
        if not shot_stats.empty:
            shot_stats['shots_on_target'] = 0

    shot_stats.drop(columns='shots_saved', inplace=True)
    
    # Estadísticas de pases por partido
    pass_stats = df_players[df_players['eventTypeName'] == 'Pass'].groupby(['playerName', 'match_id']).agg({
        'eventTypeName': 'count',
        'outcome': 'sum',
        'Length': 'mean',
        'Assist': lambda x: (x == 16).sum(),
        'keyPass': lambda x: x.fillna(0).sum()
    }).rename(columns={
        'eventTypeName': 'passes_attempted',
        'outcome': 'passes_completed',
        'Length': 'avg_pass_distance',
        'Assist': 'assists',
        'keyPass': 'key_passes'
    })
    
    # Calcular % de pases completados por tipo
    pass_stats['pass_completion_rate'] = (
        pass_stats['passes_completed'] / pass_stats['passes_attempted']
    ).round(3)
    
    # Estadísticas defensivas por partido
    defensive_events = ['Tackle', 'Interception', 'Clearance', 'Block']
    available_defensive = [event for event in defensive_events if event in df_players['eventTypeName'].values]
    
    if available_defensive:
        defensive_stats = df_players[
            df_players['eventTypeName'].isin(available_defensive)
        ].groupby(['playerName', 'match_id']).agg({
            'eventTypeName': 'count'
        }).rename(columns={'eventTypeName': 'defensive_actions'})
    else:
        defensive_stats = pd.DataFrame()
    
    # Disciplina por partido
    card_stats = df_players[
        df_players['eventTypeName'].isin(['Yellow Card', 'Red Card'])
    ].groupby(['playerName', 'match_id', 'eventTypeName']).size().unstack(fill_value=0)
    
    # Renombrar columnas de tarjetas si existen
    if not card_stats.empty:
        if 'Yellow Card' in card_stats.columns:
            card_stats = card_stats.rename(columns={'Yellow Card': 'yellow_cards'})
        if 'Red Card' in card_stats.columns:
            card_stats = card_stats.rename(columns={'Red Card': 'red_cards'})
    
    # Estadísticas de posición en el campo por partido
    position_stats = df_players.groupby(['playerName', 'match_id']).agg({
        'x': 'mean',                    # Posición X promedio
        'y': 'mean',                    # Posición Y promedio
        'Zone': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Unknown'  # Zona más frecuente
    }).rename(columns={
        'x': 'avg_x_position',
        'y': 'avg_y_position', 
        'Zone': 'primary_zone'
    })
    
    # Combinar todas las estadísticas
    final_stats = match_info
    
    # Lista de DataFrames para merge
    stats_to_merge = [pass_stats, shot_stats, defensive_stats, 
                     card_stats, position_stats]
    
    for stats_df in stats_to_merge:
        if not stats_df.empty:
            final_stats = final_stats.merge(stats_df, left_index=True, right_index=True, how='left')
    
    # Rellenar valores faltantes
    final_stats = final_stats.fillna(0)
    
    # 11. Eficiencia de finalización por tipo de disparo
    final_stats['shot_conversion_rate'] = (
        final_stats['goals'] / final_stats['shots_total'].replace(0, 1)
    ).round(3)
    
    # Porcentaje de disparos a puerta
    if 'shots_on_target' in final_stats.columns:
        final_stats['shots_on_target_rate'] = (
            final_stats['shots_on_target'] / final_stats['shots_total'].replace(0, 1)
        ).round(3)
    
    # Transformar columnas 'float' a 'int'
    int_cols = ['passes_attempted','key_passes', 'assists','goals', 'shots_total', 'shots_on_target', 'defensive_actions']
    for col in int_cols:
        final_stats[col] = final_stats[col].astype('int32')

    final_stats = final_stats.reset_index()
    
    logger.info(f"Estadísticas por partido calculadas para {len(final_stats)} registros de Inter Miami")

    # Obtener el path absoluto
    PROJECT_ROOT = find_project_root()
    path = PROJECT_ROOT / "data" / "processed" / "players_stats_per_match_mls24.csv"

    # Exportar DataFrame
    final_stats.to_csv(path, index=False)
    logger.info(f"{path.name} guardado correctamente en {path}")
    
    return final_stats


# Ejemplo de uso
if __name__ == "__main__":
    pass
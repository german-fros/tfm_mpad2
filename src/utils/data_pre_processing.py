import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from functools import lru_cache
from config.logger_config import LoggerSetup, log_function, find_project_root

# Configurar logger al inicio del módulo
logger_setup = LoggerSetup()
logger = logger_setup.setup_logger(__name__)

# === CONSTRUIR DATAFRAME DE EVENTOS ===
@log_function()
def build_initial_dataframe(team: str = None) -> pd.DataFrame:
    """
    Ejecuta las diferentes funciones que componen la etapa de creación del DataFrame inicial de eventos.
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

    current = find_project_root()
    path = current / "data" / "raw"

    # Exportar DataFrame
    if team:
        df_inicial.to_csv(f"{path}/{team.lower()}_mls24_events.csv", index=False)
    else:
        df_inicial.to_csv(f"{path}/all_mls24_events.csv", index=False)

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


# === CONSTRUIR DATAFRAMES DE STATS DE JUGADORES Y EQUIPOS
@log_function()
def extract_players_season_stats() -> pd.DataFrame:
    """
    Extrae estadísticas de jugadores desde los archivos JSON de stats de temporada.
    
    Returns:
        DataFrame con estadísticas de todos los jugadores de todos los equipos.
        
    Raises:
        FileNotFoundError: Si el directorio no existe.
        ValueError: Si no se encuentran archivos JSON o no se pueden procesar.
        TypeError: Si la estructura JSON no es válida.
    """
    # Obtener el path absoluto
    PROJECT_ROOT = find_project_root()
    path_jsons = PROJECT_ROOT / "data" / "pre_raw" / "jsons_season_stats"
    
    # Verificar directorio
    if not path_jsons.exists():
        raise FileNotFoundError(f"Directorio {path_jsons} no encontrado")
    
    # Buscar todos los archivos JSON
    json_files = list(path_jsons.glob("*.json"))
    if not json_files:
        raise ValueError(f"No se encontraron archivos JSON en {path_jsons}")
    
    logger.info(f"Procesando estadísticas de jugadores desde {len(json_files)} archivos JSON")
    
    all_players_stats = []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extraer información del equipo
            team_info = data.get('contestant', {})
            team_name = team_info.get('name', 'Unknown')
            team_id = team_info.get('id', '')
            
            # Extraer información de la competición
            competition_info = data.get('competition', {})
            competition_name = competition_info.get('name', '')
            
            # Extraer información del torneo
            tournament_info = data.get('tournamentCalendar', {})
            season = tournament_info.get('name', '')
            
            # Extraer jugadores
            players = data.get('player', [])
            
            logger.debug(f"Procesando {len(players)} jugadores del equipo {team_name}")
            
            for player in players:
                if not isinstance(player, dict):
                    logger.warning(f"Estructura de jugador inválida en {json_file.name}")
                    continue
                
                # Información básica del jugador
                player_data = {
                    'team_name': team_name,
                    'team_id': team_id,
                    'competition': competition_name,
                    'season': season,
                    'player_id': player.get('id', ''),
                    'player_name': player.get('matchName', ''),
                    'first_name': player.get('firstName', ''),
                    'last_name': player.get('lastName', ''),
                    'short_name': f"{player.get('shortFirstName', '')} {player.get('shortLastName', '')}".strip(),
                    'position': player.get('position', ''),
                    'shirt_number': player.get('shirtNumber', '')
                }
                
                # Extraer estadísticas del jugador
                player_stats = player.get('stat', [])
                
                for stat in player_stats:
                    if isinstance(stat, dict) and 'name' in stat and 'value' in stat:
                        # Normalizar el nombre de la estadística
                        stat_name = stat['name'].lower().replace(' ', '_').replace('-', '_')
                        stat_value = stat['value']
                        
                        # Intentar convertir a numérico si es posible
                        try:
                            if '.' in str(stat_value):
                                stat_value = float(stat_value)
                            else:
                                stat_value = int(stat_value)
                        except (ValueError, TypeError):
                            # Mantener como string si no es numérico
                            pass
                        
                        player_data[stat_name] = stat_value
                
                all_players_stats.append(player_data)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON inválido en {json_file.name}: {str(e)}")
            continue
        except Exception as e:
            logger.error(f"Error procesando {json_file.name}: {str(e)}")
            continue
    
    if not all_players_stats:
        raise ValueError("No se pudieron extraer estadísticas de ningún jugador")
    
    # Crear DataFrame
    df_players = pd.DataFrame(all_players_stats)
    
    # Rellenar valores faltantes con 0 para columnas numéricas
    numeric_columns = df_players.select_dtypes(include=[np.number]).columns
    df_players[numeric_columns] = df_players[numeric_columns].fillna(0)
    
    # Rellenar valores faltantes con string vacío para columnas de texto
    text_columns = df_players.select_dtypes(include=['object']).columns
    df_players[text_columns] = df_players[text_columns].fillna('')
    
    logger.info(f"Extraídas estadísticas de {len(df_players)} jugadores de {df_players['team_name'].nunique()} equipos")

    path_export = PROJECT_ROOT / "data" / "raw" / "players_stats_mls24.csv"

    df_players.to_csv(path_export, index=False)

    logger.info(f"Stats de jugadores exportado con éxito en {path_export}!")
    
    return df_players


@log_function()
def extract_teams_season_stats() -> pd.DataFrame:
    """
    Extrae estadísticas de equipos desde los archivos JSON de stats de temporada.
    
    Returns:
        DataFrame con estadísticas de todos los equipos.
        
    Raises:
        FileNotFoundError: Si el directorio no existe.
        ValueError: Si no se encuentran archivos JSON o no se pueden procesar.
        TypeError: Si la estructura JSON no es válida.
    """
    # Obtener el path absoluto
    PROJECT_ROOT = find_project_root()
    path = PROJECT_ROOT / "data" / "pre_raw" / "jsons_season_stats"
    
    # Verificar directorio
    if not path.exists():
        raise FileNotFoundError(f"Directorio {path} no encontrado")
    
    # Buscar todos los archivos JSON
    json_files = list(path.glob("*.json"))
    if not json_files:
        raise ValueError(f"No se encontraron archivos JSON en {path}")
    
    logger.info(f"Procesando estadísticas de equipos desde {len(json_files)} archivos JSON")
    
    all_teams_stats = []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extraer información del equipo
            team_info = data.get('contestant', {})
            if not team_info:
                logger.warning(f"No se encontró información del equipo en {json_file.name}")
                continue
            
            # Información básica del equipo
            team_data = {
                'team_name': team_info.get('name', 'Unknown'),
                'team_id': team_info.get('id', ''),
            }
            
            # Extraer información de la competición
            competition_info = data.get('competition', {})
            team_data.update({
                'competition_id': competition_info.get('id', ''),
                'competition_name': competition_info.get('name', ''),
                'competition_known_name': competition_info.get('knownName', '')
            })
            
            # Extraer información del torneo
            tournament_info = data.get('tournamentCalendar', {})
            team_data.update({
                'tournament_id': tournament_info.get('id', ''),
                'season': tournament_info.get('name', ''),
                'start_date': tournament_info.get('startDate', ''),
                'end_date': tournament_info.get('endDate', ''),
                'last_updated': data.get('lastUpdated', '')
            })
            
            # Extraer estadísticas del equipo
            team_stats = team_info.get('stat', [])
            
            logger.debug(f"Procesando {len(team_stats)} estadísticas del equipo {team_data['team_name']}")
            
            for stat in team_stats:
                if isinstance(stat, dict) and 'name' in stat and 'value' in stat:
                    # Normalizar el nombre de la estadística
                    stat_name = stat['name'].lower().replace(' ', '_').replace('-', '_')
                    stat_value = stat['value']
                    
                    # Intentar convertir a numérico si es posible
                    try:
                        if '.' in str(stat_value):
                            stat_value = float(stat_value)
                        else:
                            stat_value = int(stat_value)
                    except (ValueError, TypeError):
                        # Mantener como string si no es numérico
                        pass
                    
                    team_data[stat_name] = stat_value
            
            all_teams_stats.append(team_data)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON inválido en {json_file.name}: {str(e)}")
            continue
        except Exception as e:
            logger.error(f"Error procesando {json_file.name}: {str(e)}")
            continue
    
    if not all_teams_stats:
        raise ValueError("No se pudieron extraer estadísticas de ningún equipo")
    
    # Crear DataFrame
    df_teams = pd.DataFrame(all_teams_stats)
    
    # Rellenar valores faltantes con 0 para columnas numéricas
    numeric_columns = df_teams.select_dtypes(include=[np.number]).columns
    df_teams[numeric_columns] = df_teams[numeric_columns].fillna(0)
    
    # Rellenar valores faltantes con string vacío para columnas de texto
    text_columns = df_teams.select_dtypes(include=['object']).columns
    df_teams[text_columns] = df_teams[text_columns].fillna('')
    
    logger.info(f"Extraídas estadísticas de {len(df_teams)} equipos")

    path_export = PROJECT_ROOT / "data" / "raw" / "teams_stats_mls24.csv"

    df_teams.to_csv(path_export, index=False)

    logger.info(f"Stats de equipos exportados con éxito en {path_export}!")
    
    return df_teams


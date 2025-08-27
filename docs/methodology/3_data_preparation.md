# 3. Preparación de los Datos

## 3.1 Datos procesados

- `data/processed/all_mls24_events.csv`
  - Columns:
    ['id', 'eventId', 'typeId', 'eventTypeName', 'periodId', 'timeMin', 'timeSec', 'contestantId', 'outcome', 'x', 'y', 'timeStamp', 'lastModified', 'Involved', 'Player position', 'Jersey Number', 'Team Formation', 'Team Player Formation', 'Captain', 'Team kit', 'Resume', 'match_id', 'match_stage', 'contestant_name', 'Direction of Play', 'playerId', 'playerName', 'Zone', 'Pass End X', 'Pass End Y', 'Length', 'Angle', 'Kick Off', 'Opposite related event ID', 'Deleted Event Type', 'Intended tackle target', 'Defensive', 'Not visible', 'Related event ID', 'Foul', 'Goalmouth Y Coordinate', 'Goalmouth Z Coordinate', 'Blocked X Coordinate', 'Blocked Y Coordinate', 'GK X Coordinate', 'GK Y Coordinate', 'keyPass', 'Assist', 'Players caught offside', 'Box - Centre', 'Right footed', 'Regular play', 'Assisted', 'Low Centre', 'Blocked', 'Intentional Assist', 'First Touch', 'Def block', 'Out of box - Centre', 'Right', 'Volley', 'Swerve Right', 'Not past goal line', 'Individual play', 'Mis-hit', 'Not assisted', 'Next event Goal-Kick', 'Free kick taken', 'Direct', 'Injury', 'Injured player ID', 'Leading to attempt', 'Related error 1 ID', 'assist', 'Leading to goal', 'Goal shot timestamp', 'Goal shot game clock', 'GK x coordinate time of goal', 'GK y coordinate time of goal', 'Offensive', 'Next event Throw-In', 'Minutes', 'Flick-on', 'Blocked pass', 'End type', 'Left', 'Event type review', 'Review', 'Out of play', 'Formation slot', 'Detailed Position ID', 'Position Side ID', 'Defensive 1 v 1', '2nd related event ID', 'Collection complete', 'Parried safe', 'Standing', 'Hands', 'Fantasy Assist Type', 'Fantasy Assisted By', 'Fantasy Assist Team', 'Fantasy assist ID', 'Pre-Review Event Type', 'Reviewed event ID', 'Head', 'Blocked cross', 'Viral', 'Video coverage lost', 'Long ball', 'Launch', 'Shove/Push', 'Box - Left', 'Temp Shot On', 'High claim', 'Parried danger', 'Diving', 'Chipped', 'Indirect', 'Cross', 'Box - Deep Left', 'Penalty taker ID', 'Second (2nd) opposite related event ID', 'Causing player', 'Referee delay', "Awaiting official's decision", 'VAR Delay', 'Coach ID', 'Time wasting', 'Head pass', 'Goal Kick', 'Low', 'Fast break', 'Lay-off', 'Left footed', 'Close High', 'Small box - Left', 'Temp Blocked', 'Penalty', 'Attempted Tackle', 'Second yellow', 'Reckless offence', 'Goal disallowed', 'Other reason', 'Set piece', 'Overrun', 'Corner taken', 'In-swinger', 'Hit Woodwork', 'Hit Right Post', 'Coach types', 'Captain change', 'Throw in', 'Collected', 'Stooping', 'Box - Right', 'Aerial Foul', 'Jumping', 'Close Right and High', 'Swerve Left', 'Take on overtake', 'Caught', 'Temp Missed', 'Simulation', 'Unchallenged', '35+ Centre', 'Temp Miss Not Passed Goal Line', 'Yellow Card', 'Dissent', 'Drinks Break', 'Keeper Throw', 'Handball', 'High Left', 'Low Right', 'Pull back', 'Big chance', 'Other body part', 'Touch type clearance', 'Sliding', 'Take on space', 'Small box - Centre', 'Shirt Pull/Holding', 'Follows a Dribble']

  - Eventos únicos:
    ['Team set up', 'Start', 'Pass', 'Take On', 'Tackle','Ball recovery', 'Blocked Pass', 'Interception', 'Challenge', 'Attempted tackle', 'Claim', 'Ball touch', 'Out', 'Dispossessed', 'Corner Awarded', 'Keeper pick-up', 'Drop of Ball', 'Foul', 'Clearance', 'Card', 'Attempt Saved', 'Save', 'Aerial', 'Offside Pass', 'Offside provoked', 'Start delay', 'End delay', 'Referee Drop Ball', 'Error', 'Miss', 'Goal', 'Injury Time Announcement', 'End', 'Punch', 'Keeper Sweeper', 'Player off', 'Player on', 'Formation change', 'Shield ball opp', 'Obstacle', 'Collection End', 'Penalty faced', 'Post', 'Cross not claimed', 'Coverage interruption', 'Deleted After Review', 'Contentious referee decision', 'Smother', 'Good skill', 'Coach Setup']

- `data/processed/players_stats_mls24.csv`: season stats for every Inter Miami player
  - Columns:
    ['team_name',
  'team_id',
  'competition',
  'season',
  'player_id',
  'player_name',
  'first_name',
  'last_name',
  'short_name',
  'position',
  'shirt_number',
  'yellow_cards',
  'unsuccessful_short_passes',
  'tackles_won',
  'goal_assists',
  'goals_from_outside_box',
  'times_tackled',
  'left_foot_goals',
  'successful_passes_own_half',
  'rightside_passes',
  'penalty_goals_conceded',
  'total_unsuccessful_passes',
  'unsuccessful_passes_own_half',
  'unsuccessful_crosses_&_corners',
  'putthrough/blocked_distribution',
  'games_played',
  'unsuccessful_long_passes',
  'aerial_duels_lost',
  'total_fouls_won',
  'aerial_duels',
  'successful_short_passes',
  'successful_dribbles',
  'total_clearances',
  'ground_duels',
  'duels_lost',
  'corners_won',
  'unsuccessful_passes_opposition_half',
  'putthrough/blocked_distribution_won',
  'successful_corners_into_box',
  'appearances',
  'offsides',
  'goals_conceded_inside_box',
  'successful_crosses_open_play',
  'ground_duels_lost',
  'substitute_on',
  'successful_lay_offs',
  'last_player_tackle',
  'successful_passes_opposition_half',
  'ground_duels_won',
  'successful_long_passes',
  'open_play_passes',
  'shots_off_target',
  'blocks',
  'goals_conceded',
  'key_passes',
  'unsuccessful_launches',
  'backward_passes',
  'total_passes',
  'total_successful_passes',
  'total_shots',
  'leftside_passes',
  'duels',
  'total_fouls_conceded',
  'throw_ins_to_own_player',
  'starts',
  'goals',
  'total_losses_of_possession',
  'total_tackles',
  'aerial_duels_won',
  'total_touches_in_opposition_box',
  'duels_won',
  'shots_on_target',
  'unsuccessful_crosses_open_play',
  'goals_from_inside_box',
  'recoveries',
  'successful_launches',
  'unsuccessful_dribbles',
  'second_goal_assists',
  'blocked_shots',
  'index',
  'time_played',
  'touches',
  'throw_ins_to_opposition_player',
  'tackles_lost',
  'foul_attempted_tackle',
  'interceptions',
  'clean_sheets',
  'through_balls',
  'successful_crosses_&_corners',
  'corners_taken',
  'forward_passes',
  'goals_conceded_outside_box',
  'assists',
  'unsuccessful_corners_into_box',
  'substitute_off',
  'successful_open_play_passes',
  'home_goals',
  'away_goals',
  'winning_goal',
  'penalties_conceded',
  'handballs_conceded',
  'clearances_off_the_line',
  'red_cards___2nd_yellow',
  'goal_kicks',
  'gk_successful_distribution',
  'total_red_cards',
  'hit_woodwork',
  'overruns',
  'unsuccessful_lay_offs',
  'headed_goals',
  'penalties_saved',
  'catches',
  'saves_made_from_inside_box',
  'gk_unsuccessful_distribution',
  'saves_made___caught',
  'crosses_not_claimed',
  'saves_from_penalty',
  'saves_made_from_outside_box',
  'drops',
  'punches',
  'saves_made___parried',
  'saves_made',
  'goalkeeper_smother',
  'penalties_faced',
  'set_pieces_goals',
  'right_foot_goals',
  'attempts_from_set_pieces',
  'foul_won_penalty',
  'penalty_goals',
  'other_goals',
  'penalties_taken',
  'own_goal_scored',
  'straight_red_cards',
  'penalties_off_target',
  'yellow_cards_p90',
  'unsuccessful_short_passes_p90',
  'tackles_won_p90',
  'goal_assists_p90',
  'goals_from_outside_box_p90',
  'times_tackled_p90',
  'left_foot_goals_p90',
  'successful_passes_own_half_p90',
  'rightside_passes_p90',
  'penalty_goals_conceded_p90',
  'total_unsuccessful_passes_p90',
  'unsuccessful_passes_own_half_p90',
  'unsuccessful_crosses_&_corners_p90',
  'putthrough/blocked_distribution_p90',
  'games_played_p90',
  'unsuccessful_long_passes_p90',
  'aerial_duels_lost_p90',
  'total_fouls_won_p90',
  'aerial_duels_p90',
  'successful_short_passes_p90',
  'successful_dribbles_p90',
  'total_clearances_p90',
  'ground_duels_p90',
  'duels_lost_p90',
  'corners_won_p90',
  'unsuccessful_passes_opposition_half_p90',
  'putthrough/blocked_distribution_won_p90',
  'successful_corners_into_box_p90',
  'appearances_p90',
  'offsides_p90',
  'goals_conceded_inside_box_p90',
  'successful_crosses_open_play_p90',
  'ground_duels_lost_p90',
  'substitute_on_p90',
  'successful_lay_offs_p90',
  'last_player_tackle_p90',
  'successful_passes_opposition_half_p90',
  'ground_duels_won_p90',
  'successful_long_passes_p90',
  'open_play_passes_p90',
  'shots_off_target_p90',
  'blocks_p90',
  'goals_conceded_p90',
  'key_passes_p90',
  'unsuccessful_launches_p90',
  'backward_passes_p90',
  'total_passes_p90',
  'total_successful_passes_p90',
  'total_shots_p90',
  'leftside_passes_p90',
  'duels_p90',
  'total_fouls_conceded_p90',
  'throw_ins_to_own_player_p90',
  'starts_p90',
  'goals_p90',
  'total_losses_of_possession_p90',
  'total_tackles_p90',
  'aerial_duels_won_p90',
  'total_touches_in_opposition_box_p90',
  'duels_won_p90',
  'shots_on_target_p90',
  'unsuccessful_crosses_open_play_p90',
  'goals_from_inside_box_p90',
  'recoveries_p90',
  'successful_launches_p90',
  'unsuccessful_dribbles_p90',
  'second_goal_assists_p90',
  'blocked_shots_p90',
  'index_p90',
  'touches_p90',
  'throw_ins_to_opposition_player_p90',
  'tackles_lost_p90',
  'foul_attempted_tackle_p90',
  'interceptions_p90',
  'clean_sheets_p90',
  'through_balls_p90',
  'successful_crosses_&_corners_p90',
  'corners_taken_p90',
  'forward_passes_p90',
  'goals_conceded_outside_box_p90',
  'assists_p90',
  'unsuccessful_corners_into_box_p90',
  'substitute_off_p90',
  'successful_open_play_passes_p90',
  'home_goals_p90',
  'away_goals_p90',
  'winning_goal_p90',
  'penalties_conceded_p90',
  'handballs_conceded_p90',
  'clearances_off_the_line_p90',
  'red_cards___2nd_yellow_p90',
  'goal_kicks_p90',
  'gk_successful_distribution_p90',
  'total_red_cards_p90',
  'hit_woodwork_p90',
  'overruns_p90',
  'unsuccessful_lay_offs_p90',
  'headed_goals_p90',
  'penalties_saved_p90',
  'catches_p90',
  'saves_made_from_inside_box_p90',
  'gk_unsuccessful_distribution_p90',
  'saves_made___caught_p90',
  'crosses_not_claimed_p90',
  'saves_from_penalty_p90',
  'saves_made_from_outside_box_p90',
  'drops_p90',
  'punches_p90',
  'saves_made___parried_p90',
  'saves_made_p90',
  'goalkeeper_smother_p90',
  'penalties_faced_p90',
  'set_pieces_goals_p90',
  'right_foot_goals_p90',
  'attempts_from_set_pieces_p90',
  'foul_won_penalty_p90',
  'penalty_goals_p90',
  'other_goals_p90',
  'penalties_taken_p90',
  'own_goal_scored_p90',
  'straight_red_cards_p90',
  'penalties_off_target_p90',
  'tackles_%',
  'aerial_duels_%',
  'ground_duels_',
  'duels_%',
  'short_passes_%',
  'long_passes_%',
  'forward_passes_ratio',
  'passes_%',
  'crossing_%',
  'dribble_%',
  'shots_%',
  'goal_shot_ratio',
  'goals_from_outside_box_ratio',
  'g/a',
  'penalty_goals_ratio',
  'saves_ratio',
  'penalties_saves_ratio']

## 3.2. Selección de datos

### 3.2.1. Criterios de selección
Justificación de variables incluidas/excluidas

### 3.2.2. Filtrado de registros
- Criterios temporales
- Criterios geográficos
- Otros filtros aplicados

### 3.2.3. Dataset final
Descripción del conjunto resultante

## 3.3. Limpieza de datos

### 3.3.1. Tratamiento de valores faltantes
- **Estrategias aplicadas:** Eliminación, imputación, interpolación
- **Justificación:** Por qué se eligió cada método
- **Impacto:** Evaluación del efecto en el dataset

### 3.3.2. Tratamiento de outliers
- **Métodos de detección:** IQR, Z-score, isolation forest
- **Decisiones tomadas:** Eliminación, transformación, conservación
- **Documentación:** Registros afectados

### 3.3.3. Corrección de inconsistencias
- **Estandarización de formatos:** Fechas, texto, categorías
- **Unificación de criterios:** Nomenclaturas, unidades de medida

## 3.4. Construcción de datos

### 3.4.1. Feature engineering
Nuevas variables creadas

### 3.4.2. Agregaciones
Métricas calculadas

### 3.4.3. Transformaciones
- Logarítmica
- Normalización
- Escalado

## 3.5. Integración de datos

### 3.5.1. Fuentes múltiples
Cómo se combinaron diferentes datasets

### 3.5.2. Claves de unión
Variables utilizadas para merge

### 3.5.3. Resolución de conflictos
- Duplicados
- Inconsistencias

## 3.6. Formateo de datos

### 3.6.1. Estructura final
Forma del dataset para modelado

### 3.6.2. Codificación
- Variables categóricas
- Variables temporales

### 3.6.3. División del dataset
- Train
- Validation
- Test
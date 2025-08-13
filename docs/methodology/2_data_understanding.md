# 2. Comprensión de los Datos

## 2.1. Recolección inicial de datos

### 2.1.1. Fuentes de datos

`inter_miami_mls24_events.csv`: DataFrame que contiene los eventos de los 31 partidos jugados por el Inter Miami en la MLS 2024.

### 2.1.2. Descripción del dataset

- Tamaño: 64971 filas | 182 columnas
- Formato: pd.DataFrame

### 2.1.3. Calidad inicial

- Columnas con valores faltantes: 166
- 1417604 valores nulos (esperable debido a contener muchísimas columnas específicas de un tipo de evento)

## 2.2. Descripción de los datos

### 2.2.1. Variables disponibles

Data columns (total 182 columns):

      Column                                  Dtype  
---   ------                                  -----  
 0    id                                      int64  
 1    eventId                                 int64  
 2    typeId                                  int64  
 3    eventTypeName                           object
 4    periodId                                int64  
 5    timeMin                                 int64  
 6    timeSec                                 int64  
 7    contestantId                            object
 8    outcome                                 int64  
 9    x                                       float64
 10   y                                       float64
 11   timeStamp                               object
 12   lastModified                            object
 13   Involved                                object
 14   Player position                         object
 15   Jersey Number                           object
 16   Team Formation                          float64
 17   Team Player Formation                   object
 18   Captain                                 object
 19   Team kit                                float64
 20   Resume                                  object
 21   match_id                                object
 22   match_stage                             object
 23   contestant_name                         object
 24   Direction of Play                       object
 25   playerId                                object
 26   playerName                              object
 27   Zone                                    object
 28   Pass End X                              float64
 29   Pass End Y                              float64
 30   Length                                  float64
 31   Angle                                   float64
 32   Kick Off                                object
 33   Opposite related event ID               float64
 34   Deleted Event Type                      float64
 35   Intended tackle target                  object
 36   Defensive                               float64
 37   Not visible                             float64
 38   Related event ID                        float64
 39   Foul                                    float64
 40   Goalmouth Y Coordinate                  float64
 41   Goalmouth Z Coordinate                  float64
 42   Blocked X Coordinate                    float64
 43   Blocked Y Coordinate                    float64
 44   GK X Coordinate                         float64
 45   GK Y Coordinate                         float64
 46   keyPass                                 float64
 47   Assist                                  float64
 48   Players caught offside                  object
 49   Box - Centre                            float64
 50   Right footed                            float64
 51   Regular play                            float64
 52   Assisted                                float64
 53   Low Centre                              float64
 54   Blocked                                 float64
 55   Intentional Assist                      float64
 56   First Touch                             float64
 57   Def block                               float64
 58   Out of box - Centre                     float64
 59   Right                                   float64
 60   Volley                                  float64
 61   Swerve Right                            float64
 62   Not past goal line                      float64
 63   Individual play                         float64
 64   Mis-hit                                 float64
 65   Not assisted                            float64
 66   Next event Goal-Kick                    float64
 67   Free kick taken                         float64
 68   Direct                                  float64
 69   Injury                                  object
 70   Injured player ID                       object
 71   Leading to attempt                      float64
 72   Related error 1 ID                      float64
 73   assist                                  float64
 74   Leading to goal                         float64
 75   Goal shot timestamp                     object
 76   Goal shot game clock                    object
 77   GK x coordinate time of goal            float64
 78   GK y coordinate time of goal            float64
 79   Offensive                               float64
 80   Next event Throw-In                     float64
 81   Minutes                                 float64
 82   Flick-on                                float64
 83   Blocked pass                            float64
 84   End type                                float64
 85   Left                                    float64
 86   Event type review                       float64
 87   Review                                  float64
 88   Out of play                             float64
 89   Formation slot                          float64
 90   Detailed Position ID                    float64
 91   Position Side ID                        float64
 92   Defensive 1 v 1                         object
 93   2nd related event ID                    float64
 94   Collection complete                     object
 95   Parried safe                            float64
 96   Standing                                float64
 97   Hands                                   float64
 98   Fantasy Assist Type                     object
 99   Fantasy Assisted By                     object
 100  Fantasy Assist Team                     float64
 101  Fantasy assist ID                       float64
 102  Pre-Review Event Type                   float64
 103  Reviewed event ID                       float64
 104  Head                                    float64
 105  Blocked cross                           float64
 106  Viral                                   float64
 107  Video coverage lost                     float64
 108  Long ball                               float64
 109  Launch                                  float64
 110  Shove/Push                              float64
 111  Box - Left                              float64
 112  Temp Shot On                            float64
 113  High claim                              float64
 114  Parried danger                          float64
 115  Diving                                  float64
 116  Chipped                                 float64
 117  Indirect                                float64
 118  Cross                                   float64
 119  Box - Deep Left                         float64
 120  Penalty taker ID                        object
 121  Second (2nd) opposite related event ID  float64
 122  Causing player                          float64
 123  Referee delay                           float64
 124  Awaiting official's decision            float64
 125  VAR Delay                               float64
 126  Coach ID                                object
 127  Time wasting                            float64
 128  Head pass                               float64
 129  Goal Kick                               float64
 130  Low                                     float64
 131  Fast break                              float64
 132  Lay-off                                 float64
 133  Left footed                             float64
 134  Close High                              float64
 135  Small box - Left                        float64
 136  Temp Blocked                            float64
 137  Penalty                                 float64
 138  Attempted Tackle                        float64
 139  Second yellow                           float64
 140  Reckless offence                        float64
 141  Goal disallowed                         float64
 142  Other reason                            float64
 143  Set piece                               float64
 144  Overrun                                 float64
 145  Corner taken                            float64
 146  In-swinger                              float64
 147  Hit Woodwork                            float64
 148  Hit Right Post                          float64
 149  Coach types                             object
 150  Captain change                          float64
 151  Throw in                                float64
 152  Collected                               float64
 153  Stooping                                float64
 154  Box - Right                             float64
 155  Aerial Foul                             float64
 156  Jumping                                 float64
 157  Close Right and High                    float64
 158  Swerve Left                             float64
 159  Take on overtake                        float64
 160  Caught                                  float64
 161  Temp Missed                             float64
 162  Simulation                              float64
 163  Unchallenged                            float64
 164  35+ Centre                              float64
 165  Temp Miss Not Passed Goal Line          float64
 166  Yellow Card                             float64
 167  Dissent                                 float64
 168  Drinks Break                            float64
 169  Keeper Throw                            float64
 170  Handball                                float64
 171  High Left                               float64
 172  Low Right                               float64
 173  Pull back                               float64
 174  Big chance                              float64
 175  Other body part                         float64
 176  Touch type clearance                    float64
 177  Sliding                                 float64
 178  Take on space                           float64
 179  Small box - Centre                      float64
 180  Shirt Pull/Holding                      float64
 181  Follows a Dribble                       float64
dtypes: float64(144), int64(7), object(31)

## 2.3. Exploración de los datos

### 2.3.1. Análisis variado

Distribución de eventos:

- Total eventos: 64971
- Tipos únicos: 52
- Evento principal: Pass (60.3%)
- Concentración top 5: 76.8%
- Eventos raros (< 1%): 38

## 2.4. Verificación de calidad de datos

### 2.4.1. Valores faltantes

- Media de valores faltantes por columna: 88 %
- El 75% de las columnas tiene 99.7 % o más de valores nulos.
- Las columnas con qualifiers de pases (Long pass, Head pass y Blocked pass) está completamente vacías. Antes no aparecían como tal debido a que algunos eventos "Deleted event" tenían 0.0 en dichas columnas.

### 2.4.2. Valores duplicados

Sin duplicados

### 2.4.3. Outliers

- Un partido contiene un evento registrado como en el minuto 1429; sin embargo, está como "deleted".

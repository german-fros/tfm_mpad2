# 1. Comprensión del proyecto

## 1.1. Objetivos del proyecto

### 1.1.1. Contexto

Trabajo final del Máster en Python Avanzado Aplicado al Deporte - Sports Data Campus (UCAM). El proyecto debe demostrar las competencias técnicas adquiridas durante el programa, abarcando todas las etapas de la metodología CRISP-DM y culminando en una aplicación web desplegada.

Requisitos técnicos obligatorios:

- Aplicación desarrollada en Streamlit
- Página de análisis estadístico con visualizaciones, incuyendo modelo de clustering
- Funcionalidad de exportación a PDF en todas las páginas

Documentación de referencia: [Estructura de documentación](<../PFM - Estructura de documentacion.pdf>)

### 1.1.2. Problema de negocio

**Situación actual**: Los analistas deportivos y aficionados carecen de una herramienta unificada para analizar el rendimiento de los jugadores de la Major League Soccer.

**Problema específico**: La información está dispersa en múltiples fuentes y formatos, dificultando análisis comparativos profundos de las estadísticas y rendimiento táctico y técnico de los jugadores.

**Impacto**: Permitirá tomar decisiones informadas en scouting, análisis táctico y seguimiento de los jugadores.

### 1.1.3. Objetivos específicos

1. **Análisis de datos**: Procesar y analizar estadísticas de todos los jugadores de la Major League Soccer en la temporada 23/24
2. **Interfaz intuitiva**: Desarrollar sistema de filtros por equipo y navegación eficiente
3. **Visualizaciones de valor**: Crear gráficos que revelen patrones tácticos y de rendimiento no evidentes
4. **Modelo predictivo**: Clustering evidenciando diferentes perfiles de jugadores dentro de cada posición

## 1.2. Evaluación de la situación

### 1.2.1. Recursos disponibles

**Datos**:

`pre_raw/jsons_events/*.json`: carpeta con 522 jsons que contienen cada uno los eventos de un partido en específico de la MLS 23/24, obtenidos a través de la API de Opta
`pre_raw/jsons_season_stats/*.json`: carpeta con 29 jsons que contienen cada uno los stats a nivel de temporada de un equipo de la MLS 23/24 en específico y sus jugadores, obtenidos a través de la API de Opta

`all_events_mls24.csv`: DataFrame que contiene los eventos de todos los partidos de la MLS 23/24. Se extraen a partir de los jsons en pre_raw/jsons_events/
`players_stats_mls24.csv`: DataFrame que contiene stats a nivel de temporada de todos los jugadores de la MLS 23/24. Se extraen a partir de los jsons en pre_raw/jsons_season_stats/
`teams_stats_mls24.csv`: DataFrame que contiene stats a nivel de temporada de todos los equipos de la MLS 23/24. Se extraen a partir de los jsons en pre_raw/jsons_season_stats/

**Personal**: Germán Fros (desarrollador único)

**Tecnología**:

- Python 3.x + ecosistema de análisis de datos
- Jupyter Notebooks para exploración
- Streamlit para desarrollo web
- VS Code como IDE principal

### 1.2.2. Restricciones

**Temporales**: 30 días calendario para completar desarrollo, documentación y despliegue

**Técnicas**:

- Limitaciones de memoria para procesamiento de datasets grandes
- Restricciones de rendering en aplicaciones web gratuitas

### 1.2.3. Análisis de riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| Sobrecarga de funcionalidades | Alta | Alto | MVP con funcionalidades core prioritarias |
| Incumplimiento de plazo | Media | Crítico | Planificación ágil con entregas incrementales |
| Problemas de rendimiento | Media | Medio | Optimización temprana y testing de carga |

### 1.2.4. Plan de contingencias

- **Scope creep**: Mantener MVP definido, agregar features solo después de core completo
- **Retrasos técnicos**: Priorizar funcionalidad sobre diseño visual
- **Problemas de datos**: Preparar subset de datos reducido para desarrollo

## 1.3. Objetivos de minería de datos

### 1.3.1. Objetivos técnicos

**Análisis descriptivo**:

- Métricas de rendimiento en al temporada
- Patrones de juego mediante análisis de eventos
- Comparativas entre jugadores

**Machine Learning**:

- Modelo de clustering para clasificación de perfiles de jugador
- Algoritmo: K-means
- Variables: estadísticas de cada jugador en la temporada

### 1.3.2. Criterios de éxito

**Rendimiento técnico**:

- Tiempo de carga inicial: < 5 segundos
- Tiempo de respuesta a filtros: < 2 segundos
- Uptime de aplicación desplegada: > 95%

**Calidad del modelo**:

- Interpretabilidad: clusters claramente diferenciados
- Validación: consistencia con conocimiento táctico del fútbol

**Usabilidad**:

- Navegación intuitiva sin documentación
- Visualizaciones autoexplicativas
- Funcionalidad de exportación operativa

### 1.3.3. Entregables

1. **Aplicación web** desplegada públicamente
2. **Documentación técnica** siguiendo estructura CRISP-DM
3. **Video demostrativo** (5-10 minutos) explicando funcionalidades
4. **Repositorio GitHub** con código documentado y reproducible
5. **Informe de resultados**

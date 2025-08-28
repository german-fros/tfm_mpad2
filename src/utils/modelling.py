import pandas as  pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterable
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

from src.config.logger_config import LoggerSetup, log_function, find_project_root

logger_setup = LoggerSetup()
logger = logger_setup.setup_logger(__name__)


@log_function("prep_data_modelling")
def prep_data_modelling(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepara los datos para modelado de clustering.

    Args:
        df: DataFrame con estadísticas de jugadores.

    Returns:
        Tupla con DataFrame preparado para modelado y DataFrame con nombres de jugadores.
    """
    df_model = df.copy()

    float_cols = df_model.select_dtypes(['float']).columns.to_list()

    df_prepared = df_model[['position'] + float_cols]

    df_players_name = df_model[['player_name', 'position']]

    current = find_project_root()
    path = current / "data" / "processed" / "df_modelo.csv"

    df_prepared.to_csv(path, index=False)

    return df_prepared, df_players_name


@log_function("build_pipeline")
def build_pipeline(
    pca_components: Optional[int],
    n_clusters: int,
    random_state: int = 42,
) -> Pipeline:
    """
    Construye un Pipeline con MinMaxScaler + PCA + KMeans.

    Args:
        pca_components: Número de componentes PCA. Si es None, no aplica PCA.
        n_clusters: Número de clusters para KMeans.
        random_state: Semilla para reproducibilidad.

    Returns:
        Pipeline configurado para clustering.
    """
    steps = [("scaler", MinMaxScaler())]

    if pca_components is not None:
        steps.append(("pca", PCA(n_components=pca_components, random_state=random_state)))

    steps.append(("kmeans", KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)))
    return Pipeline(steps)


@log_function("fit_clusters")
def fit_clusters(
    X: pd.DataFrame,
    pca_components: Optional[int],
    n_clusters: int,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, Pipeline]:
    """
    Ajusta el pipeline al dataset y devuelve los clusters.

    Args:
        X: DataFrame con características para clustering.
        pca_components: Número de componentes PCA. Si es None, no aplica PCA.
        n_clusters: Número de clusters.
        random_state: Semilla para reproducibilidad.

    Returns:
        Tupla con DataFrame que incluye clusters y pipeline entrenado.
    """
    pipe = build_pipeline(pca_components, n_clusters, random_state)
    labels = pipe.fit_predict(X)
    df_out = X.copy()
    df_out["cluster"] = labels
    return df_out, pipe


@log_function("define_k")
def define_k(
    X: pd.DataFrame,
    k_range: Iterable[int] = range(2, 11),
    pca_components: Optional[int] = None,
    random_state: int = 42,
) -> Tuple[Dict[str, object], Dict[str, object]]:
    """
    Devuelve la selección de k óptimo según Silhouette y Elbow.

    Args:
        X: DataFrame con características.
        k_range: Rango de valores k a evaluar.
        pca_components: Número de componentes PCA.
        random_state: Semilla para reproducibilidad.

    Returns:
        Tupla con resultados de Silhouette y Elbow.
    """

    def _select_k_by_silhouette(
        X: pd.DataFrame,
        k_range: Iterable[int],
        pca_components: Optional[int],
        random_state: int
    ) -> Dict[str, object]:
        scores = {}
        for k in k_range:
            pipe = build_pipeline(pca_components=pca_components, n_clusters=k, random_state=random_state)
            labels = pipe.fit_predict(X)
            if len(set(labels)) > 1:
                X_transformed = pipe[:-1].transform(X)
                score = silhouette_score(X_transformed, labels)
                scores[k] = score
        best_k = max(scores, key=scores.get)
        return {"best_k": best_k, "best_score": scores[best_k], "scores": scores}

    def _select_k_by_elbow(
        X: pd.DataFrame,
        k_range: Iterable[int],
        pca_components: Optional[int],
        random_state: int
    ) -> Dict[str, object]:
        inertias = {}
        for k in k_range:
            pipe = build_pipeline(pca_components=pca_components, n_clusters=k, random_state=random_state)
            pipe.fit(X)
            inertias[k] = pipe[-1].inertia_

        # Método geométrico del codo
        k_list = list(inertias.keys())
        inertia_list = list(inertias.values())
        k_arr = np.array(k_list, dtype=float)
        i_arr = np.array(inertia_list, dtype=float)

        k_norm = (k_arr - k_arr.min()) / (k_arr.max() - k_arr.min() + 1e-12)
        i_norm = (i_arr - i_arr.min()) / (i_arr.max() - i_arr.min() + 1e-12)

        p1, p2 = np.array([k_norm[0], i_norm[0]]), np.array([k_norm[-1], i_norm[-1]])
        line_vec = p2 - p1
        line_unit = line_vec / (np.linalg.norm(line_vec) + 1e-12)

        dists = []
        for x, y in zip(k_norm, i_norm):
            p = np.array([x, y])
            proj_len = np.dot(p - p1, line_unit)
            proj_point = p1 + proj_len * line_unit
            dists.append(np.linalg.norm(p - proj_point))

        best_k = int(k_list[np.argmax(dists)])
        return {"best_k": best_k, "inertias": inertias, "k_list": k_list, "inertia_list": inertia_list}

    return (
        _select_k_by_silhouette(X, k_range, pca_components, random_state),
        _select_k_by_elbow(X, k_range, pca_components, random_state)
    )


@log_function("plot_k_diagnostics")
def plot_k_diagnostics(
    sil_result: dict,
    elbow_result: dict,
    title: str = "Selección de número de clusters (k)"
) -> None:
    """
    Grafica las curvas de Silhouette y Elbow para comparar la elección de k.

    Args:
        sil_result: Diccionario con resultados de Silhouette.
        elbow_result: Diccionario con resultados de Elbow.
        title: Título del gráfico.
    """
    fig, ax1 = plt.subplots(figsize=(8, 5))

    # --- Curva de Silhouette ---
    k_sil = list(sil_result["scores"].keys())
    sil_scores = list(sil_result["scores"].values())
    ax1.plot(k_sil, sil_scores, marker="o", color="tab:blue", label="Silhouette score")
    ax1.set_xlabel("Número de clusters (k)")
    ax1.set_ylabel("Silhouette score", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    # Resaltar mejor k según Silhouette
    ax1.axvline(sil_result["best_k"], color="tab:blue", linestyle="--", alpha=0.5)
    ax1.scatter(sil_result["best_k"], sil_result["best_score"], color="tab:blue", s=100, zorder=5)

    # --- Curva de Elbow (inercia) ---
    ax2 = ax1.twinx()
    k_elbow = elbow_result["k_list"]
    inertias = elbow_result["inertia_list"]
    ax2.plot(k_elbow, inertias, marker="s", color="tab:red", label="Inercia (Elbow)")
    ax2.set_ylabel("Inercia", color="tab:red")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    # Resaltar mejor k según Elbow
    ax2.axvline(elbow_result["best_k"], color="tab:red", linestyle="--", alpha=0.5)
    ax2.scatter(elbow_result["best_k"], elbow_result["inertias"][elbow_result["best_k"]],
                color="tab:red", s=100, zorder=5)

    # Título y leyenda
    fig.suptitle(title, fontsize=14)
    fig.tight_layout()
    plt.show()


@log_function("optimal_pca_components")
def optimal_pca_components(
    X: pd.DataFrame,
    threshold: float = 0.9,
    random_state: int = 42
) -> int:
    """
    Número mínimo de componentes PCA necesarios para explicar >= threshold de la varianza.

    Args:
        X: DataFrame con características.
        threshold: Umbral de varianza explicada (por defecto 0.9).
        random_state: Semilla para reproducibilidad.

    Returns:
        Número óptimo de componentes PCA.
    """
    X_scaled = MinMaxScaler().fit_transform(X)
    pca = PCA(random_state=random_state).fit(X_scaled)
    cum_var = np.cumsum(pca.explained_variance_ratio_)
    return np.argmax(cum_var >= threshold) + 1


@log_function("auto_configure_clustering")
def auto_configure_clustering(
    X: pd.DataFrame,
    pca_threshold: float = 0.9,
    k_range: Iterable[int] = range(2, 11),
    random_state: int = 42
) -> Dict[str, object]:
    """
    Determina automáticamente el número de componentes PCA y el número de clusters K.

    Args:
        X: DataFrame con features numéricas.
        pca_threshold: proporción de varianza acumulada deseada para PCA (ej. 0.9 = 90%).
        k_range: rango de valores de K a evaluar.
        random_state: semilla.

    Returns:
        Dict con configuración recomendada:
        {
            "n_components": int,
            "silhouette": int,
            "elbow": int
        }
    """
    # Paso 1: nº de componentes óptimos según varianza
    n_components = optimal_pca_components(X, threshold=pca_threshold, random_state=random_state)

    # Paso 2: selección de k
    sil_result, elbow_result = define_k(
        X, k_range=k_range, pca_components=n_components, random_state=random_state
    )

    return {
        "n_components": n_components,
        "sil": sil_result["best_k"],
        "elbow": elbow_result["best_k"]
    }


@log_function("plot_pca_2d")
def plot_pca_2d(X: pd.DataFrame, pipe: Pipeline) -> None:
    """
    Grafica los clusters proyectados en 2D usando las dos primeras componentes de PCA.
    """
    if "pca" not in pipe.named_steps:
        raise ValueError("El pipeline no tiene PCA, agrega pca_components>=2.")

    if pipe["pca"].n_components < 2:
        raise ValueError("Se requieren al menos 2 componentes PCA para graficar.")

    X_trans = pipe["scaler"].transform(X)
    X_pca = pipe["pca"].transform(X_trans)
    labels = pipe["kmeans"].labels_

    plt.figure(figsize=(7, 6))
    scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=labels, cmap="tab10", s=40, alpha=0.7)
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    plt.title("Clusters proyectados en PCA 2D")
    plt.legend(*scatter.legend_elements(), title="Cluster")
    plt.show()
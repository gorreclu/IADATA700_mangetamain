from __future__ import annotations

"""Streamlit page: Analyse de co-occurrence et clustering d'ingrédients.

Cette page utilise une matrice de co-occurrence PRÉCALCULÉE pour optimiser les performances.
La matrice 300x300 est générée à froid par utils/preprocess_ingredients_matrix.py.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE

from core.logger import get_logger


@dataclass
class IngredientsClusteringConfig:
    """Configuration pour l'analyse de clustering d'ingrédients.

    Attributes:
        matrix_path: Chemin vers la matrice de co-occurrence précalculée.
        ingredients_list_path: Chemin vers la liste des ingrédients.
        n_ingredients: Nombre d'ingrédients à analyser (de la matrice 300x300).
        n_clusters: Nombre de clusters à créer avec K-means.
        tsne_perplexity: Paramètre de perplexité pour la visualisation t-SNE.
    """

    matrix_path: Path = Path("data/ingredients_cooccurrence_matrix.csv")
    ingredients_list_path: Path = Path("data/ingredients_list.csv")
    n_ingredients: int = 40
    n_clusters: int = 4
    tsne_perplexity: int = 30


class IngredientsClusteringPage:
    """Page Streamlit pour l'analyse de clustering des ingrédients.

    Cette classe charge une matrice de co-occurrence PRÉCALCULÉE et effectue
    le clustering et la visualisation en temps réel.

    Attributes:
        matrix_path: Chemin vers la matrice de co-occurrence précalculée.
        ingredients_list_path: Chemin vers la liste des ingrédients.
        logger: Instance du logger pour le suivi des opérations.
    """

    def __init__(
        self,
        matrix_path: str = "data/ingredients_cooccurrence_matrix.csv",
        ingredients_list_path: str = "data/ingredients_list.csv",
    ) -> None:
        """Initialise la page de clustering d'ingrédients.

        Args:
            matrix_path: Chemin vers la matrice de co-occurrence précalculée (300x300).
            ingredients_list_path: Chemin vers la liste des 300 ingrédients avec fréquences.
        """
        self.matrix_path = Path(matrix_path)
        self.ingredients_list_path = Path(ingredients_list_path)
        self.logger = get_logger()
        self.logger.info("Initializing IngredientsClusteringPage with precomputed matrix")

    @st.cache_data(ttl=None, show_spinner="Chargement de la matrice précalculée...")
    def _load_cooccurrence_matrix(_self) -> Optional[tuple[pd.DataFrame, pd.DataFrame]]:
        """Charge et sanitise la matrice de co-occurrence + liste d'ingrédients.

        Sanitation appliquée:
        - Strip espaces
        - Détection mismatch index/colonnes
        - Forçage de la symétrie (colonnes = index) si nécessaire
        - Suppression doublons éventuels

        Returns:
            Tuple (matrice 300x300 nettoyée, liste des ingrédients) si succès, None sinon.
        """
        try:
            if not _self.matrix_path.exists():
                st.error(f"❌ Matrice introuvable: {_self.matrix_path}")
                st.info("💡 Exécutez d'abord: `uv run python -m utils.preprocess_ingredients_matrix`")
                st.stop()
                return None

            cooc_matrix = pd.read_csv(_self.matrix_path, index_col=0)
            _self.logger.info(f"✅ Matrice chargée brute: {cooc_matrix.shape}")

            # Validation de forme: la matrice doit être carrée et <= 400x400
            if cooc_matrix.shape[0] != cooc_matrix.shape[1] or cooc_matrix.shape[0] < 10:
                _self.logger.error(
                    "❌ Le fichier chargé n'est pas une matrice de co-occurrence carrée valide. Vérifiez le chemin fourni."
                )
                st.error(
                    "Le fichier chargé n'est pas une matrice de co-occurrence carrée. Assurez-vous d'avoir précalculé la matrice avec `utils/preprocess_ingredients_matrix.py` et que le chemin est `data/ingredients_cooccurrence_matrix.csv`."
                )
                st.stop()
            elif cooc_matrix.shape[0] > 500:
                _self.logger.warning(
                    f"⚠️ Matrice très grande ({cooc_matrix.shape}); ce n'est probablement pas le fichier précalculé attendu."
                )

            # Normalisation légère des labels (mais on conserve casse/minuscule existante)
            cooc_matrix.index = cooc_matrix.index.str.strip()
            cooc_matrix.columns = cooc_matrix.columns.str.strip()

            # Vérifier symétrie des labels
            idx_set = set(cooc_matrix.index)
            col_set = set(cooc_matrix.columns)
            if idx_set != col_set:
                missing_in_cols = idx_set - col_set
                missing_in_idx = col_set - idx_set
                _self.logger.warning(
                    f"⚠️ Mismatch labels: rows_only={len(missing_in_cols)}, cols_only={len(missing_in_idx)}"
                )
                # Intersection pour carré cohérent
                common = sorted(idx_set & col_set)
                cooc_matrix = cooc_matrix.loc[common, common]
                _self.logger.info(
                    f"🔧 Matrice réduite à intersection commune: {cooc_matrix.shape}"
                )

            # Forcer colonnes = index si ordre différent
            if not (cooc_matrix.index.tolist() == cooc_matrix.columns.tolist()):
                _self.logger.warning("⚠️ Réordonnancement des colonnes pour correspondre à l'index")
                cooc_matrix = cooc_matrix[cooc_matrix.index]

            # Vérifier doublons
            if cooc_matrix.index.has_duplicates or cooc_matrix.columns.has_duplicates:
                _self.logger.warning("⚠️ Doublons détectés dans labels; déduplication")
                # Déduplication par agrégation (somme)
                cooc_matrix = (
                    cooc_matrix.groupby(cooc_matrix.index).sum()
                )
                cooc_matrix = cooc_matrix[cooc_matrix.index]  # réaligner colonnes
                _self.logger.info(
                    f"🔁 Après déduplication: {cooc_matrix.shape}"
                )

            _self.logger.info(
                f"✅ Matrice finalisée: {cooc_matrix.shape} | Sample: {cooc_matrix.index[:5].tolist()}"
            )

            if not _self.ingredients_list_path.exists():
                st.error(f"❌ Liste des ingrédients introuvable: {_self.ingredients_list_path}")
                st.stop()
                return None

            ingredients_list = pd.read_csv(_self.ingredients_list_path)
            ingredients_list['ingredient'] = ingredients_list['ingredient'].str.strip()
            _self.logger.info(
                f"✅ Liste chargée: {len(ingredients_list)} ingrédients | Top 5: {ingredients_list.head()['ingredient'].tolist()}"
            )

            return cooc_matrix, ingredients_list

        except Exception as e:
            st.error(f"❌ Erreur de chargement: {e}")
            _self.logger.error(f"Failed to load precomputed matrix: {e}")
            st.stop()
            return None

    def render_sidebar(self) -> dict[str, int | bool]:
        """Affiche la sidebar avec les paramètres de clustering.

        Returns:
            Dictionnaire contenant les paramètres sélectionnés.
        """
        st.sidebar.header("🔧 Paramètres de Clustering")

        st.sidebar.info("📊 Matrice précalculée: 300 ingrédients")

        # Nombre d'ingrédients à sélectionner
        n_ingredients = st.sidebar.slider(
            "Nombre d'ingrédients à analyser",
            min_value=40,
            max_value=300,
            value=40,
            step=10,
            help="Sélectionner les N ingrédients les plus fréquents depuis la matrice 300x300",
        )

        # Nombre de clusters
        n_clusters = st.sidebar.slider(
            "Nombre de clusters",
            min_value=3,
            max_value=20,
            value=4,
            step=1,
            help="Nombre de groupes d'ingrédients à créer avec K-means",
        )

        # Paramètres t-SNE
        st.sidebar.subheader("🎨 Visualisation t-SNE")
        tsne_perplexity = st.sidebar.slider(
            "Perplexité",
            min_value=5,
            max_value=50,
            value=30,
            step=5,
            help="Contrôle la densité des groupes (5=local, 50=global)",
        )

        # Bouton d'analyse
        analyze_button = st.sidebar.button("🚀 Lancer l'analyse", type="primary")

        return {
            "n_ingredients": n_ingredients,
            "n_clusters": n_clusters,
            "tsne_perplexity": tsne_perplexity,
            "analyze_button": analyze_button,
        }

    def _select_top_ingredients(
        self, cooc_matrix: pd.DataFrame, ingredients_list: pd.DataFrame, n: int
    ) -> tuple[pd.DataFrame, list[str]]:
        """Sélectionne robustement les N ingrédients les plus fréquents.

        Diagnostic détaillé:
        - Taille liste vs matrice
        - Intersections
        - Fallback si mismatch complet (utilisation directe de l'index matrice)
        """
        matrix_index = list(cooc_matrix.index)
        matrix_cols = list(cooc_matrix.columns)

        # Logs de diagnostic
        self.logger.info(
            f"🔎 Diagnostic sélection: matrix_index={len(matrix_index)}, matrix_cols={len(matrix_cols)}, list_rows={len(ingredients_list)}"
        )

        if set(matrix_index) != set(matrix_cols):
            self.logger.warning("⚠️ Les labels lignes/colonnes ne correspondent pas parfaitement.")

        list_ings = ingredients_list['ingredient'].tolist()
        inter_with_index = set(list_ings) & set(matrix_index)
        inter_with_cols = set(list_ings) & set(matrix_cols)
        self.logger.info(
            f"🔎 Intersections: with_index={len(inter_with_index)}, with_cols={len(inter_with_cols)}"
        )

        if not inter_with_index:
            self.logger.error("❌ Aucune intersection entre la liste et l'index de la matrice. Fallback sur index brut.")
            # Fallback: prendre directement premiers n ingrédients de la matrice
            top_final = matrix_index[:n]
            sub_matrix = cooc_matrix.loc[top_final, top_final]
            self.logger.info(
                f"✅ Fallback utilisé: {len(top_final)} ingrédients | shape={sub_matrix.shape}"
            )
            return sub_matrix, top_final

        # Filtrage selon index (pas colonnes encore)
        filtered = ingredients_list[ingredients_list['ingredient'].isin(matrix_index)]
        top = filtered.nlargest(n, 'frequency')['ingredient'].tolist()

        # Vérification colonnes
        top_valid = [ing for ing in top if ing in set(matrix_cols)]
        lost = set(top) - set(top_valid)
        if lost:
            self.logger.warning(
                f"⚠️ Ingrédients présents dans index mais absents des colonnes ignorés: {list(lost)[:8]}{'...' if len(lost)>8 else ''}"
            )

        top_final = top_valid[:n]
        if len(top_final) < n:
            self.logger.warning(
                f"⚠️ Seulement {len(top_final)}/{n} ingrédients disponibles après filtrage"
            )

        sub_matrix = cooc_matrix.reindex(index=top_final, columns=top_final)
        if sub_matrix.isna().any().any():
            self.logger.warning("⚠️ NaN détectés dans sous-matrice; remplissage à 0")
            sub_matrix = sub_matrix.fillna(0)

        self.logger.info(
            f"✅ Sélection finale: {len(top_final)} ingrédients | shape={sub_matrix.shape}"
        )
        return sub_matrix, top_final

    def _perform_clustering(self, matrix: pd.DataFrame, n_clusters: int) -> np.ndarray:
        """Effectue le clustering K-means sur la matrice.

        Args:
            matrix: Matrice de co-occurrence.
            n_clusters: Nombre de clusters.

        Returns:
            Array des labels de cluster.
        """
        self.logger.info(f"Performing K-means clustering with k={n_clusters}")

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(matrix.values)

        self.logger.info(f"Clustering completed: {len(set(clusters))} unique clusters")

        return clusters

    def _generate_tsne(
        self, matrix: pd.DataFrame, clusters: np.ndarray, perplexity: int
    ) -> dict:
        """Génère la visualisation t-SNE.

        Args:
            matrix: Matrice de co-occurrence.
            clusters: Labels de cluster.
            perplexity: Paramètre de perplexité.

        Returns:
            Dict avec coordonnées x, y et métadonnées.
        """
        self.logger.info(f"Generating t-SNE visualization with perplexity={perplexity}")

        try:
            # Ajuster la perplexité si nécessaire
            n_samples = matrix.shape[0]
            adjusted_perplexity = min(perplexity, n_samples - 1)

            if adjusted_perplexity != perplexity:
                self.logger.warning(
                    f"Perplexity adjusted from {perplexity} to {adjusted_perplexity} (n_samples={n_samples})"
                )

            # t-SNE
            tsne = TSNE(
                n_components=2,
                perplexity=adjusted_perplexity,
                random_state=42,
                max_iter=1000,
            )

            coords = tsne.fit_transform(matrix.values)

            return {
                "x_coords": coords[:, 0].tolist(),
                "y_coords": coords[:, 1].tolist(),
                "ingredient_names": matrix.index.tolist(),
                "cluster_labels": clusters.tolist(),
                "n_clusters": len(set(clusters)),
                "tsne_params": {
                    "perplexity": adjusted_perplexity,
                    "max_iter": 1000,
                    "random_state": 42,
                    "method": "tsne",
                },
            }

        except Exception as e:
            self.logger.error(f"t-SNE failed: {e}")
            return {"error": str(e)}

    def render_cooccurrence_analysis(
        self, ingredient_names: list[str], matrix: pd.DataFrame
    ) -> None:
        """Affiche l'analyse de co-occurrence interactive."""
        st.subheader("🔍 Analyse de Co-occurrence")

        col1, col2 = st.columns(2)

        with col1:
            ing1 = st.selectbox("Premier ingrédient", options=ingredient_names, index=0)

        with col2:
            ing2 = st.selectbox(
                "Deuxième ingrédient",
                options=ingredient_names,
                index=1 if len(ingredient_names) > 1 else 0,
            )

        if ing1 and ing2 and ing1 != ing2:
            try:
                score = matrix.at[ing1, ing2]
                max_score = matrix.values.max()
                avg_score = matrix.values[matrix.values > 0].mean()

                col_m1, col_m2, col_m3 = st.columns(3)

                with col_m1:
                    st.metric("Score", f"{score:.0f}", help="Nombre de recettes communes")

                with col_m2:
                    percentile = (score / max_score) * 100 if max_score > 0 else 0
                    st.metric("Percentile", f"{percentile:.1f}%")

                with col_m3:
                    ratio = score / avg_score if avg_score > 0 else 0
                    st.metric("vs Moyenne", f"{ratio:.1f}x")

                # Barre de progression
                if max_score > 0:
                    st.progress(score / max_score)

                # Interprétation
                if score >= avg_score * 2:
                    st.success("🔥 Combinaison très fréquente!")
                elif score >= avg_score:
                    st.info("✅ Combinaison courante")
                elif score > 0:
                    st.warning("⚠️ Combinaison rare")
                else:
                    st.error("❌ Aucune co-occurrence")

            except Exception as e:
                st.warning(f"Erreur: {e}")

    def render_clusters(
        self, clusters: np.ndarray, ingredient_names: list[str], n_clusters: int
    ) -> None:
        """Affiche les clusters d'ingrédients."""
        st.subheader("🎯 Clusters d'Ingrédients")

        colors = ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "⚫", "⚪", "🟤", "🔘"]

        for cluster_id in range(n_clusters):
            cluster_ings = [
                ingredient_names[i]
                for i, c in enumerate(clusters)
                if c == cluster_id
            ]

            color = colors[cluster_id % len(colors)]

            with st.expander(
                f"{color} Cluster {cluster_id + 1} ({len(cluster_ings)} ingrédients)",
                expanded=cluster_id < 2,  # Expand first 2 clusters only
            ):
                cols = st.columns(4)
                for i, ing in enumerate(cluster_ings):
                    cols[i % 4].write(f"• **{ing}**")

    def render_tsne_visualization(self, tsne_data: dict) -> None:
        """Affiche la visualisation t-SNE."""
        st.subheader("🎨 Visualisation t-SNE 2D")

        if "error" in tsne_data:
            st.error(f"❌ Erreur t-SNE: {tsne_data['error']}")
            return

        # Créer le graphique
        fig = go.Figure()

        colors = [
            "#FF6B6B",
            "#4ECDC4",
            "#45B7D1",
            "#96CEB4",
            "#FFEAA7",
            "#DDA0DD",
            "#98D8C8",
            "#F7DC6F",
            "#BB8FCE",
            "#85C1E9",
            "#F8B88B",
            "#FAA0A0",
            "#B0E57C",
            "#87CEEB",
            "#DDA0DD",
            "#F0E68C",
            "#FFB6C1",
            "#20B2AA",
            "#FF69B4",
            "#BA55D3",
        ]

        n_clusters = tsne_data["n_clusters"]

        for cluster_id in range(n_clusters):
            mask = [label == cluster_id for label in tsne_data["cluster_labels"]]
            cluster_x = [x for i, x in enumerate(tsne_data["x_coords"]) if mask[i]]
            cluster_y = [y for i, y in enumerate(tsne_data["y_coords"]) if mask[i]]
            cluster_names = [
                name for i, name in enumerate(tsne_data["ingredient_names"]) if mask[i]
            ]

            color = colors[cluster_id % len(colors)]

            fig.add_trace(
                go.Scatter(
                    x=cluster_x,
                    y=cluster_y,
                    mode="markers+text",
                    marker=dict(size=12, color=color, line=dict(width=2, color="white"), opacity=0.8),
                    text=cluster_names,
                    textposition="top center",
                    textfont=dict(size=10),
                    name=f"Cluster {cluster_id + 1}",
                    hovertemplate=f"<b>%{{text}}</b><br>Cluster: {cluster_id + 1}<extra></extra>",
                )
            )

        fig.update_layout(
            title="Visualisation t-SNE des Ingrédients",
            xaxis_title="Dimension 1",
            yaxis_title="Dimension 2",
            showlegend=True,
            height=600,
            hovermode="closest",
            plot_bgcolor="rgba(245,245,245,0.8)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )

        st.plotly_chart(fig, use_container_width=True)

        with st.expander("ℹ️ À propos de t-SNE"):
            st.markdown(
                """
            **t-SNE** réduit la dimensionnalité pour visualiser les similarités entre ingrédients.
            
            - **Points proches** = ingrédients avec profils de co-occurrence similaires
            - **Couleurs** = clusters K-means
            - **Distance** = mesure de similarité culinaire
            
            **Paramètres utilisés**:
            - Perplexité: {}
            - Itérations: 1000
            - Seed: 42
            """.format(
                    tsne_data["tsne_params"]["perplexity"]
                )
            )

    def render_sidebar_statistics(
        self, clusters: np.ndarray, ingredient_names: list[str]
    ) -> None:
        """Affiche les statistiques dans la sidebar."""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Statistiques")

        cluster_counts = pd.Series(clusters).value_counts().sort_index()

        st.sidebar.metric("Ingrédients analysés", len(ingredient_names))
        st.sidebar.metric("Clusters créés", len(cluster_counts))

        # Graphique
        st.sidebar.markdown("**Répartition:**")

        colors = [
            "#FF6B6B",
            "#4ECDC4",
            "#45B7D1",
            "#96CEB4",
            "#FFEAA7",
            "#DDA0DD",
            "#98D8C8",
            "#F7DC6F",
            "#BB8FCE",
            "#85C1E9",
        ]

        fig = go.Figure()

        for i, count in enumerate(cluster_counts):
            percentage = (count / len(ingredient_names)) * 100
            color = colors[i % len(colors)]

            fig.add_trace(
                go.Bar(
                    x=[count],
                    y=[f"C{i + 1}"],
                    orientation="h",
                    marker_color=color,
                    text=f"{count} ({percentage:.0f}%)",
                    textposition="outside",
                    showlegend=False,
                )
            )

        fig.update_layout(
            xaxis_title="Nombre",
            height=min(400, len(cluster_counts) * 40 + 100),
            margin=dict(l=10, r=10, t=10, b=10),
            font=dict(size=10),
        )

        st.sidebar.plotly_chart(fig, use_container_width=True)

    def _render_step_1_preprocessing(self) -> None:
        """Affiche l'étape 1 : Prétraitement NLP des ingrédients."""
        st.markdown("---")
        st.header("📈 ÉTAPE 1 : Prétraitement NLP des ingrédients")

        st.markdown(
            """
        **Question :** Comment normaliser et regrouper les variantes d'un même ingrédient ?

        Les recettes utilisent des descriptions variées pour un même ingrédient (ex: "sel", "gros sel",
        "sel de mer", "sel fin"). Le prétraitement NLP vise à identifier et regrouper ces variantes
        pour créer une représentation cohérente.

        **Métrique :** Taux de réduction du nombre d'ingrédients uniques après normalisation.
        
        **💡 Note technique :** Cette étape a été **précalculée à froid** lors de la génération de la 
        matrice 300×300 avec `utils/preprocess_ingredients_matrix.py`. Environ **~230,000 recettes** ont 
        été traitées pour extraire et normaliser les 300 ingrédients les plus fréquents.

        **Méthodologie appliquée :**
        - Normalisation : minuscules, suppression ponctuation, filtrage stop words
        - Regroupement : variantes lexicales fusionnées
        - Réduction typique : ~70% des variantes éliminées

        **🎯 Résultat :** Le prétraitement réduit significativement la redondance en identifiant
        les variantes linguistiques d'un même ingrédient. Cette étape est cruciale pour obtenir une
        matrice de co-occurrence fiable et permet de concentrer l'analyse sur les véritables patterns
        culinaires plutôt que sur les variations de nomenclature.
        """
        )

    def _render_step_2_cooccurrence(
        self, ingredient_names: list[str], matrix: pd.DataFrame
    ) -> None:
        """Affiche l'étape 2 : Création de la matrice de co-occurrence."""
        st.markdown("---")
        st.header("📈 ÉTAPE 2 : Matrice de co-occurrence")

        st.markdown(
            """
        **Objectif :** Quantifier la fréquence d'apparition conjointe de chaque paire d'ingrédients.

        La matrice de co-occurrence capture l'information fondamentale : combien de fois deux
        ingrédients apparaissent ensemble dans les recettes. Cette matrice symétrique constitue
        la base de notre analyse de similarité.

        **Méthode :** Pour chaque recette, toutes les paires d'ingrédients présents sont comptabilisées.
        
        **💡 Note technique :** Cette matrice **300×300** a été **précalculée à froid** sur l'ensemble 
        du corpus (~230,000 recettes). Vous sélectionnez dynamiquement un sous-ensemble (40-300 ingrédients) 
        de cette matrice pour votre analyse.
        """
        )

        # Statistiques de la matrice
        total_cooccurrences = int(matrix.values.sum() / 2)
        non_zero_pairs = int((matrix.values > 0).sum() / 2)
        matrix_size = len(ingredient_names)
        max_possible_pairs = matrix_size * (matrix_size - 1) / 2
        sparsity = (1 - non_zero_pairs / max_possible_pairs) * 100

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Dimension matrice", f"{matrix_size}×{matrix_size}")
        with col2:
            st.metric("Co-occurrences totales", f"{total_cooccurrences:,}")
        with col3:
            st.metric("Paires non-nulles", f"{non_zero_pairs:,}")
        with col4:
            st.metric(
                "Sparsité",
                f"{sparsity:.1f}%",
                help="Pourcentage de paires sans co-occurrence",
            )

        st.markdown("---")

        # Analyse interactive de co-occurrence
        self.render_cooccurrence_analysis(ingredient_names, matrix)

        st.markdown(
            """
        **📊 Ce que révèle la matrice :**

        La distribution des co-occurrences n'est pas uniforme. Certaines paires d'ingrédients
        apparaissent ensemble dans des milliers de recettes, révélant des associations culinaires
        fortes.

        """
        )

    def _render_step_3_clustering(
        self, clusters: np.ndarray, ingredient_names: list[str], n_clusters: int
    ) -> None:
        """Affiche l'étape 3 : Clustering K-means."""
        st.markdown("---")
        st.header("📈 ÉTAPE 3 : Clustering K-means")

        st.markdown(
            f"""
        **Objectif :** Regrouper automatiquement les ingrédients en {n_clusters} familles distinctes.

        L'algorithme K-means partitionne les ingrédients en fonction de leurs profils de co-occurrence.
        Deux ingrédients dans le même cluster partagent des contextes d'utilisation similaires, même
        s'ils ne co-occurrent pas directement.

        **Méthode :** K-means avec k={n_clusters}, distance euclidienne sur les vecteurs de co-occurrence.
        """
        )

        # Statistiques des clusters
        cluster_counts = pd.Series(clusters).value_counts().sort_index()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nombre de clusters", n_clusters)
        with col2:
            avg_size = len(ingredient_names) / n_clusters
            st.metric("Taille moyenne", f"{avg_size:.1f} ingrédients")
        with col3:
            largest_cluster_size = cluster_counts.max()
            st.metric("Plus grand cluster", f"{largest_cluster_size} ingrédients")

        st.markdown("---")

        # Affichage des clusters
        self.render_clusters(clusters, ingredient_names, n_clusters)

        st.markdown(
            f"""
        **🎯 Interprétation des clusters :**

        Les clusters arrivent à révéler des "famille culinaire" d'ingrédients. Ils peuvent être :
        - **Ingrédients pour patisserie**
        - **Produits de recettes salés**

        **Limite méthodologique** : Le choix de k={n_clusters} est paramétrique. Différentes valeurs
        de k révèlent des structures à différentes granularités.
        De plus, les clusters ont tendance à ne pas être de la même taille car une masse d'ingrédient à faible co-occurence se regrouppent ensemble.
        """
        )

    def _render_step_4_visualization(self, tsne_data: dict) -> None:
        """Affiche l'étape 4 : Visualisation t-SNE 2D."""
        st.markdown("---")
        st.header("📈 ÉTAPE 4 : Visualisation t-SNE 2D")

        st.markdown(
            """
        **Objectif :** Projeter l'espace haute-dimensionnalité des co-occurrences en 2D pour exploration visuelle.

        La matrice de co-occurrence est un espace à n dimensions (une par ingrédient). t-SNE
        (t-Distributed Stochastic Neighbor Embedding) réduit cette dimensionnalité à 2D tout en
        préservant les proximités locales.

        **Méthode :** t-SNE avec perplexité ajustée, optimisation par descente de gradient.
        """
        )

        # Visualisation t-SNE
        self.render_tsne_visualization(tsne_data)

        st.markdown(
            """
        **🔍 Lecture de la visualisation :**

        - **Proximité spatiale** : Les ingrédients proches dans l'espace 2D ont des profils de
          co-occurrence similaires (utilisés dans des contextes culinaires similaires)
        - **Couleurs** : Chaque couleur représente un cluster K-means. La cohésion spatiale des
          couleurs valide la qualité du clustering
        - **Groupes isolés** : Les clusters bien séparés géographiquement indiquent des familles
          culinaires distinctes

        **💡 Insights visuels :**

        La visualisation révèle souvent une structure non-linéaire de l'espace culinaire. Certains
        ingrédients "pont" peuvent se situer entre plusieurs clusters, reflétant leur polyvalence
        (ex: l'huile d'olive utilisée dans de multiples contextes, ou l'eau).

        **Validation du clustering** : Si les couleurs (clusters K-means) forment des groupes
        visuellement cohérents dans l'espace t-SNE, cela confirme que le clustering a capturé
        des structures réelles plutôt qu'artificielles.

        **Limite de t-SNE** : La représentation 2D est approximative. Les distances absolues ne
        sont pas strictement préservées, seules les proximités relatives comptent. Différentes
        exécutions peuvent donner des configurations légèrement différentes (non-déterminisme).
        """
        )

    def _render_conclusion(
        self, ingredient_names: list[str], clusters: np.ndarray, n_clusters: int
    ) -> None:
        """Affiche la conclusion de l'analyse."""
        st.markdown("---")
        st.subheader("📋 Conclusion de l'analyse")

        # Calculer quelques statistiques finales
        cluster_counts = pd.Series(clusters).value_counts()
        largest_cluster = cluster_counts.max()
        smallest_cluster = cluster_counts.min()

        st.markdown(
            f"""
        ### Synthèse des résultats

        **1. Prétraitement NLP réussi :** La normalisation automatique a permis de réduire
        significativement la redondance des variantes d'ingrédients, créant une base solide
        pour l'analyse.

        **2. Structure révélée par la co-occurrence :** L'analyse de {len(ingredient_names)}
        ingrédients a révélé des patterns clairs d'association culinaire, confirmant que la
        cuisine n'est pas aléatoire.

        **3. Clustering cohérent :** L'algorithme K-means a identifié {n_clusters} familles
        d'ingrédients distinctes, avec des tailles variant de {smallest_cluster} à {largest_cluster}
        ingrédients. Ces clusters essaye de capturer des insight sur le co-usage des ingrédients.

        **4. Validation visuelle :** La projection t-SNE montre la structure des clusters et
        l'organisation de l'espace culinaire.

        ### Applications pratiques

        Ces résultats peuvent être utilisés pour :
        - **Systèmes de recommandation** : Suggérer des ingrédients complémentaires lors de la
          création de recettes
        - **Analyse nutritionnelle** : Identifier les associations alimentaires courantes pour
          des études diététiques, nottament en reliant les informations caloriques
        - **Créativité culinaire** : Découvrir des combinaisons innovantes en explorant les
          frontières entre clusters
        - **Détection d'anomalies** : Identifier des recettes avec des combinaisons inhabituelles

        ### Limites et perspectives

        **Limites :**
        - La co-occurrence ne capture pas l'ordre ou les quantités des ingrédients
        - Les ingrédients très rares ne sont pas représentés et ceux trop présent
        peuvent être mal représentés

        **Perspectives d'amélioration :**
        - Clustering hiérarchique pour révéler plusieurs niveaux de granularité
        - Intégration d'informations sémantiques (catégories nutritionnelles, origines)
        - Modèles de recommandation basés sur les embeddings d'ingrédients
        """
        )

    def run(self) -> None:
        """Point d'entrée principal de la page."""
        self.logger.info("Starting ingredients clustering analysis with precomputed matrix")

        # Introduction et User Story
        with st.expander("🎯 Objectifs et méthodologie de l'analyse", expanded=True):
            st.markdown(
                """
            ### Peut-on regrouper les ingrédients selon leurs usages culinaires ?

            Cette analyse explore les patterns de co-occurrence d'ingrédients dans les recettes pour
            identifier les associations culinaires naturelles. En analysant des milliers de recettes,
            nous révélons les combinaisons d'ingrédients qui apparaissent fréquemment ensemble.

            **Questions centrales :** Quels ingrédients sont naturellement associés ? Existe-t-il des
            familles d'ingrédients distinctes ? Comment les ingrédients se regroupent-ils en fonction
            de leurs profils d'utilisation ?

            **Approche :** 
            - **Étapes 1-2 (précalculées à froid)** : Analyse NLP des listes d'ingrédients et construction 
              d'une matrice de co-occurrence 300×300
            - **Étapes 3-4 (temps réel)** : Clustering automatique par K-means et visualisation en 2D par t-SNE

            **Problématique :** Dans un espace culinaire où des milliers d'ingrédients peuvent être
            combinés, comment identifier automatiquement les groupes d'ingrédients qui partagent des
            contextes d'utilisation similaires ?
            
            **💡 Optimisation** : Les étapes 1-2 sont précalculées pour accélérer l'analyse. Vous ajustez 
            le nombre d'ingrédients (40-300) et de clusters (3-20) en temps réel.
            """
            )

        # Sidebar
        params = self.render_sidebar()
        self.logger.debug(f"Parameters: {params}")

        # Charger la matrice précalculée
        data = self._load_cooccurrence_matrix()

        if data is None:
            return

        full_matrix, ingredients_list = data

        # Vérifier si les paramètres ont changé
        params_changed = False
        if "last_params" in st.session_state:
            last = st.session_state["last_params"]
            if (
                last["n_ingredients"] != params["n_ingredients"]
                or last["n_clusters"] != params["n_clusters"]
                or last["tsne_perplexity"] != params["tsne_perplexity"]
            ):
                params_changed = True

        # Décider si on lance l'analyse
        should_analyze = (
            params["analyze_button"]
            or "clusters" not in st.session_state
            or params_changed
        )

        if should_analyze:
            self.logger.info(
                f"Running analysis: n_ingredients={params['n_ingredients']}, n_clusters={params['n_clusters']}"
            )

            with st.spinner("Analyse en cours..."):
                # Sélectionner les top N ingrédients
                matrix, ingredient_names = self._select_top_ingredients(
                    full_matrix, ingredients_list, params["n_ingredients"]
                )

                # Clustering
                clusters = self._perform_clustering(matrix, params["n_clusters"])

                # t-SNE
                tsne_data = self._generate_tsne(matrix, clusters, params["tsne_perplexity"])

                # Sauvegarder dans session
                st.session_state["matrix"] = matrix
                st.session_state["ingredient_names"] = ingredient_names
                st.session_state["clusters"] = clusters
                st.session_state["tsne_data"] = tsne_data
                st.session_state["last_params"] = params.copy()

        # Afficher les résultats si disponibles
        if "clusters" in st.session_state:
            matrix = st.session_state["matrix"]
            ingredient_names = st.session_state["ingredient_names"]
            clusters = st.session_state["clusters"]
            tsne_data = st.session_state["tsne_data"]

            # Métriques
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Matrice source", "300x300")
            with col2:
                st.metric("🥘 Ingrédients analysés", f"{len(ingredient_names)}")
            with col3:
                st.metric("🎯 Clusters créés", f"{params['n_clusters']}")

            # ÉTAPES
            self._render_step_1_preprocessing()
            self._render_step_2_cooccurrence(ingredient_names, matrix)
            self._render_step_3_clustering(clusters, ingredient_names, params["n_clusters"])
            self._render_step_4_visualization(tsne_data)
            self._render_conclusion(ingredient_names, clusters, params["n_clusters"])

            # Statistiques sidebar
            self.render_sidebar_statistics(clusters, ingredient_names)

        # Footer
        st.markdown("---")
        st.caption(
            "💡 **Configuration** : Ajustez les paramètres dans la sidebar pour explorer différentes configurations."
        )

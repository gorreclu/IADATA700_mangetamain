from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
import urllib.request

import streamlit as st

# Ajouter le répertoire parent au chemin Python pour les imports
sys.path.append(str(Path(__file__).parent))

from components.ingredients_clustering_page import IngredientsClusteringPage
from components.popularity_analysis_page import PopularityAnalysisPage
from core.data_explorer import DataExplorer
from core.data_loader import DataLoader
from core.logger import get_logger, setup_logging

DEFAULT_RECIPES = Path("data/RAW_recipes.csv")
DEFAULT_INTERACTIONS = Path("data/RAW_interactions.csv")

# S3 URLs pour les fichiers de données
S3_URLS = {
    "RAW_recipes.csv": "https://iadata700-mangetamain-data.s3.eu-west-3.amazonaws.com/RAW_recipes+2.csv",
    "RAW_interactions.csv": "https://iadata700-mangetamain-data.s3.eu-west-3.amazonaws.com/RAW_interactions+3.csv",
}


@dataclass
class AppConfig:
    default_recipes_path: Path = DEFAULT_RECIPES
    default_interactions_path: Path = DEFAULT_INTERACTIONS
    page_title: str = "Mangetamain - Analyse de Données"
    layout: str = "wide"


class App:
    """Application Streamlit pour l'analyse de données de recettes."""

    def __init__(self, config: AppConfig | None = None):
        self.config = config or AppConfig()

        # Setup logging for the application with performance focus
        setup_logging(level="WARNING")  # Less verbose for better performance
        self.logger = get_logger()
        self.logger.info("Mangetamain application starting")

    @staticmethod
    @st.cache_data
    def _download_file(url: str, destination: Path) -> bool:
        """Télécharge un fichier depuis une URL vers un chemin local."""
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Python-urllib/3.12 MangetamainApp/1.0",
                    "Accept": "*/*",
                    "Accept-Encoding": "identity",
                },
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                chunk_size = 1024 * 1024  # 1MB chunks

                with open(destination, "wb") as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)

            return True
        except Exception:
            return False

    def _ensure_data_files(self):
        """S'assure que tous les fichiers de données sont présents."""
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        required_files = ["RAW_recipes.csv", "RAW_interactions.csv"]
        missing_files = []

        for filename in required_files:
            filepath = data_dir / filename
            if not filepath.exists() or filepath.stat().st_size < 1000:
                missing_files.append(filename)

        if not missing_files:
            return True

        st.info("📥 Téléchargement des données depuis AWS S3...")
        progress_bar = st.progress(0)
        status_text = st.empty()

        total_files = len(missing_files)

        for i, filename in enumerate(missing_files):
            status_text.text(f"Téléchargement de {filename}...")
            progress = int((i / total_files) * 100)
            progress_bar.progress(progress)

            url = S3_URLS[filename]
            destination = data_dir / filename

            if not App._download_file(url, destination):
                st.error(f"❌ Échec du téléchargement de {filename}")
                return False

        progress_bar.progress(100)
        status_text.text("✅ Téléchargement terminé!")
        st.success("Données téléchargées avec succès!")
        return True

    def _sidebar(self) -> dict:
        """Configuration de la sidebar avec sélection des pages et datasets."""
        st.sidebar.header("Navigation")

        # Sélection de la page
        page = st.sidebar.selectbox(
            "Page",
            [
                "Home",
                "Analyse de clustering des ingrédients",
                "Analyse popularité des recettes",
            ],
            key="page_select_box",
        )

        if page == "Analyse de clustering des ingrédients":
            st.sidebar.markdown(f"### {page}")
            st.sidebar.caption("Clustering d'ingrédients basé sur la co-occurrence.")
            return {"page": page}
        if page == "Analyse popularité des recettes":
            st.sidebar.markdown(f"### {page}")
            st.sidebar.caption("Relations popularité / notes / caractéristiques")
            return {"page": page}

        # Configuration pour la page Home
        st.sidebar.markdown("### Configuration des données")

        # Sélection du dataset
        dataset_type = st.sidebar.radio(
            "Type de dataset",
            ["recettes", "interactions"],
            key="dataset_type",
        )

        # Chemin par défaut selon le type
        if dataset_type == "recettes":
            default_path = self.config.default_recipes_path
            st.sidebar.caption("Analyse dédiée aux recettes (RAW_recipes).")
        else:
            default_path = self.config.default_interactions_path
            st.sidebar.caption("Analyse des interactions utilisateur-recette.")

        # Options de rechargement
        refresh = st.sidebar.checkbox("Forcer le rechargement", value=False, key="force_refresh")

        return {
            "page": page,
            "path": default_path,
            "refresh": refresh,
            "active": dataset_type,
        }

    def run(self):
        """Point d'entrée principal de l'application."""
        st.set_page_config(
            page_title=self.config.page_title,
            layout=self.config.layout,
        )

        # Vérifier et télécharger les données si nécessaire
        if not self._ensure_data_files():
            st.error("❌ Impossible de charger les données. Veuillez réessayer.")
            st.stop()

        # Gestion du titre dynamique
        page = st.session_state.get("page_select_box", "Home")

        if page == "Analyse de clustering des ingrédients":
            st.title("🍳 Analyse de clustering des ingrédients")
        elif page == "Analyse popularité des recettes":
            st.title("🔥 Analyse popularité des recettes")
        else:
            st.title("🏠 Home - Data Explorer")

        selection = self._sidebar()
        page = selection.get("page")

        # Logique des pages
        if page == "Analyse de clustering des ingrédients":
            clustering_page = IngredientsClusteringPage(str(self.config.default_recipes_path))
            clustering_page.run()
            return
        if page == "Analyse popularité des recettes":
            popularity_page = PopularityAnalysisPage(
                interactions_path=str(self.config.default_interactions_path),
                recipes_path=str(self.config.default_recipes_path),
            )
            popularity_page.run()
            return

        # Page Home - Affichage des données avec exploration
        self._render_home_page(selection)

    def _render_home_page(self, selection: dict):
        """Rendu de la page d'accueil avec exploration des données."""
        data_path = selection["path"]
        refresh = selection["refresh"]
        dataset_type = selection["active"]

        loader = DataLoader(data_path)

        try:
            self.logger.debug(f"Attempting to load {dataset_type} data from {data_path}")
            loader.load_data(force=refresh)
            self.logger.info(f"Successfully loaded {dataset_type} data")
        except FileNotFoundError:
            self.logger.warning(f"File not found: {data_path}")
            st.warning(f"Fichier introuvable: {data_path}. Vous pouvez en téléverser un ci-dessous.")
            uploaded = st.file_uploader("Déposer un fichier CSV", type=["csv"], key="uploader")
            if uploaded is not None:
                import pandas as pd

                try:
                    tmp_df = pd.read_csv(uploaded)
                    self.logger.info(f"Successfully loaded {dataset_type} from upload: {tmp_df.shape}")
                except Exception as e:
                    self.logger.error(f"Error reading uploaded file: {e}")
                    st.error(f"Erreur lors de la lecture: {e}")
                    return
        except Exception as e:
            self.logger.error(f"Unexpected error during data loading: {e}")
            st.error(f"Erreur chargement données: {e}")
            return

        # Explorer de base pour tous les types de données
        self.logger.debug("Initializing DataExplorer")
        explorer = DataExplorer(loader=loader)
        self.logger.info(
            f"Data overview: {explorer.df.shape} rows/cols, " f"{explorer.df.memory_usage(deep=True).sum() / 1024**2:.1f} MB"
        )

        st.subheader("📋 Aperçu des données (10 premières lignes)")
        st.dataframe(explorer.df.head(10))

        # Affichage des informations de base
        st.subheader("📊 Informations sur le dataset")
        with st.expander("Informations générales", expanded=True):
            df = explorer.df
            missing_values = df.isnull().sum().sum()
            memory_mb = df.memory_usage(deep=True).sum() / 1024**2

            self.logger.debug(f"Dataset analysis: {len(df)} rows, {len(df.columns)} cols, {missing_values} missing values")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Nombre de lignes", f"{len(df):,}")
                st.metric("Nombre de colonnes", len(df.columns))
            with col2:
                st.metric("Taille mémoire", f"{memory_mb:.1f} MB")
                st.metric("Valeurs manquantes", f"{missing_values:,}")

        with st.expander("Types de données"):
            # Certains objets dtype (extension / objets Python) provoquent une erreur
            # ArrowInvalid lors de la conversion interne Streamlit -> Arrow
            # (ex: numpy.dtype objects non sérialisables). On convertit donc en str.
            dtypes_df = df.dtypes.apply(lambda x: str(x)).to_frame("Type")
            st.dataframe(dtypes_df)

        with st.expander("Analyse des colonnes clés"):
            # Analyse spécifique aux recettes si les colonnes existent
            if "ingredients" in df.columns:
                st.write("🥘 **Ingrédients** :")
                # Compter les recettes avec ingrédients valides
                valid_ingredients = df["ingredients"].notna().sum()
                st.write(f"- Recettes avec ingrédients : {valid_ingredients:,}")

            if "name" in df.columns:
                st.write("📝 **Noms de recettes** :")
                unique_names = df["name"].nunique()
                st.write(f"- Recettes uniques : {unique_names:,}")

            if "minutes" in df.columns:
                st.write("⏱️ **Temps de préparation** :")
                avg_minutes = df["minutes"].mean()
                st.write(f"- Temps moyen : {avg_minutes:.1f} minutes")

            if "n_steps" in df.columns:
                st.write("📋 **Étapes de préparation** :")
                avg_steps = df["n_steps"].mean()
                st.write(f"- Nombre moyen d'étapes : {avg_steps:.1f}")


def main():
    """Point d'entrée pour l'exécution directe via streamlit run."""
    App().run()


if __name__ == "__main__":
    main()

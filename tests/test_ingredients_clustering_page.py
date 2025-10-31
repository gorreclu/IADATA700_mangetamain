"""
Tests for IngredientsClusteringPage - Comprehensive Test Suite
================================================================

Test suite pour la page d'analyse de clustering des ingrédients.
Tests basés sur la même structure que test_popularity_analysis_page.py
avec focus sur les fonctionnalités spécifiques au clustering.
"""

from components.ingredients_clustering_page import (
    IngredientsClusteringPage,
    IngredientsClusteringConfig,
)
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import warnings
from unittest.mock import Mock, MagicMock, patch

# Suppress warnings during testing
warnings.filterwarnings("ignore")

# Add src to path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestIngredientsClusteringConfig:
    """Test la dataclass de configuration."""

    def test_config_creation(self):
        """Test la création basique de configuration avec nouvelle API (matrice précalculée)."""
        config = IngredientsClusteringConfig(
            matrix_path=Path("data/ingredients_cooccurrence_matrix.csv"),
            ingredients_list_path=Path("data/ingredients_list.csv"),
            n_ingredients=50,
            n_clusters=5,
            tsne_perplexity=30,
        )
        assert config.matrix_path == Path("data/ingredients_cooccurrence_matrix.csv")
        assert config.ingredients_list_path == Path("data/ingredients_list.csv")
        assert config.n_ingredients == 50
        assert config.n_clusters == 5
        assert config.tsne_perplexity == 30

    def test_config_with_defaults(self):
        """Test que les valeurs par défaut sont correctement appliquées."""
        config = IngredientsClusteringConfig()
        assert config.matrix_path == Path("data/ingredients_cooccurrence_matrix.csv")
        assert config.ingredients_list_path == Path("data/ingredients_list.csv")
        assert config.n_ingredients == 40  # Valeur par défaut
        assert config.n_clusters == 4
        assert config.tsne_perplexity == 30

    def test_config_path_types(self):
        """Test la gestion des différents types de chemins."""
        # Test avec Path
        config1 = IngredientsClusteringConfig(
            matrix_path=Path("data/matrix.csv"),
            ingredients_list_path=Path("data/list.csv")
        )
        assert isinstance(config1.matrix_path, Path)
        assert isinstance(config1.ingredients_list_path, Path)


class TestIngredientsClusteringPage:
    """Test la classe principale IngredientsClusteringPage."""

    @pytest.fixture
    def sample_recipes_data(self):
        """Génère des données de recettes réalistes avec ingrédients."""
        np.random.seed(42)
        n_recipes = 100

        # Liste d'ingrédients courants pour créer des combinaisons réalistes
        common_ingredients = [
            "salt",
            "pepper",
            "sugar",
            "flour",
            "butter",
            "eggs",
            "milk",
            "onion",
            "garlic",
            "olive oil",
            "tomato",
            "cheese",
            "chicken",
            "beef",
            "rice",
            "pasta",
            "carrot",
            "potato",
            "lemon",
            "basil",
        ]

        # Créer des listes d'ingrédients pour chaque recette
        ingredients_lists = []
        for _ in range(n_recipes):
            n_ingredients = np.random.randint(3, 10)
            recipe_ingredients = list(np.random.choice(common_ingredients, size=n_ingredients, replace=False))
            ingredients_lists.append(str(recipe_ingredients))

        data = {
            "id": range(1, n_recipes + 1),
            "name": [f"Recipe {i}" for i in range(1, n_recipes + 1)],
            "ingredients": ingredients_lists,
            "minutes": np.random.randint(5, 180, n_recipes),
            "n_steps": np.random.randint(1, 20, n_recipes),
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_recipes_file(self, sample_recipes_data):
        """Crée un fichier CSV temporaire pour les tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recipes_path = Path(tmpdir) / "recipes.csv"
            sample_recipes_data.to_csv(recipes_path, index=False)
            yield recipes_path

    @pytest.fixture
    def temp_matrix_files(self):
        """Crée des fichiers temporaires de matrice et liste pour les tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Créer une mini matrice 5x5 pour les tests
            ingredients = ["flour", "sugar", "eggs", "butter", "milk"]
            matrix = pd.DataFrame(
                np.random.randint(0, 50, (5, 5)),
                index=ingredients,
                columns=ingredients
            )
            matrix_path = Path(tmpdir) / "matrix.csv"
            matrix.to_csv(matrix_path)
            
            # Créer la liste des ingrédients
            ing_list = pd.DataFrame({
                "ingredient": ingredients,
                "frequency": [100, 90, 80, 70, 60]
            })
            list_path = Path(tmpdir) / "list.csv"
            ing_list.to_csv(list_path, index=False)
            
            yield matrix_path, list_path

    @pytest.fixture
    def page_instance(self, temp_matrix_files):
        """Crée une instance de IngredientsClusteringPage pour les tests."""
        matrix_path, list_path = temp_matrix_files
        return IngredientsClusteringPage(str(matrix_path), str(list_path))

    def test_initialization(self, temp_matrix_files):
        """Test l'initialisation basique de la page avec nouvelle API."""
        matrix_path, list_path = temp_matrix_files
        page = IngredientsClusteringPage(str(matrix_path), str(list_path))

        assert page.matrix_path == Path(matrix_path)
        assert page.ingredients_list_path == Path(list_path)
        assert page.logger is not None

    def test_initialization_with_default_path(self):
        """Test l'initialisation avec le chemin par défaut."""
        page = IngredientsClusteringPage()
        assert page.matrix_path == Path("data/ingredients_cooccurrence_matrix.csv")
        assert page.ingredients_list_path == Path("data/ingredients_list.csv")

    def test_initialization_accepts_both_paths(self):
        """Test que l'initialisation accepte les deux chemins."""
        page = IngredientsClusteringPage(
            matrix_path="custom/matrix.csv",
            ingredients_list_path="custom/list.csv"
        )
        assert page.matrix_path == Path("custom/matrix.csv")
        assert page.ingredients_list_path == Path("custom/list.csv")

    def test_render_sidebar_returns_expected_structure(self, page_instance):
        """Test que render_sidebar retourne la structure attendue."""
        with (
            patch("streamlit.sidebar.header"),
            patch("streamlit.sidebar.slider") as mock_slider,
            patch("streamlit.sidebar.subheader"),
            patch("streamlit.sidebar.button") as mock_button,
        ):

            # Configuration des valeurs de retour
            mock_slider.side_effect = [
                50,
                5,
                30,
            ]  # n_ingredients, n_clusters, perplexity
            mock_button.return_value = False

            params = page_instance.render_sidebar()

            # Vérifier la structure du dictionnaire retourné
            expected_keys = [
                "n_ingredients",
                "n_clusters",
                "tsne_perplexity",
                "analyze_button",
            ]
            assert all(key in params for key in expected_keys)

            # Vérifier les types
            assert isinstance(params["n_ingredients"], int)
            assert isinstance(params["n_clusters"], int)
            assert isinstance(params["tsne_perplexity"], int)
            assert isinstance(params["analyze_button"], bool)

    def test_render_sidebar_parameter_ranges(self, page_instance):
        """Test que les paramètres sont dans les bonnes plages."""
        with (
            patch("streamlit.sidebar.header"),
            patch("streamlit.sidebar.slider") as mock_slider,
            patch("streamlit.sidebar.subheader"),
            patch("streamlit.sidebar.button"),
        ):

            # Tester différentes valeurs
            test_values = [
                (100, 8, 25),  # n_ingredients, n_clusters, perplexity
                (10, 2, 5),
                (200, 20, 50),
            ]

            for n_ing, n_clust, perp in test_values:
                mock_slider.side_effect = [n_ing, n_clust, perp]
                params = page_instance.render_sidebar()

                # Vérifier les valeurs
                assert 10 <= params["n_ingredients"] <= 200
                assert 2 <= params["n_clusters"] <= 20
                assert 5 <= params["tsne_perplexity"] <= 50

    def test_render_cooccurrence_analysis_basic(self, page_instance):
        """Test l'affichage de l'analyse de co-occurrence."""
        # Créer des données de test
        ingredient_names = ["salt", "pepper", "sugar", "flour", "butter"]
        matrix = pd.DataFrame(
            np.random.randint(0, 50, (5, 5)),
            index=ingredient_names,
            columns=ingredient_names,
        )

        with (
            patch("streamlit.subheader"),
            patch("streamlit.columns") as mock_columns,
            patch("streamlit.selectbox") as mock_selectbox,
            patch("streamlit.metric"),
            patch("streamlit.progress"),
            patch("streamlit.success"),
            patch("streamlit.info"),
            patch("streamlit.warning"),
            patch("streamlit.error"),
            patch("streamlit.dataframe"),
        ):

            # Simuler la sélection d'ingrédients et les colonnes comme context managers
            mock_col = MagicMock()
            mock_col.__enter__ = Mock(return_value=mock_col)
            mock_col.__exit__ = Mock(return_value=False)
            # Note: render_cooccurrence_analysis utilise st.columns(2)
            mock_columns.return_value = [mock_col, mock_col]
            mock_selectbox.side_effect = ["salt", "pepper"]

            # Ne devrait pas lever d'exception
            page_instance.render_cooccurrence_analysis(ingredient_names, matrix)

    def test_render_clusters_basic(self, page_instance):
        """Test l'affichage des clusters."""
        clusters = np.array([0, 0, 1, 1, 2])
        ingredient_names = ["salt", "pepper", "sugar", "flour", "butter"]
        n_clusters = 3

        with (
            patch("streamlit.subheader"),
            patch("streamlit.expander") as mock_expander,
            patch("streamlit.columns"),
        ):

            mock_expander.return_value.__enter__ = Mock()
            mock_expander.return_value.__exit__ = Mock()

            # Ne devrait pas lever d'exception
            page_instance.render_clusters(clusters, ingredient_names, n_clusters)

    def test_render_clusters_with_empty_cluster(self, page_instance):
        """Test l'affichage quand un cluster est vide."""
        clusters = np.array([0, 0, 0, 0, 0])  # Tous dans le même cluster
        ingredient_names = ["salt", "pepper", "sugar", "flour", "butter"]
        n_clusters = 3  # Mais on demande 3 clusters

        with (
            patch("streamlit.subheader"),
            patch("streamlit.expander"),
            patch("streamlit.columns"),
        ):

            # Ne devrait pas crasher même si certains clusters sont vides
            page_instance.render_clusters(clusters, ingredient_names, n_clusters)

    def test_render_sidebar_statistics_with_data(self, page_instance):
        """Test l'affichage des statistiques avec données valides."""
        clusters = np.array([0, 0, 1, 1, 2])
        ingredient_names = ["salt", "pepper", "sugar", "flour", "butter"]

        with (
            patch("streamlit.sidebar.markdown"),
            patch("streamlit.sidebar.metric"),
            patch("streamlit.sidebar.plotly_chart"),
        ):

            # Ne devrait pas lever d'exception
            page_instance.render_sidebar_statistics(clusters, ingredient_names)

    def test_formal_language_in_methods(self, page_instance):
        """Test que les méthodes utilisent un langage formel."""
        # Vérifier les docstrings
        assert page_instance.run.__doc__ is not None
        assert page_instance.render_sidebar.__doc__ is not None

        # Les docstrings ne devraient pas contenir de langage informel
        informal_words = [" tu ", " vous ", " ton ", " ta ", " votre "]

        for method in [
            page_instance.run,
            page_instance.render_sidebar,
            page_instance.render_cooccurrence_analysis,
        ]:
            if method.__doc__:
                doc_with_spaces = f" {method.__doc__} "
                for word in informal_words:
                    assert word.lower() not in doc_with_spaces.lower()


class TestIngredientsClusteringPageTyping:
    """Test que le typage est correctement appliqué."""

    def test_all_methods_have_type_annotations(self):
        """Vérifie que toutes les méthodes publiques ont des annotations de type."""
        page = IngredientsClusteringPage()

        # Liste des méthodes qui doivent être typées (API mise à jour)
        methods_to_check = [
            "render_sidebar",
            "render_cooccurrence_analysis",
            "render_clusters",
            "render_tsne_visualization",
            "render_sidebar_statistics",
        ]

        for method_name in methods_to_check:
            method = getattr(page, method_name)
            annotations = method.__annotations__

            # Vérifier qu'il y a au moins une annotation (return type)
            assert "return" in annotations, f"{method_name} manque l'annotation de retour"

    def test_return_type_annotations(self):
        """Vérifie les annotations de type de retour."""
        page = IngredientsClusteringPage()

        # Vérifier que render_sidebar retourne un dict
        return_annotation = page.render_sidebar.__annotations__["return"]
        # Les annotations peuvent être des strings en Python 3.9+ avec from __future__ import annotations
        if isinstance(return_annotation, str):
            assert "dict" in return_annotation.lower()
        else:
            assert return_annotation.__name__ == "dict"

        # Vérifier que les méthodes render_* retournent None
        for method_name in [
            "render_cooccurrence_analysis",
            "render_clusters",
            "render_sidebar_statistics",
            "run",
        ]:
            method = getattr(page, method_name)
            return_annotation = method.__annotations__["return"]
            # None type peut être une string ou le type None
            if isinstance(return_annotation, str):
                assert return_annotation == "None"
            else:
                assert return_annotation is None or return_annotation.__name__ == "NoneType"


class TestDocumentation:
    """Test la qualité de la documentation."""

    def test_module_has_docstring(self):
        """Vérifie que le module a une docstring avec User Story."""
        # Au lieu de tester __doc__ du module importé (qui peut être None avec l'optimisation),
        # on vérifie directement le contenu du fichier source
        from pathlib import Path

        module_file = Path(__file__).parent.parent / "src" / "components" / "ingredients_clustering_page.py"

        # Lire le fichier source
        with open(module_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Vérifier qu'il y a une docstring au début (après from __future__)
        lines = content.split("\n")

        # Trouver la première docstring (après imports)
        docstring_found = False
        for i, line in enumerate(lines):
            if '"""' in line and i < 20:  # Dans les 20 premières lignes
                docstring_found = True
                docstring_content = []
                # Récupérer le contenu de la docstring
                if line.count('"""') == 2:  # Docstring sur une ligne
                    docstring_content.append(line)
                else:  # Docstring multi-lignes
                    j = i
                    while j < len(lines) and (j == i or '"""' not in lines[j]):
                        docstring_content.append(lines[j])
                        j += 1
                    if j < len(lines):
                        docstring_content.append(lines[j])

                docstring_text = "\n".join(docstring_content).lower()

                # Vérifier le contenu
                assert "streamlit" in docstring_text or "page" in docstring_text or "user story" in docstring_text
                break

        assert docstring_found, "Aucune docstring trouvée dans le module"

    def test_class_has_comprehensive_docstring(self):
        """Vérifie que la classe a une docstring complète."""
        doc = IngredientsClusteringPage.__doc__

        assert doc is not None
        assert len(doc) > 50

        # Devrait mentionner le but de la classe
        doc_lower = doc.lower()
        assert any(word in doc_lower for word in ["clustering", "ingrédient", "analyse"])

    def test_all_public_methods_documented(self):
        """Vérifie que toutes les méthodes publiques ont des docstrings."""
        page = IngredientsClusteringPage()

        public_methods = [name for name in dir(page) if callable(getattr(page, name)) and not name.startswith("_")]

        for method_name in public_methods:
            method = getattr(page, method_name)
            assert method.__doc__ is not None, f"La méthode {method_name} n'a pas de docstring"
            assert len(method.__doc__.strip()) > 20, f"La docstring de {method_name} est trop courte"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

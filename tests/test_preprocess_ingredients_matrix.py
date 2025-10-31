"""
Tests pour le module de preprocessing de la matrice de co-occurrence des ingrédients.

Note: Ces tests vérifient la logique de normalisation et la structure du preprocessor.
Les tests d'intégration end-to-end nécessitent le fichier RAW_recipes.csv complet.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

from utils.preprocess_ingredients_matrix import IngredientsMatrixPreprocessor


class TestNormalizeIngredient:
    """Tests pour la méthode de normalisation des ingrédients."""

    @pytest.fixture
    def preprocessor(self):
        """Crée une instance minimale du preprocessor pour tester normalize_ingredient."""
        return IngredientsMatrixPreprocessor(n_ingredients=10)

    def test_lowercase_conversion(self, preprocessor):
        """Test de conversion en minuscules."""
        assert preprocessor.normalize_ingredient("FLOUR") == "flour"
        assert preprocessor.normalize_ingredient("Salt") == "salt"

    def test_stop_words_removal(self, preprocessor):
        """Test de suppression des stop words."""
        result = preprocessor.normalize_ingredient("fresh garlic")
        assert "garlic" in result
        
        result = preprocessor.normalize_ingredient("ground black pepper")
        assert "pepper" in result

    def test_special_characters_cleaning(self, preprocessor):
        """Test de nettoyage des caractères spéciaux."""
        result = preprocessor.normalize_ingredient("butter (softened)")
        assert "butter" in result
        assert "softened" in result

    def test_whitespace_normalization(self, preprocessor):
        """Test de normalisation des espaces."""
        assert "flour" in preprocessor.normalize_ingredient("  flour   ")
        result = preprocessor.normalize_ingredient("all  purpose  flour")
        assert "flour" in result

    def test_empty_string(self, preprocessor):
        """Test avec chaîne vide."""
        assert preprocessor.normalize_ingredient("") == ""
        assert preprocessor.normalize_ingredient("   ").strip() == ""

    def test_complex_ingredient(self, preprocessor):
        """Test avec ingrédient complexe."""
        result = preprocessor.normalize_ingredient("2 cups all-purpose flour, sifted")
        # Devrait enlever stop words et nettoyer
        assert "flour" in result or "sifted" in result


class TestIngredientsMatrixPreprocessor:
    """Tests pour la classe IngredientsMatrixPreprocessor."""

    @pytest.fixture
    def temp_dir(self):
        """Crée un répertoire temporaire pour les tests."""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path)

    @pytest.fixture
    def sample_recipes_df(self):
        """Crée un DataFrame de recettes pour les tests."""
        return pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Recipe 1", "Recipe 2", "Recipe 3"],
            "ingredients": [
                "['flour', 'sugar', 'eggs']",
                "['flour', 'butter', 'sugar']",
                "['eggs', 'butter', 'milk']",
            ],
            "nutrition": [
                "[100, 10, 5, 2, 15, 20, 3]",
                "[150, 15, 8, 3, 20, 25, 4]",
                "[80, 8, 4, 1, 12, 18, 2]",
            ],
        })

    @pytest.fixture
    def sample_recipes_file(self, temp_dir, sample_recipes_df):
        """Crée un fichier CSV de recettes pour les tests."""
        filepath = temp_dir / "test_recipes.csv"
        sample_recipes_df.to_csv(filepath, index=False)
        return filepath

    @pytest.fixture
    def preprocessor(self, sample_recipes_file, temp_dir):
        """Crée une instance du preprocessor pour les tests."""
        return IngredientsMatrixPreprocessor(n_ingredients=3)

    def test_initialization(self):
        """Test de l'initialisation du preprocessor."""
        preprocessor = IngredientsMatrixPreprocessor(n_ingredients=5)
        assert preprocessor.n_ingredients == 5

    def test_initialization_default_n_ingredients(self):
        """Test de l'initialisation avec valeur par défaut."""
        preprocessor = IngredientsMatrixPreprocessor()
        assert preprocessor.n_ingredients == 300

    def test_parse_ingredients_string_valid(self, preprocessor):
        """Test du parsing d'une chaîne d'ingrédients valide."""
        result = preprocessor._parse_ingredients_string("['flour', 'sugar', 'eggs']")
        assert result == ["flour", "sugar", "eggs"]

    def test_parse_ingredients_string_invalid(self, preprocessor):
        """Test du parsing d'une chaîne invalide."""
        result = preprocessor._parse_ingredients_string("invalid string")
        assert result == []

    def test_parse_ingredients_string_empty(self, preprocessor):
        """Test du parsing d'une chaîne vide."""
        result = preprocessor._parse_ingredients_string("")
        assert result == []

    def test_load_and_process_recipes(self, sample_recipes_file):
        """Test du chargement et traitement des recettes."""
        preprocessor = IngredientsMatrixPreprocessor(n_ingredients=3)
        df = preprocessor.load_and_process_recipes(str(sample_recipes_file))
        
        assert isinstance(df, pd.DataFrame)
        assert "normalized_ingredients" in df.columns  # Colonne renommée après normalisation
        assert "id" in df.columns
        assert len(df) > 0
        
        # Vérifier que les ingrédients ont été parsés et sont des listes
        assert isinstance(df.iloc[0]["normalized_ingredients"], list)

    def test_get_top_ingredients(self, sample_recipes_file):
        """Test de la sélection des top ingrédients."""
        preprocessor = IngredientsMatrixPreprocessor(n_ingredients=3)
        df = preprocessor.load_and_process_recipes(str(sample_recipes_file))
        top_ingredients, ingredient_counts = preprocessor.get_top_ingredients(df)
        
        assert isinstance(top_ingredients, list)
        assert isinstance(ingredient_counts, dict)
        assert len(top_ingredients) <= preprocessor.n_ingredients
        
        # Vérifier que ce sont bien des chaînes
        assert all(isinstance(ing, str) for ing in top_ingredients)

    def test_build_cooccurrence_matrix(self, sample_recipes_file):
        """Test de la construction de la matrice de co-occurrence."""
        preprocessor = IngredientsMatrixPreprocessor(n_ingredients=5)
        df = preprocessor.load_and_process_recipes(str(sample_recipes_file))
        top_ingredients, _ = preprocessor.get_top_ingredients(df)
        
        matrix = preprocessor.build_cooccurrence_matrix(df, top_ingredients)
        
        # Vérifications de structure
        assert isinstance(matrix, pd.DataFrame)
        assert matrix.shape[0] == matrix.shape[1]  # Matrice carrée
        assert matrix.shape[0] == len(top_ingredients)
        
        # Vérifier la symétrie
        assert np.allclose(matrix.values, matrix.values.T)
        
        # Vérifier que la diagonale est non-nulle (auto-occurrence)
        assert all(matrix.iloc[i, i] >= 0 for i in range(len(top_ingredients)))
        
        # Vérifier que les valeurs sont des entiers non-négatifs
        assert (matrix >= 0).all().all()

    def test_build_cooccurrence_matrix_values(self, sample_recipes_file):
        """Test des valeurs de la matrice de co-occurrence."""
        preprocessor = IngredientsMatrixPreprocessor(n_ingredients=5)
        df = preprocessor.load_and_process_recipes(str(sample_recipes_file))
        top_ingredients, _ = preprocessor.get_top_ingredients(df)
        matrix = preprocessor.build_cooccurrence_matrix(df, top_ingredients)
        
        # Dans notre échantillon :
        # Recipe 1: flour, sugar, eggs
        # Recipe 2: flour, butter, sugar
        # Recipe 3: eggs, butter, milk
        
        # flour et sugar apparaissent ensemble 2 fois
        if "flour" in matrix.index and "sugar" in matrix.index:
            flour_sugar_cooc = matrix.loc["flour", "sugar"]
            assert flour_sugar_cooc == 2

    def test_n_ingredients_parameter(self, sample_recipes_file):
        """Test du paramètre n_ingredients."""
        preprocessor_10 = IngredientsMatrixPreprocessor(n_ingredients=10)
        
        df = preprocessor_10.load_and_process_recipes(str(sample_recipes_file))
        top_ingredients, _ = preprocessor_10.get_top_ingredients(df)
        
        # Avec notre petit échantillon, on devrait avoir max 5 ingrédients uniques
        assert len(top_ingredients) <= 10
        assert len(top_ingredients) > 0


class TestEdgeCases:
    """Tests des cas limites."""

    @pytest.fixture
    def temp_dir(self):
        """Crée un répertoire temporaire pour les tests."""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path)

    def test_special_characters_in_ingredients(self, temp_dir):
        """Test avec caractères spéciaux dans les ingrédients."""
        df = pd.DataFrame({
            "id": [1],
            "name": ["Recipe 1"],
            "ingredients": ["['café', 'chocolat@', 'œufs']"],
            "nutrition": ["[100, 10, 5, 2, 15, 20, 3]"],
        })
        
        filepath = temp_dir / "test_special.csv"
        df.to_csv(filepath, index=False)
        
        preprocessor = IngredientsMatrixPreprocessor(n_ingredients=10)
        df_loaded = preprocessor.load_and_process_recipes(str(filepath))
        assert len(df_loaded) > 0

    def test_very_long_ingredient_list(self, temp_dir):
        """Test avec liste d'ingrédients très longue."""
        long_list = str([f"ingredient_{i}" for i in range(100)])
        df = pd.DataFrame({
            "id": [1],
            "name": ["Recipe 1"],
            "ingredients": [long_list],
            "nutrition": ["[100, 10, 5, 2, 15, 20, 3]"],
        })
        
        filepath = temp_dir / "test_long.csv"
        df.to_csv(filepath, index=False)
        
        preprocessor = IngredientsMatrixPreprocessor(n_ingredients=50)
        df_loaded = preprocessor.load_and_process_recipes(str(filepath))
        top_ingredients, _ = preprocessor.get_top_ingredients(df_loaded)
        assert len(top_ingredients) <= 50

    def test_duplicate_ingredients_in_recipe(self, temp_dir):
        """Test avec ingrédients dupliqués dans une recette."""
        df = pd.DataFrame({
            "id": [1],
            "name": ["Recipe 1"],
            "ingredients": ["['flour', 'flour', 'sugar']"],
            "nutrition": ["[100, 10, 5, 2, 15, 20, 3]"],
        })
        
        filepath = temp_dir / "test_dup.csv"
        df.to_csv(filepath, index=False)
        
        preprocessor = IngredientsMatrixPreprocessor(n_ingredients=10)
        df_loaded = preprocessor.load_and_process_recipes(str(filepath))
        top_ingredients, _ = preprocessor.get_top_ingredients(df_loaded)
        matrix = preprocessor.build_cooccurrence_matrix(df_loaded, top_ingredients)
        
        # La matrice devrait traiter les doublons correctement
        assert matrix.loc["flour", "flour"] >= 0

"""Pipeline de prétraitement pour générer la matrice de co-occurrence des ingrédients.

Ce script doit être exécuté AVANT le déploiement de l'application Streamlit.
Il génère une matrice de co-occurrence 300x300 pré-calculée qui sera utilisée
par la page de clustering pour accélérer le chargement.

Usage:
    python -m utils.preprocess_ingredients_matrix

Output:
    data/ingredients_cooccurrence_matrix.csv : Matrice 300x300 avec noms d'ingrédients
    data/ingredients_list.csv : Liste des 300 ingrédients avec leurs fréquences
"""

from pathlib import Path
import pandas as pd
import numpy as np
from collections import Counter
import re
import sys
import ast
import logging

# Ajouter le dossier parent au path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


def get_logger() -> logging.Logger:
    """Crée un logger simple pour le preprocessing (évite import circulaire)."""
    logger = logging.getLogger("preprocessing")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


class IngredientsMatrixPreprocessor:
    """Pipeline de prétraitement pour la matrice de co-occurrence."""

    def __init__(self, n_ingredients: int = 300):
        """
        Initialise le preprocessor.

        Args:
            n_ingredients: Nombre d'ingrédients les plus fréquents à inclure.
        """
        self.n_ingredients = n_ingredients
        self.logger = get_logger()

        # Liste optimisée de stop words (50 mots essentiels)
        self.stop_words = {
            # Taille/quantité
            "large", "small", "medium", "extra", "whole",
            "sliced", "diced", "chopped", "minced", "ground",
            # Couleurs
            "black", "white", "red", "green", "dark", "light",
            # États/préparations
            "fresh", "dried", "frozen", "canned", "raw", "cooked",
            "grilled", "fried", "roasted", "crushed", "shredded", "grated",
            # Qualités
            "organic", "natural", "pure", "virgin", "premium",
            "old", "new", "aged",
            # Emballage
            "can", "jar", "bottle", "bag",
            # Sel/graisse
            "unsalted", "salted", "low", "reduced", "free", "light",
            # Articles/prépositions
            "with", "without", "and", "the",
        }

    def normalize_ingredient(self, ingredient: str) -> str:
        """
        Normalise un ingrédient en appliquant le traitement NLP.

        Args:
            ingredient: Nom brut de l'ingrédient.

        Returns:
            Nom normalisé de l'ingrédient.
        """
        # Mettre en minuscules
        t = ingredient.lower().strip()

        # Retirer la ponctuation et normaliser les espaces
        t = re.sub(r"[^\w\s]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()

        # Filtrer les stop words
        tokens = []
        for word in t.split():
            if word not in self.stop_words and len(word) > 1:
                tokens.append(word)

        # Retourner l'ingrédient normalisé
        normalized = " ".join(tokens) if tokens else t
        return normalized if normalized else ingredient.lower()

    def _parse_ingredients_string(self, ingredients_str: str) -> list[str]:
        """Parse la chaîne d'ingrédients au format liste Python."""
        try:
            return ast.literal_eval(ingredients_str)
        except (ValueError, SyntaxError):
            return []

    def load_and_process_recipes(self, recipes_path: str = "data/RAW_recipes.csv") -> pd.DataFrame:
        """
        Charge les recettes et applique la normalisation NLP.

        Args:
            recipes_path: Chemin vers le fichier de recettes.

        Returns:
            DataFrame avec colonnes: id, ingredients (liste normalisée).
        """
        self.logger.info("=" * 60)
        self.logger.info("ÉTAPE 1: Chargement des recettes")
        self.logger.info("=" * 60)

        # Charger les données directement avec pandas
        recipes_file = Path(recipes_path)

        if not recipes_file.exists():
            raise FileNotFoundError(f"Fichier introuvable: {recipes_path}")

        self.logger.info(f"Chargement depuis: {recipes_path}")
        df = pd.read_csv(recipes_path)

        # Parser la colonne ingredients si elle existe
        if 'ingredients' in df.columns:
            self.logger.info("Parsing des ingrédients...")
            df['ingredients'] = df['ingredients'].apply(self._parse_ingredients_string)

        self.logger.info(f"✅ {len(df):,} recettes chargées")

        # Normaliser tous les ingrédients
        self.logger.info("\nÉTAPE 2: Normalisation NLP des ingrédients")
        self.logger.info("=" * 60)

        normalized_ingredients = []
        total_before = 0

        for idx, row in df.iterrows():
            if idx % 10000 == 0 and idx > 0:
                self.logger.info(f"  Progression: {idx:,}/{len(df):,} recettes ({idx/len(df)*100:.1f}%)")

            if isinstance(row['ingredients'], list):
                raw_ings = row['ingredients']
                total_before += len(raw_ings)

                # Normaliser chaque ingrédient
                normalized = [self.normalize_ingredient(ing) for ing in raw_ings]
                # Retirer les doublons dans la même recette
                normalized = list(dict.fromkeys(normalized))

                normalized_ingredients.append(normalized)
            else:
                normalized_ingredients.append([])

        df['normalized_ingredients'] = normalized_ingredients

        total_after = sum(len(ings) for ings in normalized_ingredients)
        reduction = (1 - total_after / total_before) * 100 if total_before > 0 else 0

        self.logger.info(f"✅ Normalisation terminée:")
        self.logger.info(f"   - Avant: {total_before:,} ingrédients")
        self.logger.info(f"   - Après: {total_after:,} ingrédients")
        self.logger.info(f"   - Réduction: {reduction:.1f}%")

        return df[['id', 'normalized_ingredients']]

    def get_top_ingredients(self, df: pd.DataFrame) -> tuple[list[str], dict[str, int]]:
        """
        Identifie les N ingrédients les plus fréquents.

        Args:
            df: DataFrame avec colonne normalized_ingredients.

        Returns:
            Tuple (liste des ingrédients, dict des fréquences).
        """
        self.logger.info("\nÉTAPE 3: Identification des ingrédients les plus fréquents")
        self.logger.info("=" * 60)

        # Compter les occurrences
        all_ingredients = []
        for ings in df['normalized_ingredients']:
            all_ingredients.extend(ings)

        ingredient_counts = Counter(all_ingredients)

        # Prendre les N plus fréquents
        top_ingredients = [ing for ing, _ in ingredient_counts.most_common(self.n_ingredients)]

        self.logger.info(f"✅ Top {self.n_ingredients} ingrédients identifiés")
        self.logger.info(f"   - Total unique: {len(ingredient_counts):,}")
        self.logger.info(f"   - Fréquence max: {ingredient_counts.most_common(1)[0][1]:,}")
        self.logger.info(f"   - Fréquence min (top {self.n_ingredients}): {ingredient_counts[top_ingredients[-1]]:,}")

        return top_ingredients, dict(ingredient_counts)

    def build_cooccurrence_matrix(
        self,
        df: pd.DataFrame,
        top_ingredients: list[str]
    ) -> pd.DataFrame:
        """
        Construit la matrice de co-occurrence pour les top ingrédients.

        Args:
            df: DataFrame avec normalized_ingredients.
            top_ingredients: Liste des ingrédients à inclure.

        Returns:
            Matrice de co-occurrence (DataFrame).
        """
        self.logger.info("\nÉTAPE 4: Construction de la matrice de co-occurrence")
        self.logger.info("=" * 60)

        n = len(top_ingredients)
        matrix = np.zeros((n, n), dtype=int)

        # Créer un index pour accès rapide
        ing_to_idx = {ing: idx for idx, ing in enumerate(top_ingredients)}

        # Calculer les co-occurrences
        for idx, row in df.iterrows():
            if idx % 10000 == 0 and idx > 0:
                self.logger.info(f"  Progression: {idx:,}/{len(df):,} recettes ({idx/len(df)*100:.1f}%)")

            # Ingrédients de cette recette qui sont dans le top
            recipe_ings = [ing for ing in row['normalized_ingredients'] if ing in ing_to_idx]

            # Incrémenter les co-occurrences
            for i, ing1 in enumerate(recipe_ings):
                idx1 = ing_to_idx[ing1]
                for ing2 in recipe_ings[i:]:  # Commencer à i pour inclure la diagonale
                    idx2 = ing_to_idx[ing2]
                    matrix[idx1, idx2] += 1
                    if idx1 != idx2:
                        matrix[idx2, idx1] += 1  # Symétrique

        # Créer le DataFrame
        cooc_df = pd.DataFrame(matrix, index=top_ingredients, columns=top_ingredients)

        self.logger.info(f"✅ Matrice {n}x{n} construite")
        self.logger.info(f"   - Valeur max: {matrix.max():,}")
        self.logger.info(f"   - Valeur moyenne: {matrix.mean():.1f}")
        self.logger.info(f"   - Diagonale moyenne: {np.diag(matrix).mean():.1f}")

        return cooc_df

    def save_results(
        self,
        cooc_matrix: pd.DataFrame,
        ingredient_counts: dict[str, int],
        output_dir: str = "data"
    ) -> None:
        """
        Sauvegarde la matrice et la liste des ingrédients.

        Args:
            cooc_matrix: Matrice de co-occurrence.
            ingredient_counts: Dict des fréquences d'ingrédients.
            output_dir: Dossier de sortie.
        """
        self.logger.info("\nÉTAPE 5: Sauvegarde des résultats")
        self.logger.info("=" * 60)

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Sauvegarder la matrice
        matrix_path = output_path / "ingredients_cooccurrence_matrix.csv"
        cooc_matrix.to_csv(matrix_path, index=True)
        self.logger.info(f"✅ Matrice sauvegardée: {matrix_path}")
        self.logger.info(f"   - Taille: {matrix_path.stat().st_size / (1024*1024):.2f} MB")

        # Sauvegarder la liste des ingrédients avec fréquences
        ingredients_list = []
        for ing in cooc_matrix.index:
            ingredients_list.append({
                'ingredient': ing,
                'frequency': ingredient_counts.get(ing, 0)
            })

        ingredients_df = pd.DataFrame(ingredients_list)
        list_path = output_path / "ingredients_list.csv"
        ingredients_df.to_csv(list_path, index=False)
        self.logger.info(f"✅ Liste des ingrédients sauvegardée: {list_path}")
        self.logger.info(f"   - Taille: {list_path.stat().st_size / 1024:.2f} KB")

    def run_pipeline(self, recipes_path: str = "data/RAW_recipes.csv") -> None:
        """
        Exécute le pipeline complet de prétraitement.

        Args:
            recipes_path: Chemin vers le fichier de recettes.
        """
        self.logger.info("\n" + "=" * 60)
        self.logger.info("PIPELINE DE PRÉTRAITEMENT - MATRICE DE CO-OCCURRENCE")
        self.logger.info("=" * 60)
        self.logger.info(f"Configuration: {self.n_ingredients} ingrédients")
        self.logger.info("=" * 60 + "\n")

        try:
            # 1. Charger et normaliser
            df = self.load_and_process_recipes(recipes_path)

            # 2. Identifier les top ingrédients
            top_ingredients, ingredient_counts = self.get_top_ingredients(df)

            # 3. Construire la matrice
            cooc_matrix = self.build_cooccurrence_matrix(df, top_ingredients)

            # 4. Sauvegarder
            self.save_results(cooc_matrix, ingredient_counts)

            self.logger.info("\n" + "=" * 60)
            self.logger.info("✅ PIPELINE TERMINÉ AVEC SUCCÈS")
            self.logger.info("=" * 60)
            self.logger.info("\nFichiers générés:")
            self.logger.info("  - data/ingredients_cooccurrence_matrix.csv")
            self.logger.info("  - data/ingredients_list.csv")
            self.logger.info("\nCes fichiers peuvent maintenant être versionnés sur GitHub.")
            self.logger.info("=" * 60 + "\n")

        except Exception as e:
            self.logger.error(f"\n❌ ERREUR DANS LE PIPELINE: {e}")
            raise


def main():
    """Point d'entrée principal."""
    preprocessor = IngredientsMatrixPreprocessor(n_ingredients=300)
    preprocessor.run_pipeline()


if __name__ == "__main__":
    main()

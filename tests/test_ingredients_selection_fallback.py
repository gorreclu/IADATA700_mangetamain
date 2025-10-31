import pandas as pd
from src.components.ingredients_clustering_page import IngredientsClusteringPage

def test_select_top_ingredients_fallback_no_intersection():
    # Construire matrice factice 5x5
    ingredients = ["salt", "butter", "pepper", "onion", "sugar"]
    data = {
        ing: [10, 2, 3, 4, 5] for ing in ingredients
    }
    df_matrix = pd.DataFrame(data, index=ingredients)

    # Construire liste d'ingrédients sans intersection volontaire
    df_list = pd.DataFrame({
        "ingredient": ["x", "y", "z"],
        "frequency": [100, 50, 25]
    })

    page = IngredientsClusteringPage()

    sub_matrix, selected = page._select_top_ingredients(df_matrix, df_list, 3)

    # Fallback doit sélectionner les 3 premiers de la matrice originale
    assert selected == ingredients[:3]
    assert sub_matrix.shape == (3, 3)
    assert set(sub_matrix.index) == set(selected)
    assert set(sub_matrix.columns) == set(selected)

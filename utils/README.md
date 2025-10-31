# Prétraitement de la matrice de co-occurrence

## 📋 Objectif

Ce script génère une matrice de co-occurrence 300x300 précalculée pour optimiser les performances de l'application Streamlit.

## 🚀 Exécution

### Prérequis
- Python 3.11+
- Packages: pandas, numpy
- Fichier `data/RAW_recipes.csv` présent

### Commande
```bash
# Avec uv (recommandé)
uv run python -m utils.preprocess_ingredients_matrix

# Avec python classique
python -m utils.preprocess_ingredients_matrix
```

## 📊 Résultats générés

Le script génère 2 fichiers dans `data/`:

1. **`ingredients_cooccurrence_matrix.csv`** (≈15-20 MB)
   - Matrice 300x300 des co-occurrences
   - Index/colonnes = noms d'ingrédients normalisés
   - Valeurs = nombre de recettes où les ingrédients apparaissent ensemble

2. **`ingredients_list.csv`** (≈10 KB)
   - Liste des 300 ingrédients
   - Colonnes: `ingredient`, `frequency`
   - Triée par fréquence décroissante

## 🔄 Pipeline de traitement

```
RAW_recipes.csv (230k recettes)
        ↓
    Normalisation NLP (50 stop words)
        ↓
    Comptage des ingrédients
        ↓
    Sélection Top 300
        ↓
    Calcul co-occurrences
        ↓
  Matrice 300x300 + Liste
```

## ⏱️ Temps d'exécution

- **Dataset complet** (~230k recettes): ~5-10 minutes
- **Mémoire requise**: ~2-4 GB RAM

## 📝 Logs

Les logs détaillés sont affichés dans la console et sauvegardés dans:
- `debug/debug.log`
- `debug/errors.log`

## 🔍 Vérification

Après exécution, vérifiez:
```bash
ls -lh data/ingredients_*
```

Vous devriez voir:
```
ingredients_cooccurrence_matrix.csv  (~15-20 MB)
ingredients_list.csv                 (~10 KB)
```

## ✅ Validation

Le script affiche:
- ✅ Nombre de recettes traitées
- ✅ Réduction après normalisation NLP
- ✅ Top 300 ingrédients identifiés
- ✅ Matrice construite (taille, valeurs min/max/moyenne)
- ✅ Fichiers sauvegardés

## 🔄 Réexécution

Pour regénérer la matrice (si données modifiées):
```bash
# Supprimer les anciens fichiers
rm data/ingredients_cooccurrence_matrix.csv data/ingredients_list.csv

# Relancer le preprocessing
uv run python -m utils.preprocess_ingredients_matrix
```

## 📦 Git LFS (optionnel)

Si vous versionnez les fichiers CSV volumineux:
```bash
# Installer Git LFS
brew install git-lfs
git lfs install

# Tracker les gros CSV
git lfs track "data/ingredients_cooccurrence_matrix.csv"
git add .gitattributes
git add data/ingredients_cooccurrence_matrix.csv
git commit -m "Add precomputed cooccurrence matrix"
```

## 🚨 Troubleshooting

### Erreur: "FileNotFoundError: data/RAW_recipes.csv"
**Solution**: Téléchargez d'abord les données
```bash
python download_data.py
```

### Erreur: "MemoryError"
**Solution**: Réduire `n_ingredients` dans le script (ligne 341)
```python
preprocessor = IngredientsMatrixPreprocessor(n_ingredients=200)  # Au lieu de 300
```

### Erreur: "ModuleNotFoundError"
**Solution**: Installer les dépendances
```bash
uv sync
```

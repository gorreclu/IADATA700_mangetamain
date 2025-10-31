#!/bin/bash
# Script de test complet pour la matrice précalculée

set -e  # Stop on error

echo "=========================================="
echo "🚀 TEST MATRICE PRÉCALCULÉE"
echo "=========================================="
echo ""

# Vérifier qu'on est dans le bon dossier
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Erreur: Exécutez ce script depuis la racine du projet"
    exit 1
fi

echo "📂 Dossier de travail: $(pwd)"
echo ""

# Étape 1 : Vérifier les données sources
echo "=========================================="
echo "ÉTAPE 1: Vérification des données sources"
echo "=========================================="

if [ ! -f "data/RAW_recipes.csv" ]; then
    echo "⚠️  Fichier RAW_recipes.csv manquant"
    echo "📥 Téléchargement depuis S3..."
    uv run python download_data.py
else
    echo "✅ data/RAW_recipes.csv trouvé"
fi

echo ""

# Étape 2 : Générer la matrice
echo "=========================================="
echo "ÉTAPE 2: Génération de la matrice 300x300"
echo "=========================================="
echo "⏱️  Temps estimé: 5-10 minutes"
echo ""

uv run python -m utils.preprocess_ingredients_matrix

echo ""

# Étape 3 : Vérifier les fichiers générés
echo "=========================================="
echo "ÉTAPE 3: Vérification des fichiers"
echo "=========================================="

if [ -f "data/ingredients_cooccurrence_matrix.csv" ]; then
    SIZE=$(ls -lh "data/ingredients_cooccurrence_matrix.csv" | awk '{print $5}')
    echo "✅ Matrice générée: $SIZE"
else
    echo "❌ Erreur: Matrice non trouvée"
    exit 1
fi

if [ -f "data/ingredients_list.csv" ]; then
    SIZE=$(ls -lh "data/ingredients_list.csv" | awk '{print $5}')
    LINES=$(wc -l < "data/ingredients_list.csv")
    echo "✅ Liste générée: $SIZE ($LINES lignes)"
else
    echo "❌ Erreur: Liste non trouvée"
    exit 1
fi

echo ""

# Étape 4 : Aperçu des fichiers
echo "=========================================="
echo "ÉTAPE 4: Aperçu des données"
echo "=========================================="

echo ""
echo "📋 Top 10 ingrédients:"
head -11 "data/ingredients_list.csv" | tail -10

echo ""
echo "📊 Première ligne de la matrice:"
head -2 "data/ingredients_cooccurrence_matrix.csv" | tail -1 | cut -d',' -f1-5

echo ""

# Étape 5 : Instructions pour lancer l'app
echo "=========================================="
echo "✅ PREPROCESSING TERMINÉ AVEC SUCCÈS"
echo "=========================================="
echo ""
echo "📋 Prochaines étapes:"
echo ""
echo "1. Lancer l'application:"
echo "   uv run python run_app.py"
echo ""
echo "2. Naviguer vers:"
echo "   http://localhost:8501"
echo ""
echo "3. Tester la page:"
echo "   🍳 Clustering des Ingrédients"
echo ""
echo "4. Vérifier:"
echo "   - Chargement instantané (<3 sec)"
echo "   - Message 'Matrice précalculée: 300 ingrédients'"
echo "   - Clustering fonctionnel (40-300 ingrédients)"
echo "   - Visualisation t-SNE interactive"
echo ""
echo "=========================================="
echo "🎉 Prêt pour le test!"
echo "=========================================="

# Mangetamain - Guide de Développement

Application web d'analyse de données culinaires développée avec Streamlit.

**Projet académique** - Telecom Paris - IADATA700 Kit Big Data

## 🚀 Installation Rapide

```bash
# 1. Cloner et installer
git clone https://github.com/gorreclu/IADATA700_mangetamain.git
cd IADATA700_mangetamain
uv sync

# 2. Générer la matrice précalculée (première fois)
uv run python -m utils.preprocess_ingredients_matrix

# 3. Lancer l'application
uv run python scripts/run_app.py
```

## 📋 Pages de l'Application

### 🏠 Home
Exploration générale des datasets avec métriques clés et statistiques descriptives.

### 🍳 Clustering des Ingrédients
- Matrice de co-occurrence 300×300 précalculée
- Clustering K-means (3-20 clusters)
- Visualisation t-SNE 2D interactive
- Sélection dynamique de 40 à 300 ingrédients

### 📊 Analyse de Popularité
- Relations popularité ↔ notes ↔ caractéristiques
- Preprocessing IQR avec détection d'outliers
- Scatter plots interactifs
- Segmentation par percentiles

## 🏗️ Architecture

Voir le [Diagramme de Classes](ClassDiagram.rst) pour l'architecture détaillée.

**Modules principaux :**
- `src/core/` : DataLoader, DataExplorer, InteractionsAnalyzer, CacheManager
- `src/components/` : Pages Streamlit (IngredientsClusteringPage, PopularityAnalysisPage)
- `utils/` : IngredientsMatrixPreprocessor (génération offline de la matrice)
- `scripts/` : Utilitaires de lancement et téléchargement

## ⚡ Optimisations

### Preprocessing Offline
```bash
uv run python -m utils.preprocess_ingredients_matrix
```
Génère la matrice 300×300 en ~5-10 min (une seule fois).

### Système de Cache
- Données d'interactions : cache disque automatique
- Matrice d'ingrédients : versionnée dans git
- Cache Streamlit natif pour chargements optimisés

## 🧪 Tests

```bash
# Tous les tests (124)
uv run pytest

# Avec couverture
uv run pytest --cov=src --cov-report=html
```

## 📖 Documentation Complète

Voir l'[API Reference](api/modules.rst) pour la documentation détaillée de tous les modules.


# 🍳 Mangetamain - Analyse de Données Culinaires

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat&logo=scikit-learn&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat&logo=plotly&logoColor=white)
![Tests](https://img.shields.io/badge/tests-124%20passed-success?style=flat)

**Application web d'analyse de recettes et d'interactions utilisateurs**  
*Projet académique - Telecom Paris - IADATA700 Kit Big Data*

[![Streamlit App](https://img.shields.io/badge/Streamlit-Live%20Demo-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://iadata700mangetamain-uwgeofayxcifcmeisuesrb.streamlit.app/)

[🚀 Installation](#-installation) • [📖 Documentation](#-documentation) • [🧪 Tests](#-tests)

</div>

---

## 📋 À propos

**Mangetamain** est une application web interactive développée avec Streamlit pour analyser un large corpus de recettes de cuisine et leurs interactions utilisateurs. Le projet met en œuvre des techniques avancées de data science et de machine learning pour :

- 🔍 **Explorer** plus de 230 000 recettes et leurs métadonnées
- 🧩 **Analyser** les associations d'ingrédients par clustering et co-occurrence
- 📊 **Visualiser** les relations entre popularité, notes et caractéristiques des recettes
- ⚡ **Optimiser** les performances grâce à un système de preprocessing et de cache

### 🌐 Démo en ligne

L'application est déployée sur **Streamlit Cloud** et accessible publiquement :

**🔗 [https://iadata700mangetamain-uwgeofayxcifcmeisuesrb.streamlit.app/](https://iadata700mangetamain-uwgeofayxcifcmeisuesrb.streamlit.app/)**

> 💡 Essayez l'application directement dans votre navigateur sans installation !

## 🚀 Installation

### Prérequis

- **Python 3.11+**
- **uv** (gestionnaire de paquets) : `pip install uv`

### Installation rapide

```bash
# 1. Cloner le repository
git clone https://github.com/gorreclu/IADATA700_mangetamain.git
cd IADATA700_mangetamain

# 2. Installer les dépendances
uv sync

# 3. Générer la matrice précalculée (première fois uniquement, ~5-10 min)
uv run python -m utils.preprocess_ingredients_matrix

# 4. Lancer l'application
uv run python scripts/run_app.py
```

> 📥 **Téléchargement automatique** : Les données sont automatiquement récupérées depuis S3 si manquantes.

L'application sera accessible sur **http://localhost:8501**

### Commandes utiles

```bash
# Démarrer l'application (avec auto-download des données)
python scripts/run_app.py

# Arrêter l'application
python scripts/stop_app.py
# ou Ctrl+C dans le terminal

# Démarrage direct Streamlit (données déjà présentes)
uv run streamlit run src/app.py

# Télécharger manuellement les données
python scripts/download_data.py
```

## ✨ Fonctionnalités

### 🏠 Page Home - Exploration des données
- Aperçu interactif des datasets (recettes et interactions)
- Métriques clés et statistiques descriptives
- Informations sur les types de données et valeurs manquantes

### 🍳 Clustering des Ingrédients
Analyse des associations d'ingrédients par co-occurrence et clustering :
- **Matrice précalculée** : 300×300 ingrédients sur ~230k recettes
- **Sélection dynamique** : 40 à 300 ingrédients analysables
- **Clustering K-means** : 3 à 20 clusters configurables
- **Visualisation t-SNE** : Projection 2D interactive des groupes
- **Analyse des groupes** : Ingrédients caractéristiques par cluster

> � Voir la section [Preprocessing & Optimisations](#-preprocessing--optimisations) pour les détails du preprocessing de la matrice.

### � Analyse de Popularité
Relations entre popularité, notes et caractéristiques des recettes :
- **Métriques agrégées** : Nombre d'interactions, note moyenne, temps de préparation
- **Scatter plots interactifs** : Popularité vs notes, popularité vs features
- **Segmentation intelligente** : Percentiles (Low/Medium/High/Viral)
- **Filtrage configurable** : Seuil d'interactions minimales
- **Preprocessing IQR** : Détection d'outliers avec seuil ajustable

## 📂 Structure du Projet

```
IADATA700_mangetamain/
├── src/                          # Code source de l'application
│   ├── app.py                   # Point d'entrée Streamlit
│   ├── core/                    # Modules de base
│   │   ├── data_loader.py      # Chargement des données CSV
│   │   ├── data_explorer.py    # Exploration et statistiques
│   │   ├── interactions_analyzer.py  # Analyse popularité/notes
│   │   ├── cache_manager.py    # Système de cache disque
│   │   ├── cacheable_mixin.py  # Mixin pour objets cacheables
│   │   └── logger.py           # Configuration du logging
│   └── components/              # Pages Streamlit
│       ├── ingredients_clustering_page.py
│       └── popularity_analysis_page.py
├── utils/                       # Utilitaires de preprocessing
│   └── preprocess_ingredients_matrix.py
├── scripts/                     # Scripts d'exécution
│   ├── run_app.py              # Lancement de l'app
│   ├── stop_app.py             # Arrêt de l'app
│   ├── download_data.py        # Téléchargement des données
│   └── test_preprocessing.sh   # Test du preprocessing
├── tests/                       # Suite de tests (124 tests)
├── docs/                        # Documentation Sphinx + diagrammes
├── data/                        # Données (non versionnées sauf matrices)
├── cache/                       # Cache de calculs (temporaire)
└── debug/                       # Logs de debug
```

## 🏗️ Architecture

![Architecture UML](docs/class-diagram.svg)

**Modules principaux** :
- **Core** : DataLoader, DataExplorer, InteractionsAnalyzer, CacheManager, Logger
- **Components** : IngredientsClusteringPage, PopularityAnalysisPage
- **Utils** : IngredientsMatrixPreprocessor

```bash
# Générer le diagramme
plantuml -tsvg docs/class-diagram.puml
```

## ⚡ Preprocessing & Optimisations

### 🍳 Matrice d'ingrédients (Offline)

Génération d'une matrice de co-occurrence 300×300 pour accélérer le clustering.

```bash
# Exécution (première fois uniquement, ~5-10 min)
uv run python -m utils.preprocess_ingredients_matrix
```

**Pipeline** : Normalisation NLP → Top 300 ingrédients → Matrice de co-occurrence → Export CSV

**Fichiers générés** :
- `data/ingredients_cooccurrence_matrix.csv` (259 KB)
- `data/ingredients_list.csv` (5 KB)

> � Voir `utils/preprocess_ingredients_matrix.py` pour plus de détails

---

### 📊 Preprocessing d'interactions (Runtime)

Nettoyage automatique des données pour l'analyse de popularité avec détection d'outliers par méthode **IQR** (seuil × 5.0).

**Pipeline** : Fusion interactions ↔ recettes → Détection outliers (IQR) → Cache

**Fichiers cache** :
- `data/merged_interactions_recipes_optimized.csv`
- `data/aggregated_popularity_metrics_optimized.csv`

**Configuration** : Interface disponible dans la page "Analyse de Popularité" (méthode IQR/Z-score, seuil ajustable)

> 📝 Voir `src/core/interactions_analyzer.py` (classe `PreprocessingConfig`)

---

**⚡ Impact** : Temps de chargement divisé par ~10-20× grâce au preprocessing + cache

## 🧪 Tests

**124 tests** couvrant tous les modules (core, components, utils, intégration)

```bash
# Tous les tests
uv run pytest

# Avec couverture
uv run pytest --cov=src --cov-report=html

# Tests spécifiques
uv run pytest tests/test_ingredients_clustering_page.py

# Linting PEP8
uv run flake8 src/ tests/
```

## 📖 Documentation

### Sphinx

```bash
cd docs && uv run make html
open build/html/index.html
```

### Logging

| Fichier | Contenu |
|---------|---------|
| `debug/debug.log` | Logs détaillés (INFO/DEBUG) |
| `debug/errors.log` | Erreurs uniquement |

## 🛠️ Technologies

| Catégorie | Technologies |
|-----------|-------------|
| **Backend** | Python 3.11+, Pandas, NumPy |
| **Frontend** | Streamlit |
| **ML/Analytics** | scikit-learn (K-means, t-SNE), NLTK |
| **Visualisation** | Plotly, Matplotlib |
| **Tests** | pytest, pytest-cov |
| **Documentation** | Sphinx, PlantUML |
| **Gestion de paquets** | uv |

## 🤝 Contribution

Ce projet est développé dans un cadre académique.

Sara EL MOUNTASSER, Cyprien CHARLATÉ, William ROOSE, Lucas GORREC

Telecom Paris - MS Big Data Expert ML OPS - Promotion IADATA700 2025-2026

---

<div align="center">

**[⬆ Retour en haut](#-mangetamain---analyse-de-données-culinaires)**

</div>




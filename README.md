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

### Diagramme de classes

![Architecture UML](docs/class-diagram.svg)

<details>
<summary>📋 <b>Description de l'architecture</b></summary>

#### Core Modules
- **DataLoader** : Chargement et validation des fichiers CSV
- **DataExplorer** : Statistiques descriptives et exploration
- **InteractionsAnalyzer** : Calculs d'agrégations popularité/notes (avec cache)
- **CacheManager** : Gestion centralisée du cache disque
- **Logger** : Système de logging structuré

#### Components (Pages Streamlit)
- **IngredientsClusteringPage** : Interface de clustering d'ingrédients
- **PopularityAnalysisPage** : Interface d'analyse de popularité

#### Utils
- **IngredientsMatrixPreprocessor** : Génération offline de la matrice de co-occurrence

</details>

**Générer le diagramme :**
```bash
brew install plantuml                     # Installation (macOS)
plantuml -tsvg docs/class-diagram.puml   # Génération SVG
```


<details>
<summary>## ⚡ Preprocessing - Optimisation des Performances</summary>

### Matrice de co-occurrence précalculée

Pour accélérer l'analyse de clustering, le projet utilise un **preprocessing offline** qui génère une matrice de co-occurrence 300×300 en analysant ~230 000 recettes.

#### 📍 Fichier
`utils/preprocess_ingredients_matrix.py`

#### 🎯 Pipeline de traitement

1. **Chargement** : Import du dataset RAW_recipes.csv
2. **Normalisation NLP** : 
   - Lowercase, suppression de la ponctuation
   - Filtrage de 50+ stop words culinaires
   - Parsing des listes d'ingrédients JSON
3. **Sélection** : Extraction des 300 ingrédients les plus fréquents
4. **Co-occurrence** : Construction de la matrice symétrique 300×300
5. **Export** : Sauvegarde en CSV optimisé

#### 🚀 Exécution

```bash
# Génération de la matrice (requis à la première installation)
uv run python -m utils.preprocess_ingredients_matrix
```

**⏱️ Durée** : ~5-10 minutes (une seule fois)

#### 📊 Fichiers générés

| Fichier | Taille | Description |
|---------|--------|-------------|
| `data/ingredients_cooccurrence_matrix.csv` | ~259 KB | Matrice de co-occurrence 300×300 |
| `data/ingredients_list.csv` | ~5 KB | Liste des 300 ingrédients avec fréquences |

#### 🔄 Quand régénérer ?

- ✅ Première installation du projet
- ✅ Après modification du dataset RAW_recipes.csv
- ✅ Pour changer le nombre d'ingrédients (paramètre `n_ingredients`)

> 💡 **Astuce** : Les fichiers générés sont versionnés dans git pour éviter de régénérer à chaque clone.

</details>


## 🧪 Tests

### Suite de tests complète

Le projet dispose de **124 tests** couvrant tous les modules critiques.

```bash
# Lancer tous les tests
uv run pytest

# Tests avec rapport de couverture
uv run pytest --cov=src --cov-report=html

# Tests d'un module spécifique
uv run pytest tests/test_ingredients_clustering_page.py
uv run pytest tests/test_preprocess_ingredients_matrix.py
uv run pytest tests/test_interactions_analyzer.py

# Mode verbose avec détails
uv run pytest -v --tb=short
```

### Modules testés

- ✅ **Core** : data_loader, data_explorer, interactions_analyzer, logger
- ✅ **Components** : ingredients_clustering_page, popularity_analysis_page
- ✅ **Utils** : preprocess_ingredients_matrix
- ✅ **Integration** : app.py, workflows complets

### Qualité du code

```bash
# Linting PEP8
uv run flake8 src/ tests/

# Vérification des types
uv run mypy src/
```

## 📖 Documentation

### Documentation Sphinx

Une documentation complète de l'API est disponible :

```bash
# Générer la documentation
cd docs
uv run make html

# Ouvrir dans le navigateur
open build/html/index.html
```

**Contenu** :
- 📚 API Reference complète
- 🏗️ Guide d'architecture
- 📝 Guide de contribution
- 🔍 Index des modules et classes

### Logging

Le projet utilise un système de logging structuré :

| Fichier | Niveau | Contenu |
|---------|--------|---------|
| `debug/debug.log` | INFO/DEBUG | Logs détaillés de tous les modules |
| `debug/errors.log` | ERROR/CRITICAL | Erreurs uniquement |

Configuration dans `src/core/logger.py`

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




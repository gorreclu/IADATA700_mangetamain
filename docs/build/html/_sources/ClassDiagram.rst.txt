Architecture du Projet
=======================

Diagramme de Classes
--------------------

Le diagramme suivant illustre l'architecture modulaire de l'application Mangetamain :

.. image:: ClassDiagram.png
   :width: 100%
   :alt: Diagramme de classes de l'application Mangetamain

Composants Principaux
---------------------

**Application Core**
   - `App` : Point d'entrée principal de l'application Streamlit
   - `AppConfig` : Configuration centralisée de l'application

**Modules de Données (Core)**
   - `DataLoader` : Chargement et validation des données CSV
   - `DataExplorer` : Exploration et statistiques des datasets
   - `InteractionsAnalyzer` : Analyse des interactions utilisateur-recettes avec preprocessing IQR

**Interface Utilisateur (Components)**
   - `IngredientsClusteringPage` : Clustering d'ingrédients basé sur matrice de co-occurrence précalculée
   - `PopularityAnalysisPage` : Analyse de popularité avec détection d'outliers

**Système de Cache**
   - `CacheManager` : Gestionnaire centralisé du cache disque
   - `CacheableMixin` : Mixin pour l'intégration du cache dans les analyseurs
   - Note : IngredientsClusteringPage utilise uniquement le cache Streamlit natif

**Preprocessing & Utilitaires**
   - `IngredientsMatrixPreprocessor` : Génération offline de la matrice 300×300
   - `PreprocessingConfig` : Configuration du preprocessing des interactions (IQR/Z-score)
   - `Logger` : Système de logging structuré

**Scripts**
   - `download_data.py` : Téléchargement automatique des données depuis S3
   - `run_app.py` / `stop_app.py` : Gestion du cycle de vie de l'application

Architecture Simplifiée
-----------------------

Cette architecture a été optimisée pour :

- **Performance** : Matrices précalculées + système de cache pour données lourdes
- **Modularité** : Séparation claire entre core, components et utils
- **Maintenabilité** : Suppression des modules inutilisés (IngredientsAnalyzer obsolète)
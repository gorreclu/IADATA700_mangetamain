Tests et Couverture
===================

Le projet dispose d'une suite de tests complète couvrant les modules critiques.

Résumé de la Couverture
-----------------------

.. list-table:: Couverture par Module
   :header-rows: 1
   :widths: 30 15 15 40

   * - Module
     - Couverture
     - Tests
     - Statut
   * - **Modules Core**
     - 
     - 
     - 
   * - ``cache_manager.py``
     - **92%**
     - 18 tests
     - ✅ Excellent
   * - ``cacheable_mixin.py``
     - **97%**
     - 18 tests
     - ✅ Excellent
   * - ``data_loader.py``
     - **100%**
     - 18 tests
     - ✅ Parfait
   * - ``data_explorer.py``
     - **95%**
     - 15 tests
     - ✅ Excellent
   * - ``logger.py``
     - **94%**
     - 11 tests
     - ✅ Excellent
   * - ``interactions_analyzer.py``
     - **61%**
     - 18 tests
     - ⚠️ Bon
   * - **Composants UI**
     - 
     - 
     - 
   * - ``app.py``
     - **63%**
     - Tests intégration
     - ⚠️ Acceptable
   * - ``ingredients_clustering_page.py``
     - **32%**
     - 18 tests
     - ⚠️ UI principalement
   * - ``popularity_analysis_page.py``
     - **22%**
     - 15 tests
     - ⚠️ UI principalement
   * - **Utilitaires**
     - 
     - 
     - 
   * - ``preprocess_ingredients_matrix.py``
     - Tests fonctionnels
     - 19 tests
     - ✅ Testé

**Couverture globale : 49%**

Total : **160 tests** passent avec succès

📊 **Rapport de couverture détaillé** : `Voir le rapport HTML interactif </coverage/index.html>`_

   Le rapport HTML complet est généré automatiquement et déployé avec cette documentation.
   Il permet de visualiser ligne par ligne le code couvert par les tests.

Détails par Module
------------------

Modules Core (Logique Métier)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Les modules ``core/`` contiennent la logique métier critique et sont **excellemment testés** :

**CacheManager (92%)**
   - Tests de sauvegarde/récupération du cache
   - Tests de génération de clés cohérentes
   - Tests de nettoyage du cache (partiel et complet)
   - Tests de gestion d'erreurs (cache corrompu, données invalides)
   - Tests d'informations sur le cache

**CacheableMixin (97%)**
   - Tests d'opérations cachées
   - Tests d'activation/désactivation du cache
   - Tests de cache hit/miss
   - Tests avec plusieurs analyseurs
   - Tests de préservation des types de données

**DataLoader (100%)**
   - Chargement de fichiers CSV
   - Validation des données
   - Préprocessing
   - Gestion d'erreurs

**DataExplorer (95%)**
   - Exploration de datasets
   - Statistiques descriptives
   - Rechargement de données

**Logger (94%)**
   - Configuration multi-handlers
   - Logs structurés (debug, info, warning, error)
   - Fichiers de logs séparés

**InteractionsAnalyzer (61%)**
   - Agrégation des interactions
   - Preprocessing IQR/Z-score
   - Détection d'outliers
   - Création de segments de popularité
   - Catégorisation de recettes

Composants UI (Pages Streamlit)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Les pages Streamlit contiennent beaucoup de code de rendu UI difficile à tester unitairement.

**Note** : Ces pages sont testées **manuellement** via :
   - Application déployée sur Streamlit Cloud
   - Tests d'intégration end-to-end
   - Validation utilisateur

La couverture plus faible est **normale et attendue** pour du code UI.

Exécuter les Tests
------------------

Tests complets
~~~~~~~~~~~~~~

.. code-block:: bash

   # Tous les tests
   uv run pytest

   # Tests avec couverture
   uv run pytest --cov=src --cov-report=html

   # Ouvrir le rapport HTML
   open htmlcov/index.html

Tests spécifiques
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Tests d'un module spécifique
   uv run pytest tests/test_cache_manager.py -v

   # Tests d'une classe spécifique
   uv run pytest tests/test_cache_manager.py::TestCacheManager -v

   # Tests avec affichage des print
   uv run pytest -s

Linting
~~~~~~~

.. code-block:: bash

   # Vérification PEP8
   uv run flake8 src/ tests/

   # Fix automatique
   uv run autopep8 --in-place --recursive src/ tests/

Tests de Preprocessing
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Tests du preprocessing de la matrice d'ingrédients
   uv run pytest tests/test_preprocess_ingredients_matrix.py -v

   # Script de test du preprocessing (avec données réelles)
   bash scripts/test_preprocessing.sh

Intégration Continue
--------------------

Les tests sont exécutés automatiquement via **GitHub Actions** :

- **Workflow** : ``.github/workflows/test-app.yml``
- **Déclenchement** : À chaque push et pull request
- **Environnement** : Python 3.11, Ubuntu latest
- **Durée** : ~3 minutes

Badges
~~~~~~

.. image:: https://img.shields.io/badge/tests-160%20passed-success
   :alt: Tests Status

.. image:: https://img.shields.io/badge/coverage-49%25-yellow
   :alt: Coverage

Amélioration Continue
---------------------

Modules Prioritaires
~~~~~~~~~~~~~~~~~~~~

Les modules **Core** étant déjà excellemment testés (92-100%), les efforts futurs devraient se concentrer sur :

1. **InteractionsAnalyzer** : Améliorer de 61% à 80%
   - Tester les méthodes de preprocessing non couvertes
   - Ajouter des tests pour les cas limites

2. **Pages Streamlit** : Tests d'intégration
   - Mocker Streamlit pour tester la logique métier
   - Tests end-to-end avec Selenium/Playwright

Bonnes Pratiques
~~~~~~~~~~~~~~~~

- ✅ Tous les nouveaux modules Core doivent avoir **>90% de couverture**
- ✅ Les bugs doivent d'abord être reproduits par un test (TDD)
- ✅ Les tests doivent être rapides (<5 secondes pour la suite complète)
- ✅ Utiliser des fixtures pytest pour partager les données de test
- ✅ Mocker les dépendances externes (fichiers, API, etc.)

Références
----------

- `pytest Documentation <https://docs.pytest.org/>`_
- `pytest-cov Documentation <https://pytest-cov.readthedocs.io/>`_
- `Coverage.py <https://coverage.readthedocs.io/>`_

.. Mangetamain documentation master file

Mangetamain - Analyse de Données Culinaires
==============================================

Application web interactive développée avec Streamlit pour analyser un corpus de ~230 000 recettes et leurs interactions utilisateurs.

**Projet académique** - Telecom Paris - MS Big Data Expert ML OPS - IADATA700 Kit Big Data (2025-2026)

**Fonctionnalités principales :**

* 🍳 **Clustering des ingrédients** - Matrice de co-occurrence 300×300 précalculée, K-means et visualisation t-SNE
* � **Analyse de popularité** - Relations entre notes, interactions et caractéristiques avec preprocessing IQR
* 🏠 **Exploration des données** - Statistiques descriptives et métriques clés
* ⚡ **Optimisations avancées** - Preprocessing offline + système de cache pour performances optimales
* 🌐 **Déploiement cloud** - Streamlit Cloud (gratuit, actif) + AWS EC2 testé (désactivé)

**Stack technique :**

* **Frontend** : Streamlit
* **ML/Analytics** : scikit-learn (K-means, t-SNE), NLTK
* **Data** : Pandas, NumPy
* **Visualisation** : Plotly, Matplotlib
* **Tests** : pytest (160 tests, 49% coverage)
* **Docs** : Sphinx, PlantUML

**Accès en ligne :**

* 🌐 **Streamlit Cloud** (actif) : https://iadata700mangetamain-uwgeofayxcifcmeisuesrb.streamlit.app/

*Note : Un déploiement AWS EC2 a été testé puis désactivé pour éviter les coûts. L'architecture reste documentée ci-dessous.*

.. toctree::
   :maxdepth: 2
   :caption: Documentation

   README
   api/modules

.. toctree::
   :maxdepth: 1
   :caption: Architecture

   Architecture AWS <ArchitectureAWS>
   Diagramme de classes <ClassDiagram>

.. toctree::
   :maxdepth: 1
   :caption: Qualité

   Tests
   Rapport de couverture HTML </coverage/index.html>

Indices et tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Architecture AWS
===============

Infrastructure de déploiement de l'application Mangetamain sur Amazon Web Services.

.. image:: Architecture_AWS_Mangetamain.svg
   :width: 100%
   :alt: Architecture AWS de Mangetamain

Vue d'Ensemble
--------------

L'application a été déployée sur **deux environnements** à des fins de **comparaison et tests** :

1. **Streamlit Cloud** (gratuit) : https://iadata700mangetamain-uwgeofayxcifcmeisuesrb.streamlit.app/ ✅ **Actif**
2. **AWS EC2** (infrastructure dédiée) : ~~http://13.37.60.84:8501~~ ❌ **Désactivé** (pour éviter les coûts)

.. note::
   L'infrastructure AWS EC2 a été utilisée pour tester et comparer les performances avec Streamlit Cloud, 
   mais elle n'est **plus active** pour éviter les frais mensuels (~30€/mois). Seul le déploiement 
   **Streamlit Cloud** reste accessible publiquement.

Cette architecture AWS était optimisée pour un usage académique/démonstration, 
privilégiant la simplicité et le contrôle des coûts tout en maintenant des performances acceptables.

**Configuration testée :**

* 🌐 **Accès** : ~~http://13.37.60.84:8501~~ (désactivé)
* 🖥️ **Instance** : EC2 t3.medium (2 vCPU, 4 GB RAM)
* 💰 **Coût** : ~30€/mois (raison de la désactivation)
* 👥 **Capacité** : ~500 utilisateurs concurrents
* ⏸️ **Statut** : Instance arrêtée après phase de tests

Composants Utilisés
-------------------

.. list-table::
   :header-rows: 1
   :widths: 20 25 25 15 15

   * - Composant
     - Description
     - Interaction
     - Coût
     - Statut
   * - 🌐 **Internet**
     - Utilisateurs accédant via navigateur
     - Source des requêtes HTTP/HTTPS
     - Gratuit
     - ✅
   * - 🔒 **Elastic IP**
     - Adresse IP publique fixe (13.37.60.84)
     - Reçoit requêtes → dirige vers EC2
     - Gratuit*
     - ✅ Gardé
   * - 🛡️ **VPC & Security Group**
     - Pare-feu numérique autorisant port 8501
     - Vérifie & laisse passer trafic légitime
     - Gratuit
     - ✅ Gardé
   * - 🖥️ **EC2 Instance**
     - Serveur 2vCPU/4GB RAM Ubuntu 24.04
     - Exécute Streamlit & traite requêtes
     - ~30€/mois
     - ✅ Gardé
   * - 🍳 **Streamlit App**
     - Application Python interactive (port 8501)
     - Charge données, crée visualisations
     - Gratuit
     - ✅ Gardé
   * - ✓ **User's Browser**
     - Navigateur affichant l'interface web
     - Affiche l'app & envoie actions utilisateur
     - Gratuit
     - ✅

\* *Gratuit tant que l'Elastic IP est attachée à une instance en cours d'exécution*

Composants Non Utilisés
------------------------

Pour des raisons de **contrôle des coûts** et de simplicité, certains composants AWS classiques 
ne sont pas utilisés :

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Composant
     - Coût
     - Raison
   * - **Route 53** (DNS)
     - 0.50€/mois
     - Accès direct via IP ``13.37.60.84:8501``
   * - **Application Load Balancer** (ALB)
     - 25€/mois
     - Une seule instance suffit (~500 users max)
   * - **Auto Scaling Group**
     - Gratuit*
     - Pas de besoin d'auto-scaling pour une démo

\* *Gratuit mais nécessiterait un ALB payant*

Configuration Technique
-----------------------

Instance EC2
~~~~~~~~~~~~

**Type** : ``t3.medium``

* **vCPU** : 2
* **RAM** : 4 GB
* **Stockage** : 20 GB gp3 SSD
* **OS** : Ubuntu 24.04 LTS
* **Région** : eu-west-3 (Paris)

Security Group
~~~~~~~~~~~~~~

Règles d'entrée (Inbound) :

.. code-block:: text

   Port 8501 (TCP) : 0.0.0.0/0  # Streamlit
   Port 22 (SSH) : [IP Admin]   # Administration

Règles de sortie (Outbound) :

.. code-block:: text

   All traffic : 0.0.0.0/0      # Internet access

Application Streamlit
~~~~~~~~~~~~~~~~~~~~~

* **Port** : 8501
* **Workers** : 1 (mode single-process)
* **Max upload size** : 200 MB
* **Cache** : Activé (Streamlit native + cache disque)
* **Données** : Chargées en mémoire au démarrage

Déploiement
-----------

Processus de Déploiement
~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Connexion SSH** à l'instance EC2
2. **Pull** du code depuis GitHub
3. **Installation** des dépendances avec ``uv``
4. **Lancement** de l'application :

   .. code-block:: bash

      cd /home/ubuntu/IADATA700_mangetamain
      git pull origin main
      uv sync
      uv run streamlit run src/app.py --server.port=8501

5. **Vérification** : http://13.37.60.84:8501

Gestion du Service
~~~~~~~~~~~~~~~~~~

L'application peut être gérée via **systemd** pour un démarrage automatique :

.. code-block:: bash

   # Démarrer le service
   sudo systemctl start mangetamain

   # Arrêter le service
   sudo systemctl stop mangetamain

   # Voir les logs
   sudo journalctl -u mangetamain -f

Monitoring
----------

Métriques EC2
~~~~~~~~~~~~~

Via AWS CloudWatch (gratuit) :

* CPU utilization
* Network in/out
* Disk read/write
* Status checks

Logs Application
~~~~~~~~~~~~~~~~

Logs stockés localement sur l'instance :

* ``debug/debug.log`` : Logs détaillés (INFO/DEBUG)
* ``debug/errors.log`` : Erreurs uniquement

Performances
------------

Capacité
~~~~~~~~

* **Utilisateurs simultanés** : ~500 (estimation)
* **Temps de réponse** : <2s pour les requêtes simples
* **Temps de chargement initial** : ~3-5s

Limitations
~~~~~~~~~~~

* Pas de haute disponibilité (single instance)
* Pas de load balancing
* Pas de CDN pour les assets statiques
* Downtime lors des mises à jour

Évolutions Possibles
~~~~~~~~~~~~~~~~~~~~

Pour un passage en production :

1. **Load Balancer** + **Auto Scaling** pour la haute disponibilité
2. **Route 53** pour un nom de domaine personnalisé
3. **CloudFront** (CDN) pour améliorer les performances
4. **RDS** pour une base de données persistante
5. **S3** pour stocker les données brutes
6. **ElastiCache** pour un cache distribué

Coûts
-----

Estimation Mensuelle
~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Ressource
     - Configuration
     - Coût mensuel
   * - EC2 t3.medium
     - 2 vCPU, 4 GB RAM, 24/7
     - ~30€
   * - Elastic IP
     - Attachée à l'instance
     - Gratuit
   * - Stockage EBS
     - 20 GB gp3
     - ~2€
   * - Transfert de données
     - ~10 GB/mois sortants
     - ~1€
   * - **TOTAL**
     - 
     - **~33€/mois**

Comparaison des Deux Déploiements
----------------------------------

Les deux environnements sont utilisés **en parallèle** pour évaluer et comparer les approches.

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Critère
     - Streamlit Cloud
     - AWS EC2
   * - **Coût**
     - ✅ Gratuit (plan Community)
     - ❌ ~33€/mois
   * - **Déploiement**
     - ✅ Automatique depuis GitHub
     - ⚠️ Manuel (SSH + git pull)
   * - **Maintenance**
     - ✅ Gérée par Streamlit
     - ❌ À gérer (updates, monitoring)
   * - **Contrôle**
     - ❌ Limité (ressources fixes)
     - ✅ Total (SSH, config, monitoring)
   * - **Performances**
     - ⚠️ Variables (ressources partagées)
     - ✅ Garanties (ressources dédiées)
   * - **Personnalisation**
     - ❌ Limitée (port 8501 fixe)
     - ✅ Complète (ports, services, etc.)
   * - **URL**
     - https://[app-name].streamlit.app
     - http://13.37.60.84:8501
   * - **Uptime**
     - ✅ Géré par Streamlit (~99%)
     - ⚠️ À gérer (redémarrages)

**Conclusion de la comparaison** :

* **Streamlit Cloud** : ✅ **Solution retenue** - Idéal pour prototypes, démos, projets académiques (gratuit, simple)
* **AWS EC2** : Testé puis désactivé - Recommandé pour production, besoins spécifiques, contrôle total (payant, flexible)

**Décision** : Streamlit Cloud a été choisi comme solution de déploiement final pour ce projet académique, 
offrant un excellent compromis entre fonctionnalités et coût (gratuit).


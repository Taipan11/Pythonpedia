
# Pythonpédia — Encyclopédie distribuée de ressources Python

Pythonpédia est une encyclopédie collaborative et distribuée consacrée au langage Python.

Chaque ordinateur participant héberge un serveur HTTP indépendant, contenant un catalogue de ressources organisées en **topics**, **items** et **URL de référence**.

Les serveurs peuvent communiquer entre eux grâce à une API REST commune, découvrir d'autres participants et synchroniser leurs ressources.

Le projet est développé avec **Python 3.11+**, **FastAPI**, **Pydantic**, **HTTPX** et **Jinja2**.

## 1. Fonctionnalités

### Encyclopédie et consultation

- Catalogue de ressources Python organisé par thématiques.
- Consultation des topics et de leurs références.
- Recherche locale dans les noms des topics et des items.
- Recherche fédérée sur les serveurs approuvés.
- Regroupement des résultats distants et suppression des URL dupliquées.
- Identification des serveurs à l'origine des ressources.

### Communication distribuée

- API REST publique respectant les contrats imposés.
- Annuaire des serveurs connus.
- Consultation des topics d'un serveur distant.
- Synchronisation incrémentale des topics, items et URL.
- Récupération des annuaires distants.
- Validation des réponses JSON.
- Gestion des erreurs réseau et des délais d'attente.
- Limitation de la concurrence des requêtes HTTP.

### Administration

- Interface web d'administration du réseau.
- Ajout manuel de serveurs.
- Découverte de serveurs compatibles.
- Approbation explicite des serveurs découverts.
- Synchronisation des serveurs approuvés.
- Consultation des résultats des opérations.
- Protection des endpoints administratifs par clé API.

### Stockage

Deux backends sont disponibles :

- **Memory** : stockage en mémoire, adapté aux démonstrations et tests.
- **SQLite** : stockage persistant, adapté aux synchronisations entre sessions.

Les deux implémentations utilisent les mêmes interfaces de repository.

---

## 2. Installation

### Prérequis

- Python 3.11 ou supérieur
- pip
- Un terminal
- Un navigateur web

### Cloner ou récupérer le projet

Se placer dans le dossier racine du projet, contenant `requirements.txt`.

### Créer un environnement virtuel

Sous Linux ou macOS :

```bash
python -m venv .venv
source .venv/bin/activate
```

Sous Windows :

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Installer les dépendances

```bash
pip install -r requirements.txt
```

### Configurer l'application

Créer un fichier `.env` à la racine du projet.

Exemple de configuration pour un développement local :

```dotenv
STORAGE_BACKEND=sqlite
DB_PATH=pythonpedia.db

HOST=127.0.0.1
PORT=8888

REQUEST_TIMEOUT=5
MAX_RESPONSE_BYTES=1048576

ADMIN_API_KEY=1

DISCOVERY_CANDIDATES=["http://127.0.0.1:8889","http://127.0.0.1:8890"]
```

Les paramètres de découverte sont facultatifs.

**Important :** la clé `1` est destinée uniquement à une démonstration locale. Pour une utilisation sur un réseau partagé, choisir une clé robuste et utiliser un accès administrateur sécurisé.

Ne pas publier le fichier `.env` dans le dépôt Git.

### Initialiser les ressources

```bash
python -m app.cli seed
```

Cette commande permet d'initialiser le catalogue selon le backend configuré.

Avec SQLite, les données sont persistantes. Avec le backend mémoire, chaque processus possède son propre catalogue : une commande CLI exécutée séparément ne modifie donc pas la mémoire du serveur Uvicorn.

### Démarrer le serveur

Pour un développement local :

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8888 --reload
```

Pour rendre le service accessible depuis d'autres ordinateurs d'un réseau autorisé :

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8888
```

L'option `0.0.0.0` permet au serveur d'écouter sur ses interfaces réseau. Elle ne désactive pas les restrictions du pare-feu ou celles du réseau local.

---

## 3. Interface web

Une fois le serveur démarré, plusieurs pages sont accessibles :

| URL | Fonction |
|-----|----------|
| `/` | Page d'accueil et présentation de Pythonpédia |
| `/topics` | Consultation des topics locaux |
| `/topics/{topic_name}` | Ressources d'un topic |
| `/search` | Recherche locale et fédérée |
| `/admin/network` | Administration du réseau |
| `/docs` | Documentation interactive Swagger |
| `/openapi.json` | Description OpenAPI de l'application |

### Recherche locale

La recherche s'effectue sur les noms des topics et des items.

Exemple :

```text
http://127.0.0.1:8888/search?q=asyncio
```

Les résultats sont classés selon leur pertinence :

1. Correspondance exacte avec le nom d'un topic.
2. Correspondance partielle avec le nom d'un topic.
3. Correspondance avec le nom d'un item.

### Recherche fédérée

Depuis `/search`, l'utilisateur peut cliquer sur **Étendre la recherche au réseau**.

Exemple :

```text
http://127.0.0.1:8888/search?q=asyncio&scope=network
```

Le serveur interroge alors les autres serveurs approuvés pour rechercher des ressources supplémentaires.

Les résultats sont fusionnés par topic, les URL identiques sont dédupliquées et les serveurs sources sont conservés.

**La recherche fédérée ne modifie pas le catalogue local.** L'enregistrement des ressources distantes s'effectue uniquement lors d'une synchronisation.

---

## 4. API REST publique

Chaque instance Pythonpédia expose trois endpoints publics, conformément à la consigne.

### GET /ws/topics

Retourne la liste des topics disponibles localement.

Exemple :

```json
[
  "concurrence",
  "exceptions",
  "fonctions",
  "types"
]
```

### GET /ws/topic/{topic_name}

Retourne les items et leurs URL pour un topic donné.

Exemple :

```json
{
  "asyncio": [
    "https://docs.python.org/3/library/asyncio.html"
  ],
  "threading": [
    "https://docs.python.org/3/library/threading.html"
  ]
}
```

Un topic inexistant produit une réponse HTTP 404.

### GET /ws/annuaire

Retourne la liste des adresses des serveurs connus.

Exemple :

```json
[
  "http://192.168.1.10:8888",
  "http://192.168.1.11:8888"
]
```

L'annuaire peut inclure des serveurs découverts mais non encore approuvés.

Les contrats JSON publics sont indépendants de l'interface HTML et doivent rester compatibles avec les implémentations des autres participants.

---

## 5. Administration du réseau

Une interface d'administration est disponible à l'adresse :

```text
http://127.0.0.1:8888/admin/network
```

Elle permet de :

1. Consulter les serveurs enregistrés.
2. Détecter de nouveaux serveurs compatibles.
3. Ajouter manuellement un serveur.
4. Approuver les serveurs découverts.
5. Synchroniser les ressources.
6. Consulter les rapports d'exécution.

### Authentification

Les endpoints privés sont protégés par une clé API.

Pour la démonstration locale :

```text
Clé administrateur : 1
```

La page d'administration demande cette clé avant d'effectuer des opérations.

La clé est envoyée dans l'en-tête HTTP `X-API-Key`, sous réserve de la configuration correspondante dans `app/security.py`.

### Endpoints administratifs

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/admin/network/peers` | Liste les serveurs connus |
| POST | `/admin/network/peers` | Ajoute manuellement un serveur |
| PATCH | `/admin/network/peers/{peer_id}/approve` | Approuve un serveur |
| GET | `/admin/network/peers/{peer_id}/topics` | Consulte un serveur distant |
| POST | `/admin/network/discover` | Lance la découverte réseau |
| POST | `/admin/network/sync` | Synchronise les serveurs approuvés |

Les routes d'administration des topics sont également disponibles dans la documentation OpenAPI.

---

## 6. Découverte de serveurs — Bonus

Pythonpédia propose un mécanisme de découverte complémentaire à la consultation des annuaires REST.

Il permet de vérifier si des adresses candidates hébergent un serveur compatible.

### Principe

Pour chaque serveur candidat :

1. Normaliser son URL.
2. Effectuer une requête `GET /ws/topics`.
3. Vérifier la réponse HTTP et le format JSON.
4. Identifier les serveurs compatibles.
5. Enregistrer les nouvelles adresses dans l'annuaire.

Les serveurs découverts sont enregistrés avec :

```python
approved = False
```

Ils doivent être approuvés explicitement avant leur interrogation par les fonctions de recherche fédérée et de synchronisation.

### Configuration

Les adresses candidates sont définies dans `.env` :

```dotenv
DISCOVERY_CANDIDATES=["http://127.0.0.1:8889","http://127.0.0.1:8890"]
```

La découverte peut être déclenchée depuis l'interface d'administration ou via :

```text
POST /admin/network/discover
```

### Limites

Le mécanisme actuel vérifie des adresses candidates explicitement configurées.

Il ne réalise pas encore de découverte entièrement automatique des ordinateurs présents sur le réseau.

Une évolution envisagée consiste à utiliser les noms des postes Linux de la salle informatique, si la convention de nommage et les règles du réseau universitaire le permettent.

Les destinations interrogées doivent être explicitement autorisées.

---

## 7. Synchronisation des ressources

Pythonpédia permet de répliquer les connaissances entre différents serveurs.

### Fonctionnement

La synchronisation suit les étapes suivantes :

1. Récupérer les serveurs approuvés.
2. Interroger leur endpoint `/ws/topics`.
3. Récupérer les items et URL de chaque topic.
4. Valider les données distantes.
5. Fusionner les nouvelles références dans le catalogue local.
6. Interroger `/ws/annuaire`.
7. Enregistrer les nouvelles adresses découvertes, sans approbation automatique.

La synchronisation est incrémentale : les ressources déjà enregistrées ne doivent pas être dupliquées.

### Déclenchement

Depuis l'interface d'administration :

```text
Synchroniser les serveurs approuvés
```

Ou depuis l'API privée :

```text
POST /admin/network/sync
```

Le rapport contient notamment :

- Le serveur interrogé.
- Le nombre de topics ajoutés.
- Le nombre d'URL ajoutées.
- Le nombre de serveurs découverts.
- Les éventuelles erreurs de synchronisation.

---

## 8. Application en ligne de commande

Pythonpédia possède également une interface CLI pour certaines opérations d'administration.

Afficher les topics :

```bash
python -m app.cli topics
```

Afficher les serveurs connus :

```bash
python -m app.cli peers
```

Ajouter un serveur manuellement :

```bash
python -m app.cli add-peer http://127.0.0.1:8889
```

Synchroniser les serveurs approuvés :

```bash
python -m app.cli sync
```

**Attention au backend mémoire :** la CLI et le serveur Uvicorn exécutés dans des processus distincts ne partagent pas leurs données en mémoire.

Utiliser SQLite pour les essais nécessitant une persistance entre plusieurs commandes et le serveur web.

---

## 9. Architecture du projet

Le projet suit une architecture modulaire séparant les interfaces HTTP, la logique métier, les modèles de données et le stockage.

```text
app/
├── main.py
├── config.py
├── dependencies.py
├── security.py
├── cli.py
│
├── routers/
│   ├── public.py
│   ├── pages.py
│   ├── admin.py
│   └── network.py
│
├── models/
│   ├── topic.py
│   ├── peer.py
│   ├── synchronization.py
│   └── responses.py
│
├── services/
│   ├── catalog_service.py
│   ├── peer_service.py
│   ├── sync_service.py
│   └── discovery_service.py
│
├── repositories/
│   ├── catalog_repository.py
│   ├── peer_repository.py
│   ├── memory/
│   │   ├── catalog.py
│   │   └── peer.py
│   └── sqlite/
│       ├── database.py
│       ├── catalog.py
│       └── peer.py
│
├── parsers/
│   └── network.py
│
├── data/
│   └── seed.py
│
├── templates/
│   ├── index.html
│   ├── topics.html
│   ├── topic_detail.html
│   ├── search.html
│   └── admin_network.html
│
└── static/
    ├── css/
    │   ├── style.css
    │   ├── search.css
    │   └── admin_network.css
    └── js/
        └── admin_network.js
```

### Responsabilités

| Composant | Responsabilité |
|-----------|----------------|
| `main.py` | Initialisation de FastAPI et enregistrement des routers |
| `config.py` | Configuration et variables d'environnement |
| `dependencies.py` | Injection des repositories et services |
| `security.py` | Protection des endpoints administratifs |
| `routers/public.py` | API REST publique |
| `routers/pages.py` | Pages HTML |
| `routers/admin.py` | Administration des topics et items |
| `routers/network.py` | Administration du réseau |
| `CatalogService` | Gestion et recherche des ressources locales |
| `PeerService` | Gestion de l'annuaire et des approbations |
| `SyncService` | Recherche fédérée et synchronisation |
| `DiscoveryService` | Détection de nouveaux serveurs |
| `repositories/` | Abstraction et persistance des données |
| `parsers/network.py` | Validation des réponses distantes |

Les services ne dépendent pas directement de SQLite ou du stockage mémoire : ils utilisent les contrats définis par les repositories.

---

## 10. Tests

La suite de tests peut être exécutée avec :

```bash
python -m pytest -q
```

Les scénarios à valider couvrent notamment :

- Les trois endpoints REST publics.
- Les formats des réponses JSON.
- L'absence de duplication des références.
- La recherche locale et distante.
- La gestion des serveurs indisponibles.
- L'approbation des serveurs.
- La persistance avec SQLite.
- La découverte de serveurs compatibles.
- La synchronisation entre plusieurs instances.
- La protection des routes administratives.

### Tester deux serveurs localement

Pour simuler deux machines, il est possible de démarrer deux instances sur des ports différents :

```bash
# Terminal A
uvicorn app.main:app --host 127.0.0.1 --port 8888
```

```bash
# Terminal B
uvicorn app.main:app --host 127.0.0.1 --port 8889
```

Les instances doivent utiliser des catalogues indépendants pour démontrer une véritable synchronisation.

Avec SQLite, configurer un fichier de base de données distinct par instance.

Attention également à la configuration du port annoncé et aux adresses candidates utilisées pour la découverte.

---

## 11. Démonstration du fonctionnement distribué

Le scénario recommandé pour présenter Pythonpédia est le suivant :

1. Démarrer deux instances possédant des topics différents.
2. Vérifier que les endpoints publics retournent leurs données respectives.
3. Lancer la découverte depuis le serveur A.
4. Vérifier que le serveur B apparaît dans l'annuaire de A.
5. Approuver B dans l'interface d'administration.
6. Rechercher depuis A un topic uniquement disponible sur B.
7. Étendre la recherche au réseau et afficher les résultats.
8. Synchroniser les serveurs approuvés.
9. Vérifier que les ressources de B ont été intégrées au catalogue de A.
10. Arrêter B et vérifier que les références répliquées restent consultables sur A.

Ce scénario montre la différence entre la consultation distante et la réplication locale.

---

## 12. Limites et améliorations possibles

Plusieurs évolutions restent envisageables :

- Découverte automatique des postes Linux de la salle, selon les autorisations réseau.
- Annonce et découverte de services via mDNS/DNS-SD.
- Indexation de la recherche pour de grands catalogues.
- Optimisation des connexions HTTP et de la concurrence.
- Utilisation d'identifiants persistants pour les serveurs.
- Renforcement de la validation des destinations réseau.
- Sécurisation de l'accès administrateur sur un réseau partagé.
- Journalisation et tests d'intégration distribués supplémentaires.

La compatibilité des contrats JSON entre les différentes implémentations étudiantes reste une priorité.

---

## 13. Technologies utilisées

- **Python** : langage principal
- **FastAPI** : API REST et serveur web
- **Pydantic** : modèles et validation des données
- **HTTPX** : client HTTP asynchrone
- **SQLite** : stockage persistant
- **Jinja2** : génération des pages HTML
- **HTML / CSS / JavaScript** : interface utilisateur
- **Pytest** : tests automatisés

---

## 14. Objectif pédagogique

Pythonpédia illustre plusieurs concepts essentiels du développement d'applications distribuées :

- Architecture client-serveur
- Communication HTTP et API REST
- Interopérabilité entre implémentations
- Découverte de services
- Réplication et fusion de données
- Tolérance aux pannes
- Validation des données provenant du réseau
- Séparation entre fonctionnalités publiques et privées

Chaque ordinateur constitue un nœud autonome capable de contribuer à une encyclopédie collective de références Python.

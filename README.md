# API de Gestion de Réservations de Ressources

API REST complète pour la gestion de réservations de ressources (salles, équipements, véhicules) dans une organisation multi-sites avec système d'authentification et de permissions.

## Table des matières

- [Technologies](#technologies)
- [Architecture](#architecture)
- [Structure du projet](#structure-du-projet)
- [Modèles de données](#modèles-de-données)
- [Endpoints API](#endpoints-api)
- [Authentification et Sécurité](#authentification-et-sécurité)
- [Installation et Configuration](#installation-et-configuration)
- [Utilisation](#utilisation)

---

## Technologies

### Stack principale
- **FastAPI 0.124.4** - Framework web moderne et performant
- **SQLModel 0.0.27** - ORM basé sur SQLAlchemy et Pydantic
- **SQLAlchemy 2.0.45** - ORM SQL
- **Pydantic 2.12.5** - Validation des données
- **Uvicorn 0.38.0** - Serveur ASGI

### Base de données
- **SQLite** - Base de données locale (`resa.db`)

### Sécurité
- Hashage des mots de passe avec **PBKDF2-HMAC-SHA256**
- Sessions avec tokens sécurisés
- Middleware d'authentification personnalisé

---

## Architecture

### Structure générale

```
Application FastAPI
    ├── Middleware d'authentification (AuthMiddleware)
    ├── Routers
    │   ├── /auth - Authentification
    │   ├── /sites - Gestion des sites
    │   └── /ressources - Gestion des ressources
    ├── Services
    │   └── Logique métier pour ressources
    ├── Models (SQLModel)
    │   ├── User
    │   ├── Site
    │   ├── Department
    │   ├── Ressource
    │   ├── Reservation
    │   └── ResourceAvailability
    └── Database (SQLite)
```

### Flux d'authentification

1. **Inscription/Connexion** → Génération d'un token de session
2. **Token** → Stocké dans un cookie HTTP-only ou header Authorization
3. **Middleware** → Vérifie le token pour chaque requête protégée
4. **Request.state.user** → Utilisateur injecté dans le contexte de la requête

---

## Structure du projet

```
Tp_Reservation/
├── app/
│   ├── models/
│   │   ├── Enum/
│   │   │   ├── EtatRessource.py       # active, en_maintenance, hors_service
│   │   │   ├── Recurrence.py          # ponctuel, quotidien, hebdomadaire
│   │   │   ├── StatutReservation.py   # en_cours, confirme, annule, fini, non_present
│   │   │   ├── TypeDisponibilite.py   # disponibilite_normale, maintenance, evenement_special
│   │   │   ├── TypePriorite.py        # standard, prioritaire
│   │   │   ├── TypeRessource.py       # salle, equipement, vehicule
│   │   │   └── TypeRole.py            # employe, manager, admin
│   │   ├── Department.py              # Modèle Département
│   │   ├── Reservation.py             # Modèle Réservation
│   │   ├── ResourceAvailability.py    # Modèle Disponibilité de ressource
│   │   ├── Ressource.py               # Modèle Ressource
│   │   ├── Site.py                    # Modèle Site
│   │   └── User.py                    # Modèle Utilisateur
│   ├── router/
│   │   ├── auth.py                    # Endpoints authentification
│   │   ├── ressources.py              # Endpoints ressources
│   │   └── sites.py                   # Endpoints sites
│   ├── services/
│   │   └── ressources.py              # Logique métier ressources
│   ├── auth.py                        # Fonctions d'authentification
│   ├── database.py                    # Configuration base de données
│   ├── dependencies.py                # Dépendances FastAPI
│   ├── middleware.py                  # Middleware d'authentification
│   └── permissions.py                 # Fonctions de permissions
├── main.py                            # Point d'entrée de l'application
└── resa.db                            # Base de données SQLite
```

---

## Modèles de données

### 1. User (Utilisateur)

**Table**: `users`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | int | Clé primaire |
| `nom_utilisateur` | str | Nom d'utilisateur unique (min 3 caractères, indexé) |
| `email` | str | Email unique (indexé) |
| `nom_prenom` | str | Nom complet (min 3 caractères) |
| `hashed_password` | str | Mot de passe hashé (PBKDF2-HMAC-SHA256) |
| `role` | TypeRole | Rôle: employe, manager, admin |
| `autorisations` | List[str] | Liste d'autorisations spécifiques (JSON) |
| `priorite` | TypePriorite | Priorité: standard, prioritaire |
| `compte_actif` | bool | Statut du compte (défaut: True) |
| `site_principal_id` | int | FK vers Site |
| `department_id` | int | FK vers Department (optionnel) |
| `date_creation` | datetime | Date de création du compte |

**Relations**:
- `site_principal` → Site
- `department` → Department
- `reservations_faites` → Liste de Reservation (en tant qu'utilisateur)
- `reservations_creees` → Liste de Reservation (en tant que créateur)

---

### 2. Site

**Table**: `sites`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | int | Clé primaire |
| `nom` | str | Nom du site (min 3 caractères, indexé) |
| `adresse` | str | Adresse complète |
| `horaires_ouverture` | time | Heure d'ouverture |
| `horaires_fermeture` | time | Heure de fermeture |

**Relations**:
- `ressources` → Liste de Ressource

**Validations**:
- L'heure d'ouverture doit être avant l'heure de fermeture

---

### 3. Department (Département)

**Table**: `departments`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | int | Clé primaire |
| `nom` | str | Nom du département (min 3 caractères, indexé) |
| `site_id` | int | FK vers Site |
| `manager_id` | int | FK vers User (doit être manager ou admin) |
| `budgetAnnuel` | float | Budget annuel (optionnel, >= 0) |

**Relations**:
- `site` → Site
- `manager` → User
- `users` → Liste de User

**Validations**:
- Le manager doit avoir le rôle `manager` ou `admin`

---

### 4. Ressource

**Table**: `ressources`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | int | Clé primaire |
| `nom` | str | Nom de la ressource (min 3 caractères, indexé) |
| `type_ressource` | TypeRessource | Type: salle, equipement, vehicule |
| `capacite_maximum` | int | Capacité maximale (>= 1) |
| `description` | str | Description détaillée |
| `caracteristiques` | List[str] | Liste de caractéristiques (JSON) |
| `site_id` | int | FK vers Site |
| `localisation_batiment` | str | Bâtiment |
| `localisation_etage` | str | Étage |
| `localisation_numero` | str | Numéro de porte/local |
| `etat` | EtatRessource | État: active, en_maintenance, hors_service |
| `horaires_ouverture` | time | Heure d'ouverture (optionnel, salles uniquement) |
| `horaires_fermeture` | time | Heure de fermeture (optionnel, salles uniquement) |
| `images` | List[str] | URLs des images (JSON) |
| `tarifs_horaires` | float | Tarif horaire (optionnel, >= 0) |

**Relations**:
- `site` → Site

**Contraintes**:
- Contrainte unique sur (`nom`, `site_id`)

**Validations**:
- L'heure d'ouverture doit être avant l'heure de fermeture
- Les horaires ne sont applicables qu'aux salles

**Méthodes**:
- `localisation` → Retourne un dict avec batiment, etage, numero
- `set_localisation(batiment, etage, numero)` → Définit la localisation
- `est_ouverte(heure)` → Vérifie si la ressource est ouverte à une heure donnée
- `est_disponible()` → Vérifie si la ressource est active

---

### 5. Reservation

**Table**: `reservations`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | int | Clé primaire |
| `ressource_id` | int | FK vers Ressource |
| `user_id` | int | FK vers User (utilisateur de la réservation) |
| `createur_id` | int | FK vers User (créateur de la réservation) |
| `debut` | datetime | Date et heure de début |
| `fin` | datetime | Date et heure de fin |
| `statut` | StatutReservation | Statut: en_cours, confirme, annule, fini, non_present |
| `description` | str | Description de la réservation |
| `nbr_participants` | int | Nombre de participants (> 0, défaut: 1) |
| `note` | str | Note additionnelle (optionnel) |
| `date_creation` | datetime | Date de création |
| `date_modification` | datetime | Date de dernière modification |

**Relations**:
- `ressource` → Ressource
- `user` → User (utilisateur)
- `createur` → User (créateur)

**Validations**:
- Les heures doivent être arrondies à 15 minutes (0, 15, 30, 45)
- La fin doit être postérieure au début
- Durée minimale: 30 minutes
- Durée maximale par type de ressource:
  - Salle: 8 heures
  - Véhicule: 24 heures
  - Équipement: 8 heures
- Le nombre de participants ne doit pas dépasser la capacité de la ressource
- Impossible de créer une réservation dans le passé (sauf admin)

**Méthodes**:
- `peut_etre_annulee()` → Vérifie si la réservation peut être annulée (>= 2h avant le début)
- `annuler()` → Annule la réservation
- `confirmer()` → Confirme la réservation
- `marquer_no_show()` → Marque l'absence
- `terminer()` → Termine la réservation
- `duree_minutes` → Propriété retournant la durée en minutes
- `est_active` → Propriété indiquant si la réservation est en cours
- `est_a_venir` → Propriété indiquant si la réservation est à venir

---

### 6. ResourceAvailability (Disponibilité de ressource)

**Table**: `resource_availabilities`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | int | Clé primaire |
| `ressource_id` | int | FK vers Ressource |
| `type_disponibilite` | TypeDisponibilite | Type: disponibilite_normale, maintenance, evenement_special |
| `debut` | datetime | Date et heure de début |
| `fin` | datetime | Date et heure de fin |
| `raison_indisponibilite` | str | Raison (optionnel) |
| `recurrence` | Recurrence | Récurrence: ponctuel, quotidien, hebdomadaire |
| `date_creation` | datetime | Date de création |

**Relations**:
- `ressource` → Ressource

**Validations**:
- La fin doit être postérieure au début

---

## Endpoints API

### Authentication (`/auth`)

#### POST `/auth/register`
Inscription d'un nouvel utilisateur.

**Body**:
```json
{
  "nom_utilisateur": "jdoe",
  "email": "jdoe@example.com",
  "nom_prenom": "John Doe",
  "password": "motdepasse123",
  "role": "employe",
  "priorite": "standard",
  "site_principal_id": 1,
  "department_id": 1
}
```

**Response**: `AuthResponse` avec token de session

---

#### POST `/auth/login`
Connexion d'un utilisateur existant.

**Body**:
```json
{
  "email": "jdoe@example.com",
  "password": "motdepasse123"
}
```

**Response**: `AuthResponse` avec token de session

---

#### POST `/auth/logout`
Déconnexion (supprime le cookie de session).

**Response**:
```json
{
  "message": "Déconnexion réussie"
}
```

---

#### GET `/auth/me`
Récupère les informations de l'utilisateur connecté.

**Response**: `UserPublic`

---

### Sites (`/sites`)

#### GET `/sites/`
Liste tous les sites avec pagination.

**Query params**:
- `offset`: int (défaut: 0)
- `limit`: int (défaut: 100, max: 100)

**Response**: `List[SitePublic]`

---

#### GET `/sites/{site_id}`
Récupère un site spécifique.

**Response**: `SitePublic`

---

#### POST `/sites/`
Crée un nouveau site.

**Body**: `SiteCreate`

**Response**: `SitePublic`

---

#### PUT `/sites/{site_id}`
Met à jour un site existant.

**Permissions**: Manager ou Admin

**Body**: `SiteUpdate`

**Response**: `SitePublic`

---

#### DELETE `/sites/{site_id}`
Supprime un site.

**Response**: `{"ok": true}`

---

### Ressources (`/ressources`)

#### GET `/ressources/`
Liste toutes les ressources avec filtres, tri et pagination.

**Query params**:
- `offset`: int (défaut: 0) - Pagination
- `limit`: int (défaut: 100, max: 200) - Limite de résultats
- `type_of_ressource`: TypeRessource - Filtre par type (salle, equipement, vehicule)
- `site_id`: int - Filtre par site
- `batiment`: str - Filtre par bâtiment (recherche partielle)
- `disponible`: bool - Filtre par état (active ou non)
- `caracteristiques`: str - Filtre par caractéristiques (séparées par virgule)
- `minimum_capacity`: int - Capacité minimale requise
- `sort_by`: "nom" | "capacite" | "type" (défaut: "nom") - Champ de tri
- `sort_order`: "asc" | "desc" (défaut: "asc") - Ordre de tri

**Response**: `RessourceListResponse`
```json
{
  "items": [
    {
      "id": 1,
      "nom": "Salle de réunion A",
      "type_ressource": "salle",
      "capacite_maximum": 10,
      ...
    }
  ],
  "meta": {
    "total": 50,
    "offset": 0,
    "limit": 100,
    "returned": 50,
    "sort_by": "nom",
    "sort_order": "asc"
  }
}
```

---

#### GET `/ressources/{ressource_id}`
Récupère une ressource avec statistiques détaillées et disponibilité.

**Response**: `RessourceDetailResponse`
```json
{
  "ressource": { ... },
  "statistiques": {
    "total_reservations": 150,
    "reservations_actives": 2,
    "reservations_a_venir": 10,
    "taux_occupation_7_jours": 45.5,
    "heures_reservees_30_jours": 120.5,
    "reservation_moyenne_duree": 90.0
  },
  "prochaines_reservations": [ ... ],
  "disponibilite_7_jours": [
    {
      "date": "2025-12-17",
      "est_disponible": true,
      "raison_indisponibilite": null,
      "creneaux_disponibles": 8
    }
  ]
}
```

---

#### POST `/ressources/`
Crée une nouvelle ressource.

**Permissions**: Admin uniquement

**Body**: `RessourceCreate`

**Response**: `RessourcePublic`

---

#### PUT `/ressources/{ressource_id}`
Met à jour une ressource existante.

**Permissions**: Manager ou Admin

**Body**: `RessourceUpdate`

**Response**: `RessourcePublic`

---

#### DELETE `/ressources/{ressource_id}`
Supprime une ressource.

**Permissions**: Admin uniquement

**Response**: `{"ok": true}`

---

## Authentification et Sécurité

### Système d'authentification

#### 1. Hashage des mots de passe
- **Algorithme**: PBKDF2-HMAC-SHA256
- **Itérations**: 100,000
- **Sel**: Généré aléatoirement (16 bytes hex)
- **Format stocké**: `{salt}${hash}`

```python
# Fonction de hashage (app/auth.py:12-15)
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
                                     salt.encode('utf-8'), 100000)
    return f"{salt}${pwd_hash.hex()}"
```

#### 2. Sessions
- **Token**: Généré avec `secrets.token_urlsafe(32)` (256 bits)
- **Stockage**: En mémoire (dictionnaire Python `SESSIONS`)
- **Durée**: 24 heures
- **Cookie**: HttpOnly, SameSite=Lax

```python
# Structure d'une session (app/auth.py:84-91)
SESSIONS[token] = {
    'user_id': user_id,
    'created_at': datetime.now(),
    'expires_at': datetime.now() + timedelta(hours=24)
}
```

#### 3. Middleware d'authentification (AuthMiddleware)

Vérifie automatiquement toutes les requêtes sauf les chemins publics:
- `/docs`
- `/openapi.json`
- `/redoc`
- `/auth/register`
- `/auth/login`

**Processus**:
1. Récupère le token depuis le cookie `session_token` ou le header `Authorization: Bearer {token}`
2. Vérifie la validité du token
3. Charge l'utilisateur depuis la base de données
4. Vérifie que le compte est actif
5. Injecte l'utilisateur dans `request.state.user`

```python
# Middleware (app/middleware.py:11-55)
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Vérifie si le chemin est public
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)

        # Récupère et vérifie le token
        token = request.cookies.get("session_token") or ...
        user_id = get_session_user_id(token)

        # Charge l'utilisateur et vérifie qu'il est actif
        user = session.get(User, user_id)
        if not user or not user.compte_actif:
            return JSONResponse(status_code=401, ...)

        # Injecte l'utilisateur dans la requête
        request.state.user = user
        return await call_next(request)
```

---

### Système de permissions

#### Rôles (TypeRole)
1. **employe**: Utilisateur standard
2. **manager**: Gestionnaire avec privilèges étendus
3. **admin**: Administrateur avec tous les privilèges

#### Fonctions de permissions (app/permissions.py)

##### `require_admin(request)`
Requiert le rôle `admin`.

```python
def require_admin(request: Request) -> User:
    user = get_current_user(request)
    if user.role != TypeRole.admin:
        raise HTTPException(status_code=403, detail="Action réservée aux administrateurs")
    return user
```

##### `require_manager_or_admin(request)`
Requiert le rôle `manager` ou `admin`.

##### `require_roles(allowed_roles: list[TypeRole])`
Factory qui crée un checker pour des rôles spécifiques.

##### `require_authorization(authorization: str)`
Vérifie qu'une autorisation spécifique est présente dans `user.autorisations`.

#### Autorisations personnalisées
Les utilisateurs peuvent avoir des autorisations spécifiques stockées dans le champ `autorisations` (liste JSON). Cela permet une granularité fine des permissions au-delà des rôles.

---

### Matrice des permissions

| Endpoint | Permissions requises |
|----------|---------------------|
| `POST /auth/register` | Public |
| `POST /auth/login` | Public |
| `POST /auth/logout` | Authentifié |
| `GET /auth/me` | Authentifié |
| `GET /sites/` | Authentifié |
| `GET /sites/{id}` | Authentifié |
| `POST /sites/` | Authentifié |
| `PUT /sites/{id}` | Manager ou Admin |
| `DELETE /sites/{id}` | Authentifié |
| `GET /ressources/` | Authentifié |
| `GET /ressources/{id}` | Authentifié |
| `POST /ressources/` | **Admin uniquement** |
| `PUT /ressources/{id}` | **Manager ou Admin** |
| `DELETE /ressources/{id}` | **Admin uniquement** |

---

## Installation et Configuration

### Prérequis
- Python 3.10+
- pip

### Installation

1. Cloner le projet:
```bash
git clone <repository_url>
cd Tp_Reservation
```

2. Créer et activer un environnement virtuel:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. Installer les dépendances:
```bash
pip install fastapi==0.124.4 sqlmodel==0.0.27 uvicorn[standard]==0.38.0 python-multipart==0.0.20
```

### Configuration de la base de données

La base de données SQLite est créée automatiquement au démarrage de l'application.

**Fichier**: `resa.db` (à la racine du projet)

La création des tables est gérée par SQLModel via le lifecycle hook `lifespan` dans `main.py:18-21`.

---

## Utilisation

### Démarrage du serveur

```bash
uvicorn main:app --reload
```

L'API sera accessible sur `http://localhost:8000`

### Documentation interactive

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Exemple de workflow

#### 1. Créer un site
```bash
curl -X POST "http://localhost:8000/sites/" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Campus Paris",
    "adresse": "123 Rue de la Paix, 75000 Paris",
    "horaires_ouverture": "08:00:00",
    "horaires_fermeture": "20:00:00"
  }'
```

#### 2. S'inscrire
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "nom_utilisateur": "jdoe",
    "email": "john.doe@example.com",
    "nom_prenom": "John Doe",
    "password": "SecurePassword123",
    "role": "employe",
    "priorite": "standard",
    "site_principal_id": 1
  }'
```

Réponse:
```json
{
  "message": "Inscription réussie",
  "user": { ... },
  "token": "abc123..."
}
```

#### 3. Se connecter
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecurePassword123"
  }'
```

#### 4. Créer une ressource (avec token)
```bash
curl -X POST "http://localhost:8000/ressources/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Salle de réunion A",
    "type_ressource": "salle",
    "capacite_maximum": 10,
    "description": "Salle équipée pour les réunions",
    "caracteristiques": ["projecteur", "tableau blanc"],
    "site_id": 1,
    "localisation_batiment": "Bâtiment A",
    "localisation_etage": "1er étage",
    "localisation_numero": "101",
    "etat": "active",
    "horaires_ouverture": "09:00:00",
    "horaires_fermeture": "18:00:00",
    "images": [],
    "tarifs_horaires": 50.0
  }'
```

#### 5. Lister les ressources avec filtres
```bash
curl -X GET "http://localhost:8000/ressources/?type_of_ressource=salle&disponible=true&minimum_capacity=8&sort_by=capacite&sort_order=desc" \
  -H "Authorization: Bearer {token}"
```

#### 6. Récupérer les détails d'une ressource
```bash
curl -X GET "http://localhost:8000/ressources/1" \
  -H "Authorization: Bearer {token}"
```

---

## Caractéristiques techniques avancées

### 1. Validations métier

Le projet utilise les validators SQLAlchemy pour appliquer des règles métier:

- **Horaires de site/ressource**: L'ouverture doit être avant la fermeture (app/models/Site.py:25-31)
- **Réservations**:
  - Heures arrondies à 15 minutes (app/models/Reservation.py:82-87)
  - Durée minimale de 30 minutes (app/models/Reservation.py:67-68)
  - Durée maximale selon le type de ressource (app/models/Reservation.py:70-79)
  - Nombre de participants ≤ capacité (app/models/Reservation.py:116-123)
- **Départements**: Le manager doit avoir le rôle approprié (app/models/Department.py:40-49)

### 2. Relations complexes

Le projet utilise des relations bidirectionnelles avec gestion des conflits:

```python
# Exemple: User a deux relations vers Reservation
reservations_faites: List["Reservation"] = Relationship(
    back_populates="user",
    sa_relationship_kwargs={"foreign_keys": "[Reservation.user_id]"}
)
reservations_creees: List["Reservation"] = Relationship(
    back_populates="createur",
    sa_relationship_kwargs={"foreign_keys": "[Reservation.createur_id]"}
)
```

### 3. Schémas Pydantic séparés

Chaque modèle a plusieurs schémas pour différents contextes:
- **Base**: Champs communs
- **[Model]**: Table SQLModel avec relations
- **[Model]Public**: Réponse API (expose l'ID et les timestamps)
- **[Model]Create**: Création (valide les champs requis)
- **[Model]Update**: Mise à jour (tous les champs optionnels)

### 4. Services métier

La logique complexe est extraite dans des services (app/services/ressources.py):
- `ressource_list()`: Filtrage et tri dynamiques (16-84)
- `get_ressource_statistics()`: Calcul de statistiques (87-173)
- `get_prochaines_reservations()`: Récupération des prochaines réservations (176-203)
- `get_disponibilite_7_jours()`: Calcul de disponibilité sur 7 jours (206-278)

### 5. Contraintes de base de données

```python
# Contrainte unique composite sur Ressource
__table_args__ = (
    UniqueConstraint("nom", "site_id", name="unique_nom_site"),
)
```

### 6. Type safety avec TYPE_CHECKING

Pour éviter les imports circulaires:

```python
if TYPE_CHECKING:
    from app.models.Ressource import Ressource
    from app.models.User import User
```

---

## Évolutions possibles

### Court terme
- [ ] Router pour les réservations (CRUD complet)
- [ ] Router pour les départements
- [ ] Router pour les disponibilités de ressources
- [ ] Endpoints de gestion des utilisateurs (CRUD par admin)
- [ ] Filtres avancés sur les réservations (par date, utilisateur, statut)

### Moyen terme
- [ ] Système de notifications (email/webhook) pour confirmations/rappels
- [ ] Calendrier ICS export/import
- [ ] Recherche full-text sur les ressources
- [ ] Système de favoris/préférences utilisateur
- [ ] Statistiques agrégées par site/département
- [ ] Rapports d'utilisation (PDF/CSV)

### Long terme
- [ ] Migration vers PostgreSQL pour production
- [ ] API webhooks pour intégrations tierces
- [ ] Système de conflits et résolution automatique
- [ ] ML pour suggestions de ressources
- [ ] Application mobile (API-first)
- [ ] SSO/OAuth2 (Google, Microsoft)
- [ ] Multi-tenancy

---

## Notes techniques importantes

### Sécurité
- Les mots de passe ne sont jamais stockés en clair
- Les sessions sont stockées en mémoire (considérer Redis pour production)
- Les cookies sont HttpOnly pour prévenir XSS
- CORS doit être configuré pour production
- Considérer l'ajout de rate limiting

### Performance
- Indexes sur les champs fréquemment filtrés (email, nom_utilisateur, nom)
- Pagination systématique pour éviter les gros datasets
- Considérer la mise en cache pour les statistiques

### Base de données
- SQLite est adapté pour le développement
- Pour production, migrer vers PostgreSQL ou MySQL
- Prévoir des migrations avec Alembic

### Tests
- Aucun test automatisé actuellement
- Recommandé: pytest + httpx pour tests d'intégration
- Recommandé: coverage.py pour mesurer la couverture

---


## Auteurs

 [GAUDIN Luidgi](https://github.com/luidgi-gaudin)

documentation générée automatiquement par IA
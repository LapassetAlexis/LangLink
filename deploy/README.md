# Déploiement

## Une seule stack : `db` + `api` + `web`

`deploy/stack.yml` décrit l'application complète. Le SPA et l'API partagent une seule
origine : nginx sert le front statique et proxifie `/api/` vers le service `api:8000`,
donc **aucun CORS** et aucun cookie cross-site.

| Service | Image / build | Port publié |
|---|---|---|
| `db` | `postgres:16-alpine` | `192.168.1.100:5433` |
| `api` | build `backend/` | `8001` → `8000` |
| `web` | build `frontend/` (nginx) | `8081` → `80` |

Le port `5433` est publié **pour les tests** (Alembic, pytest) exécutés depuis le conteneur
de l'agent. À retirer en production.

## Comment la stack est créée

⚠️ **Pas depuis un chemin local.** Portainer lit les contextes de build **depuis son propre
conteneur**, pas depuis l'hôte Docker : un `build: context: /home/tristabeau/...` échoue
avec `unable to prepare context: path ... not found`, même quand le chemin existe bien sur
l'hôte (vérifié). Seule une stack **depuis un dépôt Git** fonctionne : Portainer clone le
dépôt et résout les contextes relativement à ce clone.

### Procédure de redéploiement

```bash
python scripts/deploy_stack.py      # supprime puis recrée la stack depuis Git, Env complet
```

⚠️ **Ne pas utiliser `PUT /api/stacks/{id}/git/redeploy`** (Portainer 2.33.3) : cet appel
**vide `Env` et `ReferenceName`**. Les conteneurs démarrent alors avec des variables vides et
l'API refuse de démarrer (`DATABASE_URL doit etre un DSN PostgreSQL`, `JWT_SECRET ...`).
Diagnostiqué dans les logs du conteneur. La recréation complète est la seule voie fiable ;
le volume `langlink_pgdata` a un nom explicite et survit à la suppression de la stack.

### Création initiale

1. Pousser le dépôt sur GitHub (`main`).
2. Dans Portainer : **Stacks → Add stack → Repository**
   - Repository URL : `https://github.com/LapassetAlexis/LangLink`
   - Compose path : `deploy/stack.yml`
   - Branch : `main`
3. Renseigner les variables d'environnement de la stack :

| Variable | Exemple |
|---|---|
| `POSTGRES_DB` | `langlink` |
| `POSTGRES_USER` | `langlink` |
| `POSTGRES_PASSWORD` | *(généré)* |
| `DATABASE_URL` | `postgresql+psycopg://langlink:<mdp>@db:5432/langlink` |
| `JWT_SECRET` | *(généré, ≥ 32 caractères)* |
| `PUBLIC_BASE_URL` | `http://192.168.1.100:8081` |
| `APP_ENV` | `dev` |
| `DB_BIND` | `192.168.1.100` |
| `DB_PORT` | `5433` |
| `API_PORT` | `8001` |
| `WEB_PORT` | `8081` |

⚠️ Toute mise à jour de la stack via l'API doit renvoyer l'objet `Env` existant, sinon les
variables sont effacées (pitfall documenté dans la skill `portainer-api`).

## Base de développement temporaire

En attendant la stack complète, `langlink-db` (PostgreSQL 16 seul, sans build) est déployée
et utilisable :

```
hôte     192.168.1.100
port     5433
base     langlink
rôle     langlink
```

Identifiants dans `/workspace/.langlink_stack_env.json` (chmod 600, hors dépôt).
Le volume s'appelle **`langlink_pgdata`** (nom explicite) : il survivra à la bascule vers
la stack complète.

Vérifié sur cette base : PostgreSQL 16.15, `citext` 1.6, `jsonb`, `array`.

## Migrations — à jouer AVANT de redéployer

Le conteneur `api` ne joue **pas** `alembic upgrade head` au démarrage. Toute migration
ajoutée au code doit donc être appliquée à la base de production avant le redéploiement,
sinon l'API lit une colonne inexistante et renvoie **500**.

```bash
cd backend && . .venv/bin/activate
TARGET_DB=langlink python /tmp/al.py upgrade head   # ou : alembic -x db=prod upgrade head
TARGET_DB=langlink python /tmp/al.py current        # doit afficher la dernière révision
```

Incident du 18/10/2026 : la colonne `profiles.preferences` existait en code et en base de
test, mais pas en production. Le bouton « Continuer » du wizard a renvoyé `Internal Server
Error` jusqu'à ce que la migration soit jouée.

Correctif durable (à faire) : copier `alembic/` et `alembic.ini` dans l'image et lancer
`alembic upgrade head` avant `uvicorn` dans le `CMD` du conteneur.

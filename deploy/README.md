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

### Procédure

1. Pousser le dépôt sur GitHub (`main`).
2. Dans Portainer : **Stacks → Add stack → Repository**
   - Repository URL : `https://github.com/LapassetAlexis/LangLink`
   - Compose path : `deploy/stack.yml`
   - Branch : `main`
3. Renseigner les variables d'environnement de la stack :

| Variable | Exemple |
|---|---|
| `REPO_PATH` | `.` (racine du clone) |
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

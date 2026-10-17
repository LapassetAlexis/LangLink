# LangLink

Plateforme de correspondance linguistique **asynchrone**, centrée sur des centres
d'intérêt communs. Deux personnes qui apprennent mutuellement la langue de l'autre,
sans IA générative dans la conversation.

- **Backend** : API REST FastAPI (`backend/`) — à venir
- **Frontend** : application web React + TypeScript (`frontend/`) — à venir
- **Méthode** : Spec-Driven Development avec [OpenSpec](https://github.com/Fission-AI/OpenSpec)

## État du projet

| Étape | Statut |
|---|---|
| 1. Spécification maître (`openspec/specs/core.spec.md`) | ✅ validée (Option A) |
| 2. Planification OpenSpec du change `mvp-v1` | ✅ 4/4 artefacts, `openspec validate --strict` vert |
| 3. Initialisation backend + frontend | ⏳ lot 1 de `tasks.md` (96 tâches) |
| 4. Implémentation par lots | ⏸ non démarrée |

### Le change `mvp-v1`

| Artefact | Contenu |
|---|---|
| `openspec/changes/mvp-v1/proposal.md` | Pourquoi, périmètre, 10 capacités, impact |
| `openspec/changes/mvp-v1/specs/*/spec.md` | 10 deltas natifs : **44 exigences, 71 scénarios** |
| `openspec/changes/mvp-v1/design.md` | 15 décisions techniques (SQL de matching, offsets Unicode, idempotence, caches…) |
| `openspec/changes/mvp-v1/tasks.md` | **96 tâches** en 17 lots, chacune avec son critère de vérification |

`core.spec.md` reste la spec de revue humaine ; les deltas natifs sont la source de vérité
parsée par le CLI et seront fusionnés dans `openspec/specs/` à l'archivage du change.

> Aucun code d'implémentation n'est écrit avant la validation de la spec.

## Déploiement actuel

Stack Portainer **`langlink`** sur le Beelink, déployée depuis ce dépôt (`deploy/stack.yml`) :

| Accès | URL |
|---|---|
| Application web | http://192.168.1.100:8081 |
| API (directe) | http://192.168.1.100:8001/api/v1/docs |
| API via le proxy web | http://192.168.1.100:8081/api/v1/openapi.json |

Le SPA et l'API partagent une seule origine : nginx proxifie `/api/` vers `api:8000`,
donc aucun CORS. La base PostgreSQL n'est exposée sur le LAN (`:5433`) que pour les tests
Alembic/pytest ; voir `deploy/README.md`.

## CI

`.github/workflows/ci.yml` — 3 jobs (backend, frontend, specs OpenSpec) exécutés à chaque
push sur `main`. Dernier run vert : `39070356338`.

## Lire la spécification

| Fichier | Contenu |
|---|---|
| `openspec/specs/core.spec.md` | Spec maître : principes, entités, schéma BDD, contrats API, matching, messagerie, outils linguistiques, flux UI/UX, sécurité, décisions par défaut |
| `openspec/config.yaml` | Contexte projet et règles de rédaction des artefacts |
| `openspec/changes/` | Propositions de modifications (vides pour l'instant) |

## Méthode

```bash
source /workspace/.tools/env.sh   # Node + CLI openspec
openspec list                     # changes actifs
openspec list --specs             # capacités
openspec validate --all --strict
openspec view                     # dashboard (TTY requis)
```

Boucle SDD : `propose → validate → apply → sync → archive`.
Chaque exigence (`REQ-*`) porte au moins un scénario WHEN/THEN testable ; les tâches
d'implémentation vivent dans `openspec/changes/<change>/tasks.md`.

## Conventions

- Réponses et documentation en **français**.
- Aucun appel à un modèle génératif dans le produit (contrainte P2 de la spec).
- Messagerie asynchrone uniquement : pas de WebSocket en V1.
- Un like mutuel est la seule façon d'ouvrir une conversation.

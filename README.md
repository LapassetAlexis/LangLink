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
| 1. Spécification maître (`openspec/specs/core.spec.md`) | ✅ rédigée, **en attente de validation** |
| 2. Validation des specs | ⏳ en cours |
| 3. Initialisation backend + frontend | ⏸ bloquée par l'étape 2 |
| 4. Implémentation par change OpenSpec | ⏸ |

> Aucun code d'implémentation n'est écrit avant la validation de la spec.

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

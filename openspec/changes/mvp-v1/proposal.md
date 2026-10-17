# Proposal — mvp-v1 : LangLink, plateforme de correspondance linguistique

## Why

Il n'existe pas d'outil qui mette en relation deux apprenants **de façon réellement
réciproque** (chacun enseigne sa langue et apprend celle de l'autre) autour d'intérêts
partagés, sans transformer l'échange en conversation avec une IA. Les applications
existantes soit gamifient à l'extrême (leçons, streaks), soit sont des sites de rencontre
détournés. LangLink vise l'échange humain asynchrone, avec des outils **déterministes**
d'assistance (traduction, furigana, correction par les pairs) : aucune génération de texte
automatique n'entre dans la conversation.

Ce change livre le MVP complet, du premier écran d'inscription au premier message échangé,
en deux applications découplées (API REST + Web).

## What Changes

- **Nouveau** : API REST `/api/v1` (FastAPI, PostgreSQL, JWT + OAuth), contrat OpenAPI
  versionné, migrations Alembic.
- **Nouveau** : application web React/TypeScript (Vite), mobile-first, mode sombre.
- **Nouveau** : enrôlement progressif en 3 étapes — langues (obligatoire), intérêts
  (obligatoire, ≥ 3), profil (sautable) — avec persistance à chaque étape.
- **Nouveau** : moteur de matching à **réciprocité linguistique stricte** + score
  d'affinité explicable (intérêts communs + proximité CECRL), feed de 20 profils/jour et
  rewind borné.
- **Nouveau** : messagerie asynchrone 1-à-1 ouverte **uniquement sur like mutuel**, avec
  statut de lecture, polling borné, envoi idempotent et file locale hors connexion.
- **Nouveau** : icebreakers — 3 questions issues d'un catalogue statique, persistées à la
  création du match, donc stables dans le temps.
- **Nouveau** : correcteur collaboratif par **suggestion localisée** (offsets + remplacement)
  acceptée ou refusée par l'auteur ; le corps d'origine n'est jamais modifié.
- **Nouveau** : outils linguistiques à la demande — traduction (LibreTranslate auto-hébergé,
  DeepL en secours) avec cache, et aide à la lecture japonaise hors ligne
  (tokenizer + furigana + romaji).
- **Nouveau** : blocage, signalement avec instantané du contenu, et suppression de compte
  anonymisante (RGPD).
- **Nouveau** : socle plateforme — OpenAPI généré, CI (lint + tests + build), `/healthz`,
  `/readyz`, logs JSON corrélés.

Aucune rupture de compatibilité : le dépôt distant est vide, ce change crée l'intégralité
du produit. Aucun changement `**BREAKING**` n'est donc à signaler.

## Capabilities

### New Capabilities

| Capacité | Périmètre | Exigences |
|---|---|---|
| `identity` | Compte, mots de passe, jetons, OAuth | REQ-IDN-01…03 |
| `onboarding` | Wizard 3 étapes, langues, intérêts, photo, découvrabilité | REQ-ONB-01…08 |
| `discovery` | Feed réciproque, exclusions, quota, swipes, rewind | REQ-DSC-01…04 |
| `matching` | Score d'affinité, création atomique du match, dématch | REQ-MAT-01…04 |
| `messaging` | Fils, envoi, lecture, édition/suppression, asynchronisme | REQ-MSG-01…06 |
| `icebreakers` | Sélection déterministe et persistance des 3 questions | REQ-ICE-01 |
| `corrections` | Suggestions localisées, décision de l'auteur, obsolescence | REQ-COR-01…03 |
| `language-tools` | Traduction + cache, aide à la lecture japonaise | REQ-LNG-01…03 |
| `safety` | Blocage, signalement, modération admin, RGPD | REQ-SAF-01…04 |
| `platform` | Schéma, OpenAPI, CI, observabilité, couverture des exigences | REQ-PLT-01…07 |

### Modified Capabilities

Aucune — projet greenfield, `openspec/specs/` ne contient encore aucune capacité
(`core.spec.md` est la spec de revue humaine, hors périmètre du parseur).

## Impact

**Code créé**

- `backend/` — FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, pytest/httpx
- `frontend/` — React 18, TypeScript, Vite, TanStack Query, Tailwind
- `docker-compose.yml` — `api`, `db` (PostgreSQL 16), `libretranslate`
- `.github/workflows/ci.yml` — lint, tests, vérification de génération des types

**Contrats et données**

- 40+ endpoints REST `/api/v1`, contrat OpenAPI publié et consommé par le front
- 16 tables PostgreSQL, contraintes d'intégrité portées par la base
- Migrations Alembic : une révision par lot livrable

**Dépendances notables**

- `fugashi`/`unidic-lite` + `pykakasi` (furigana hors ligne), `argon2-cffi`, `pyjwt`
- LibreTranslate (conteneur) ; DeepL optionnel si `DEEPL_API_KEY` est fourni

**Risques d'exploitation**

- RAM : PostgreSQL + API + LibreTranslate à côté de Plex et d'un serveur de jeu sur le
  Beelink (16 Go) — le conteneur de traduction doit rester arrêtable sans casser le reste.
- Aucun mécanisme de notification push en V1 : la latence perçue est bornée par le polling
  (15 s / 60 s), ce qui est assumé par le positionnement asynchrone.

**Hors périmètre** (voir `core.spec.md` §14) : notifications email/push, audio/vidéo,
groupes, fil public, détection automatique de langue, modération automatique, paiement,
applications natives, aide à la lecture chinois/coréen, « qui m'a liké ».

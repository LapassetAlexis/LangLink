# Design — mvp-v1

## Context

Projet **greenfield** : le dépôt distant est vide, il n'existe ni code, ni données, ni
utilisateur. Tout l'existant est la spec `openspec/specs/core.spec.md` (44 exigences,
71 scénarios), validée par le propriétaire du produit.

Contraintes structurantes héritées du contexte :

| Contrainte | Origine | Effet sur le design |
|---|---|---|
| Aucune IA générative | P2 | Interdit de fait toute dépendance LLM ; la CI le vérifie |
| Asynchrone assumé | P5 | Pas de WebSocket, pas de bus d'événements, polling borné |
| Découplage API/Web | P7 | SPA statique + API JSON versionnée, aucun rendu serveur |
| Hébergement Beelink 16 Go, Docker/Portainer | Contexte homelab | Empreinte mémoire surveillée, conteneurs arrêtables indépendamment |
| Réciprocité linguistique stricte | P1 | Le filtre est une condition de jointure, pas un scoring souple |
| Texte de l'apprenant immuable | P6 | Les corrections sont des annotations, jamais des mutations |

## Goals / Non-Goals

**Goals**

- Un contrat API stable et vérifié (`/api/v1/openapi.json`) consommé par des types générés.
- Un moteur de matching dont le classement est **déterministe et explicable** (formule
  normative de REQ-MAT-02), testable sans jeu de données réel.
- Une messagerie qui reste correcte en cas de réseau instable (idempotence, file locale).
- Des outils linguistiques **dégradables** : la panne de traduction ne casse jamais la
  conversation ; le furigana fonctionne hors ligne.
- Une suite de tests qui échoue quand un scénario de spec n'est pas couvert.

**Non-Goals**

- Temps réel, présence, indicateur « en train d'écrire ».
- Scalabilité horizontale : le MVP vise quelques centaines d'utilisateurs, mono-instance.
- Multilingue complet de l'interface (fr par défaut, en préparé mais non traduit).
- Recherche plein texte dans les messages.
- Applications mobiles natives (PWA suffisante).

## Decisions

### D-1 — Architecture par domaine, pas par couche technique

```
backend/app/
├── api/v1/<domaine>/router.py     # transport : validation, statuts, dépendances
├── services/<domaine>.py          # règles métier pures, sans HTTP
├── models/<domaine>.py            # SQLAlchemy 2 typé (Mapped[...])
├── schemas/<domaine>.py           # Pydantic v2 (in/out séparés)
└── db/{session,migrations}/
```

Règle : un module `services/` ne connaît ni `Request`, ni `HTTPException` — il lève des
exceptions de domaine (`MatchClosed`, `OwnMessage`, `InvalidRange`) traduites une seule fois
par un gestionnaire global en `application/problem+json`. Raison : rendre les règles
métier testables sans client HTTP et éviter la duplication des codes d'erreur.

Alternative écartée : architecture en couches `controllers/services/repositories`
classique — trop de fichiers intermédiaires pour un MVP, et le repository n'apporte rien
au-dessus de SQLAlchemy 2.

### D-2 — Authentification : Argon2id + JWT court + refresh opaque rotatif

- `argon2-cffi` (params RFC 9106 « second recommended »), hash vérifié en temps constant.
- Access JWT HS256, 15 min, claims `sub`, `role`, `jti`, `exp`, `iat`.
- Refresh : 32 octets aléatoires, **stocké en SHA-256**, cookie `HttpOnly; Secure;
  SameSite=Lax`, portée `/api/v1/auth`.
- Rotation systématique ; présentation d'un refresh déjà consommé ⇒ révocation de toutes
  les sessions de l'utilisateur (détection de rejeu, REQ-IDN-02).
- Le login renvoie toujours le même corps et un délai comparable (plancher de 250 ms)
  pour ne pas révéler l'existence d'un compte (REQ-SAF-03).

Alternative écartée : sessions serveur + cookie de session. Plus simple, mais incompatible
avec un client SPA multi-origine en développement et avec une future app mobile.

### D-3 — Matching : filtrage et score en une seule requête SQL

Le feed ne fait **aucune** boucle applicative sur les candidats : une requête CTE calcule
les exclusions puis le score, et pagine par curseur.

```sql
WITH me AS (
  SELECT p.user_id, p.native_language AS nat, p.target_language AS tgt,
         CASE p.target_level WHEN 'A1' THEN 1 WHEN 'A2' THEN 2 WHEN 'B1' THEN 3
                             WHEN 'B2' THEN 4 WHEN 'C1' THEN 5 WHEN 'C2' THEN 6 END AS lvl,
         ARRAY(SELECT interest_id FROM user_interests ui WHERE ui.user_id = p.user_id) AS ints
  FROM profiles p WHERE p.user_id = :uid
), cand AS (
  SELECT p.user_id, p.display_name, p.avatar_key,
         CASE p.target_level WHEN 'A1' THEN 1 WHEN 'A2' THEN 2 WHEN 'B1' THEN 3
                             WHEN 'B2' THEN 4 WHEN 'C1' THEN 5 WHEN 'C2' THEN 6 END AS lvl,
         ARRAY(SELECT interest_id FROM user_interests ui WHERE ui.user_id = p.user_id) AS ints
  FROM profiles p
  JOIN me ON p.native_language = me.tgt AND p.target_language = me.nat
  WHERE p.discoverable
    AND p.user_id <> me.user_id
    AND NOT EXISTS (SELECT 1 FROM swipes s
                    WHERE s.swiper_id = me.user_id AND s.target_id = p.user_id)
    AND NOT EXISTS (SELECT 1 FROM blocks b
                    WHERE (b.blocker_id = me.user_id AND b.blocked_id = p.user_id)
                       OR (b.blocker_id = p.user_id AND b.blocked_id = me.user_id))
), scored AS (
  SELECT c.user_id, c.display_name, c.avatar_key,
         cardinality(c.ints) AS n_cand,
         cardinality(me.ints) AS n_me,
         (SELECT count(*) FROM unnest(c.ints) i WHERE i = ANY (me.ints)) AS common,
         (1 - abs(c.lvl - me.lvl) / 5.0) AS level_fit
  FROM cand c CROSS JOIN me
), final AS (
  SELECT s.user_id, s.display_name, s.avatar_key, s.common, s.n_cand, s.n_me,
         round(100 * (
           0.5 * (s.common::numeric / GREATEST(LEAST(s.n_cand, s.n_me), 1))
         + 0.3 * (s.common::numeric / GREATEST(s.n_cand + s.n_me - s.common, 1))
         + 0.2 * s.level_fit
         ))::int AS score
  FROM scored s
)
SELECT * FROM final
ORDER BY score DESC, md5(user_id::text || :day_seed)
LIMIT :limit;
```

Points importants :

- `GREATEST(..., 1)` évite la division par zéro quand un profil n'a aucun intérêt.
- Le second critère de tri `md5(user_id || day_seed)` garantit un ordre **stable sur la
  journée** (REQ-MAT-01) tout en évitant un biais permanent d'ordre d'insertion.
- Le quota de 20/jour se compte sur `swipes.created_at::date`, pas sur le feed : un profil
  servi mais non swipé n'est pas décompté (REQ-DSC-02).
- Index nécessaires : `profiles(discoverable, native_language, target_language)`,
  `swipes(swiper_id, target_id)` (déjà unique), `blocks(blocked_id)`.

Alternative écartée : calcul du score en Python après avoir chargé tous les candidats.
Rejeté — un utilisateur avec 3 000 candidats potentiels ferait transiter 3 000 lignes pour
en afficher 20, et rendrait la pagination par curseur impossible à garantir.

### D-4 — Création atomique du match

Dans **une** transaction : `INSERT` du swipe → si `like`, `SELECT` du swipe inverse →
si présent, `INSERT` du match (`ON CONFLICT (user_a_id,user_b_id) DO NOTHING`) →
`INSERT` des 3 icebreakers → `COMMIT`. L'unicité en base est le seul arbitre en cas de
course (deux likes simultanés). La paire est **canonique** (`user_a_id < user_b_id`) pour
que la contrainte d'unicité fonctionne dans les deux sens.

Alternative écartée : table `likes` séparée de `swipes`. Deux tables pour la même décision
= deux sources de vérité et un risque de désynchronisation.

### D-5 — Icebreakers : catalogue YAML statique + sélection déterministe

- Source : `backend/app/data/icebreakers.yaml`, 6 questions par intérêt, versions FR et EN.
- Sélection : `sha256(match_id + interest_slug)` ordonne les candidats ; on prend une
  question par intérêt commun distinct, puis on complète en repiochant dans les intérêts
  déjà utilisés si l'intersection est trop petite.
- Persistance : les 3 questions sont **écrites** dans `icebreakers` à la création du match.
  Le YAML peut évoluer, les matchs existants ne changent pas (REQ-ICE-03).
- Aucune génération : le catalogue est du contenu éditorial relu, pas du texte produit.

### D-6 — Corrections : offsets en points de code Unicode

Décision critique d'interopérabilité : **tous les offsets de l'API sont exprimés en points
de code Unicode** (`len()` Python), jamais en unités UTF-16.

Conséquence côté front : `Array.from(body)` ou `[...body]` avant tout découpage de chaîne,
puisque `String.prototype.slice` de JavaScript travaille en UTF-16. Un emoji (paire
surrogate) décalerait sinon toutes les plages suivantes.

Rendu : `GET /messages` renvoie `body` **et** `body_rendered`. Le serveur applique les
corrections `accepted` sur le corps d'origine ; le client n'a aucune logique de diff à
porter. Les corrections `pending` sont renvoyées séparément avec leurs offsets.

Obsolescence : à l'édition d'un message, on recalcule `body[start:end]` ; si le fragment ne
correspond plus à `original_text`, la correction passe `stale` (REQ-COR-03).

Alternative écartée : stocker directement le message corrigé dans `body`. Rejeté par P6 et
BR-07 — on perdrait la version de l'apprenant, qui est la valeur pédagogique du produit.

### D-7 — Messagerie : keyset pagination + idempotence par contrainte

- Pagination `(created_at, id)` descendante, jamais `OFFSET` : stable même si de nouveaux
  messages arrivent pendant le défilement.
- Idempotence : `UNIQUE (match_id, sender_id, client_key)`. Un renvoi avec la même
  `Idempotency-Key` renvoie `200` avec le message existant au lieu de créer un doublon
  (le scénario « perte de connexion » de REQ-MSG-05).
- Le compteur de non-lus est une requête `COUNT` sur `message_reads` manquants, avec un
  index partiel ; pas de colonne dénormalisée à maintenir.
- `last_message_at` est mis à jour dans la même transaction que l'insertion du message.

### D-8 — Polling avec ETag

`GET /matches/{id}/unread-count` renvoie un `ETag` = hash du dernier `message_id` lu.
Le client envoie `If-None-Match` ; le serveur répond `304` sans corps. Objectif : rendre le
polling à 15 s quasi gratuit en bande passante (REQ-MSG-05, Non-Goal « pas de temps réel »).

Pas de `setInterval` en onglet caché : le client utilise l'API Page Visibility.

### D-9 — Traduction : adaptateur + cache + disjoncteur

```
TranslationProvider (Protocol)
├── LibreTranslateProvider   # POST /translate, timeout 5 s
└── DeepLProvider            # POST /v2/translate, timeout 5 s, si DEEPL_API_KEY

TranslationService
├── cache lookup (translations: text_hash, source_lang, target_lang, provider)
├── provider primaire → provider secondaire → LanguageProviderUnavailable (503)
└── disjoncteur : 5 échecs consécutifs ⇒ primaire court-circuité 60 s
```

- Ne jamais traduire automatiquement : uniquement sur `POST /language/translate`.
- Le texte envoyé au fournisseur est le message brut **sans** les corrections acceptées,
  afin de ne pas propager une réécriture dans le cache.
- Le HTML et le markdown sont hors périmètre : le corps est du texte simple en V1.

### D-10 — Aide à la lecture : `fugashi` + `pykakasi`, hors ligne

- `fugashi` + `unidic-lite` (dictionnaire embarqué, pas de téléchargement au runtime).
- Les tokens sont produits dans l'ordre, `start` = somme cumulée des longueurs de
  `surface` précédentes ; on vérifie l'égalité `"".join(surfaces) == text` et on renvoie
  `422` plutôt qu'une annotation fausse si l'invariant casse.
- `pykakasi` fournit le romaji Hepburn par token.
- Le moteur et sa version entrent dans la clé de cache : une montée de version invalide
  proprement les entrées (`reading_aids.engine = "fugashi-2.1/unidic-lite"`).
- Coût d'import : le tokenizer est chargé **paresseusement** (premier appel) pour ne pas
  ralentir le démarrage de l'API ni consommer ~200 Mo de RSS sur un conteneur qui ne sert
  pas le japonais.

Alternative écartée : Kuroshiro (Node). Imposerait un second runtime pour une seule
fonction, alors que le backend est Python.

### D-11 — Médias : volume local, recompression, clé opaque

- Upload : validation par magic bytes (`python-magic`), pas par extension ni par
  `Content-Type` client.
- `Pillow` : recadrage carré centré, redimensionnement 512×512, export WebP q=82,
  `ImageOps.exif_transpose` avant suppression des métadonnées.
- Nom de fichier = `uuid4().hex`, stocké dans `MEDIA_ROOT` (volume Docker), jamais le nom
  d'origine (path traversal, fuite d'information).
- Service : `GET /media/{key}` avec `Cache-Control: public, max-age=31536000, immutable`,
  car les clés sont immuables. Un remplacement de photo crée une nouvelle clé.

Alternative écartée : S3/MinIO. Ajouter un service pour des avatars 512 px sur un homelab
mono-nœud n'est pas justifié (D-08 du core.spec).

### D-12 — Frontend : features + client typé généré

```
src/
├── app/            # providers, router, layout
├── features/       # auth, onboarding, discovery, messages, profile, safety
│   └── <feature>/{api.ts, components/, hooks.ts, schemas.ts}
├── components/ui/  # primitives (Button, Card, Dialog, Progress…)
├── lib/            # http, queryClient, i18n, offsets
└── styles/
```

- Types API générés par `openapi-typescript` depuis `/api/v1/openapi.json`, vérifiés en CI :
  si le contrat change sans régénération, le build échoue (REQ-PLT-02).
- TanStack Query gère cache, retries et invalidation ; aucune donnée serveur dans un store
  global (pas de Redux).
- File d'envoi hors connexion : `lib/outbox.ts`, persistance `localStorage`, rejeu avec la
  même `Idempotency-Key` (REQ-MSG-05).
- Aucun `fetch` direct dans un composant : tout passe par `features/*/api.ts`.

### D-13 — Tests : Postgres réel, pas de mock de base

- `pytest` + `httpx.AsyncClient` + `pytest-asyncio`.
- Base de test = PostgreSQL 16 (service container en CI, `testcontainers` en local
  optionnel). Pas de SQLite : les types `citext`, `jsonb` et `array` sont utilisés par le
  schéma, un mock masquerait les erreurs de dialecte.
- Chaque test porte l'identifiant d'exigence en docstring : `"""REQ-MSG-02 — message vide"""`.
- Matrice de couverture : `scripts/coverage_matrix.py` lit les deltas de spec, extrait
  `(REQ-*, scénario)` et cherche l'identifiant dans les tests. Sort en **code 1** si un
  scénario n'a aucun test. Sortie `coverage.md` rangée dans le dossier du change.
- Frontend : `vitest` + Testing Library ; les parcours critiques (onboarding, swipe,
  envoi) sont testés au niveau composant, pas en E2E navigateur en V1.

### D-14 — Interdiction d'IA vérifiée mécaniquement

`scripts/no_llm_guard.py` échoue si l'arbre de dépendances contient `openai`,
`anthropic`, `langchain`, `google-generativeai`, `ollama`, `transformers`, ou si le code
appelle un endpoint `chat/completions`. C'est la traduction exécutable de P2 : une
contrainte de produit non vérifiée est une intention, pas une contrainte.

### D-15 — Configuration et déploiement

- `pydantic-settings`, tout par variables d'environnement, `.env.example` exhaustif.
- `docker-compose.yml` : `api`, `db`, `libretranslate` (profil `translation`, arrêtable),
  `web` (build statique servi par nginx).
- Migrations appliquées au démarrage par une commande dédiée (`alembic upgrade head` dans
  l'entrypoint), pas par l'application elle-même.
- Stack Portainer Beelink en cible, mais **aucun déploiement dans ce change** : le MVP est
  livré testé et lançable en local. Le déploiement est un change ultérieur.

## Risks / Trade-offs

| Risque | Impact | Mitigation |
|---|---|---|
| LibreTranslate consomme ~1,5 Go de RAM | Cohabitation difficile avec Plex + un serveur de jeu sur 16 Go | Conteneur sous profil `translation`, arrêtable ; l'API renvoie `503` propre et l'UI masque l'action |
| Qualité de traduction FR↔JA médiocre | Outil peu utile sur les paires éloignées | L'outil est optionnel et affiche le moteur utilisé ; DeepL en secours si clé fournie |
| Offsets Unicode mal implémentés côté front | Corrections décalées sur les emoji | Convention points de code + test dédié avec emoji et kanji combinés |
| Score d'affinité ressenti comme arbitraire | Perte de confiance | Score affiché avec ses composantes (intérêts communs, niveau) en V1 |
| PostgreSQL en plus sur le Beelink | ~150 Mo RSS + I/O | Acceptable ; pas de réplique, sauvegarde `pg_dump` quotidien |
| 360 icebreakers à rédiger | Contenu incomplet = fonctionnalité vide | Catalogue livré en une passe éditoriale, test vérifiant 6 questions par intérêt actif |
| Polling 15 s | Latence perçue, charge CPU | ETag + 304, visibilité de page, pas de polling caché |
| Fugashi au démarrage | Démarrage lent, RSS | Chargement paresseux + cache d'instance |

## Migration / Rollout

Greenfield : aucun utilisateur, aucune donnée. Livraison par lots OpenSpec cochés dans
`tasks.md`, chaque lot laissant la suite complète au vert. Aucune fenêtre de migration.

# Tasks — mvp-v1

> Convention : chaque tâche porte son **critère de vérification**. Une case n'est cochée
> (`- [x]`) que lorsque ce critère a été exécuté avec succès, jamais « parce que le code
> est écrit ». Cocher au fur et à mesure, lot par lot.
> Référence : `openspec/changes/mvp-v1/specs/<capacité>/spec.md` + `design.md`.

## 1. Socle du dépôt et garde-fous

- [x] 1.1 Créer `backend/` (pyproject, `app/` par domaine selon design D-1, `tests/`) et `frontend/` (Vite + TS + Tailwind, structure `features/` de D-12) — **vérif** : `python -c "import app"` et `npm run build` passent sur un squelette vide.
- [x] 1.2 Configurer ruff + mypy (backend) et eslint + `tsc --noEmit` (frontend) — **vérif** : `ruff check .`, `mypy app`, `npm run lint` sortent en code 0.
- [x] 1.3 Créer `docker-compose.yml` (`api`, `db` PostgreSQL 16, `libretranslate` sous profil `translation`, `web`) et `Dockerfile` multi-stage — **vérif** : compose validé **par déploiement réel** : stack Portainer `langlink` (`deploy/stack.yml`) → 3 conteneurs `running`, `db` **healthy via `pg_isready`**, `web` 200, proxy `/api` 200. ⚠️ `docker compose config -q` sur le `docker-compose.yml` de dev reste non exécuté (aucun CLI Docker dans le conteneur de l'agent).
- [x] 1.4 Écrire `.env.example` exhaustif + `pydantic-settings` avec validation au démarrage (refus si secret manquant en prod) — **vérif** : démarrage sans `.env` échoue avec un message listant les variables manquantes.
- [x] 1.5 Écrire `scripts/no_llm_guard.py` (interdit `openai`, `anthropic`, `langchain`, `google-generativeai`, `ollama`, `transformers`, endpoints `chat/completions`) — **vérif** : test d'auto-validation avec un faux import `openai` qui fait échouer le script en code 1.
- [x] 1.6 Écrire `scripts/coverage_matrix.py` : extraire `(REQ-*, scénario)` des deltas, chercher l'identifiant dans `backend/tests` + `frontend/src`, produire `coverage.md`, sortir en code 1 si un scénario est orphelin — **vérif** : lancé sur le dépôt sans tests il liste 71 orphelins et échoue ; après le lot 3 il n'en liste plus pour `identity`.
- [x] 1.7 Mettre en place `.github/workflows/ci.yml` : lint, typecheck, tests backend (service Postgres 16), tests frontend, `no_llm_guard`, `coverage_matrix`, vérification de dérive OpenAPI — **vérif** : ✅ run GitHub Actions **39070356338** sur `4cb98bf` : jobs Backend / Frontend / Specs OpenSpec tous `success` (pytest, ruff, mypy, garde-fou P2, matrice, npm lint/typecheck/test/build, `openspec validate --strict`).

## 2. Plateforme et schéma (REQ-PLT-01, PLT-02, PLT-07)

- [ ] 2.1 Initialiser SQLAlchemy 2 (Base typée, session async, `uuid7` applicatif) et Alembic — **vérif** : `alembic upgrade head` puis `alembic downgrade base` sans erreur sur une base vide.
- [ ] 2.2 Écrire la migration initiale des 16 tables du `core.spec.md` §4, avec `citext`, `jsonb`, contraintes `CHECK` et index (dont `messages(match_id, created_at DESC, id DESC)` et l'unicité `(match_id, sender_id, client_key)`) — **vérif** : `alembic upgrade head` crée les 16 tables ; `\d+ messages` montre les deux contraintes.
- [ ] 2.3 Tests d'intégrité du schéma : unicité du swipe concurrent, match dupliqué, `swiper_id <> target_id`, `user_a_id < user_b_id` — **vérif** : `pytest tests/test_schema_integrity.py` (REQ-PLT-01, ses 2 scénarios) passe, y compris le test de concurrence à deux sessions.
- [ ] 2.4 Gestionnaire d'erreurs global : exceptions de domaine → `application/problem+json` avec `type` stable (§5.1) — **vérif** : `pytest tests/test_errors.py` vérifie 422/409/403/429 et la présence de `type`, `title`, `status`, `detail`.
- [ ] 2.5 Exposer `/api/v1/openapi.json`, `/healthz`, `/readyz` (vérifie la base), logs JSON corrélés par `X-Request-Id` — **vérif** : `curl /healthz` = 200 ; base coupée ⇒ `/readyz` = 503 ; deux requêtes portent des `request_id` distincts dans les logs.
- [ ] 2.6 Générer les types frontend via `openapi-typescript` et ajouter l'étape CI de dérive — **vérif** : modifier un schéma de réponse sans régénérer fait échouer `npm run check:api` avec un diff explicite.
- [ ] 2.7 Middleware de rate limiting (mémoire locale, fenêtre glissante) + en-têtes `RateLimit-*` — **vérif** : `pytest tests/test_rate_limit.py` : 6 inscriptions en 1 min depuis la même IP ⇒ la 6ᵉ renvoie 429 avec `Retry-After`.

## 3. Identité (REQ-IDN-01, IDN-02, IDN-03)

- [ ] 3.1 Modèles `users`, `refresh_tokens` + service de hash Argon2id — **vérif** : `pytest tests/test_security.py` : un hash ne contient jamais le mot de passe, `verify` réussit, deux hashs du même mot de passe diffèrent (sel).
- [ ] 3.2 `POST /auth/register` (email `citext`, profil vide créé, `201`) — **vérif** : REQ-IDN-01, 3 scénarios verts, dont email déjà utilisé en casse différente ⇒ 409 `auth.email_taken`.
- [ ] 3.3 `POST /auth/login`, `POST /auth/refresh` (rotation + détection de rejeu), `POST /auth/logout`, `/auth/logout-all` — **vérif** : REQ-IDN-02, les 2 scénarios verts ; réutiliser un refresh révoqué révoque bien toutes les sessions.
- [ ] 3.4 `GET /auth/me` (user + profile + état d'onboarding) et dépendance `current_user` — **vérif** : sans jeton ⇒ 401 ; avec jeton expiré ⇒ 401 `auth.token_expired` ; avec jeton valide ⇒ 200 avec `onboarding.step`.
- [ ] 3.5 OAuth Google + GitHub (Authorization Code + PKCE, state signé, rapprochement par email) — **vérif** : REQ-IDN-03, les 2 scénarios verts avec un faux provider local ; `state` invalide ⇒ 400.
- [ ] 3.6 Mot de passe oublié / réinitialisation (jeton à usage unique, TTL 1 h, réponse identique quel que soit l'email) — **vérif** : deux appels avec email connu/inconnu renvoient le même corps et le même code 202.
- [ ] 3.7 Écran d'inscription/connexion (formulaires, erreurs inline, boutons OAuth, spinner < 150 ms) — **vérif** : test Vitest : soumission valide appelle `api.register`, erreur 409 affiche le message sans vider les champs.

## 4. Enrôlement — données et API (REQ-ONB-01…08)

- [ ] 4.1 Seed du catalogue : 60 intérêts, 10 catégories, libellés FR/EN, emoji, `sort_order` — **vérif** : `alembic upgrade head` puis `GET /interests` renvoie 10 catégories et 60 entrées, triées.
- [ ] 4.2 `GET /onboarding/state`, `PUT /onboarding/languages` (validation langue ≠ langue, niveau CECRL) — **vérif** : REQ-ONB-01 et ONB-02 verts, y compris `target_language == native_language` ⇒ 422 `same_as_native`.
- [ ] 4.3 `PUT /onboarding/interests` (3 à 12, transaction atomique) — **vérif** : REQ-ONB-03, les 2 scénarios verts ; un identifiant inconnu annule tout l'enregistrement.
- [ ] 4.4 Pipeline média : validation magic bytes, `exif_transpose`, carré 512, WebP q=82, clé UUID, `GET /media/{key}` immuable — **vérif** : REQ-ONB-06/07 : 8 Mo ⇒ 413, GIF ⇒ 415, JPEG avec EXIF GPS ⇒ sortie sans EXIF et 512×512.
- [ ] 4.5 `PUT /onboarding/profile` (multipart), `POST /onboarding/complete`, `PUT /me/availability` — **vérif** : REQ-ONB-04 : `complete` sans intérêts ⇒ 409 avec `missing: ["interests"]` et `discoverable` reste `false`.
- [ ] 4.6 `GET /me/profile`, `PATCH /me/profile`, `PUT /me/languages`, `PUT /me/interests`, `DELETE /me` (confirmation par mot de passe) — **vérif** : `DELETE /me` sans mot de passe ⇒ 422 ; avec ⇒ 204 et `status = deleted`.
- [ ] 4.7 Test de parcours : inscription → langues → intérêts → complete en moins de 8 requêtes — **vérif** : `pytest tests/test_onboarding_flow.py` compte les appels et vérifie `discoverable = true` à la fin.

## 5. Enrôlement — interface (REQ-ONB-05)

- [ ] 5.1 Composant `ProgressSteps` (3 segments, `aria-current`, reprise à l'étape enregistrée) — **vérif** : REQ-ONB-05 : retour arrière conserve les intérêts cochés et affiche 2/3.
- [ ] 5.2 Étape 1 : sélecteurs de langue avec recherche + niveau en segments + aperçu de la réciprocité — **vérif** : test Vitest : langue native = langue visée désactive « Continuer » et affiche l'erreur.
- [ ] 5.3 Étape 2 : grille des 10 catégories en tuiles → chips d'intérêts, compteur `n/12`, minimum 3 — **vérif** : compteur exact après 3 clics ; bouton désactivé à 2, actif à 3, bloqué à 12.
- [ ] 5.4 Étape 3 : upload avec recadrage circulaire, bio 600 caractères avec compteur, actions « Terminer » et « Plus tard » — **vérif** : REQ-ONB-06 : « Plus tard » renseigne `onboarding_done_at` et ouvre le discovery.
- [ ] 5.5 Persistance par étape côté client (TanStack Query + invalidation) et reprise après rechargement — **vérif** : test : recharger à l'étape 2 restaure les sélections depuis `GET /onboarding/state`.

## 6. Découverte — moteur (REQ-DSC-01…04, REQ-MAT-01, MAT-02)

- [ ] 6.1 Requête de feed en une CTE (réciprocité, exclusions, score, tri stable, curseur) selon design D-3 — **vérif** : `pytest tests/test_feed_query.py` sur un jeu de 6 profils ; `EXPLAIN` ne montre aucun `Seq Scan` sur `profiles` avec 10 000 lignes.
- [ ] 6.2 Vérifier la réciprocité stricte et les exclusions (soi-même, swipes, blocages, suspendus) — **vérif** : REQ-DSC-01 + REQ-DSC-03, tous les scénarios verts, dont `ja→es` invisible pour `fr→ja`.
- [ ] 6.3 Implémenter la formule de score et la figer par des tests de valeurs — **vérif** : REQ-MAT-02 : cas 3 communs sur 5 en B1 ⇒ **63** ; intersection vide ⇒ ≤ 20.
- [ ] 6.4 Curseur de pagination + ordre stable sur la journée (`day_seed` dérivé de la date locale) — **vérif** : REQ-MAT-01 : deux appels successifs renvoient exactement le même ordre.
- [ ] 6.5 `POST /discovery/swipes` (like/pass, match éventuel, `Idempotency-Key`) et `GET /discovery/swipes/{target_id}` — **vérif** : self-swipe ⇒ 422 ; double POST ⇒ une seule ligne, 409 au second.
- [ ] 6.6 Quota de 20 nouveaux profils/jour compté sur les swipes — **vérif** : REQ-DSC-02 : après 20 swipes, `items: []` et `next_cursor: null`, pas d'erreur.
- [ ] 6.7 `DELETE /discovery/swipes/{target_id}` limité à 1/heure — **vérif** : REQ-DSC-04 : second rewind ⇒ 429 `rate.limited` avec `Retry-After` ≤ 3600.

## 7. Découverte — interface

- [ ] 7.1 Pile de cartes avec gestes (glisser) et boutons équivalents, animation de sortie, rewind visible 5 s — **vérif** : test Vitest : un like appelle `api.swipe('like')` une seule fois, la carte suivante s'affiche.
- [ ] 7.2 Navigation clavier (`←` pass, `→` like) et focus visible — **vérif** : REQ-PLT-05 : `KeyboardEvent('keydown', {key:'ArrowRight'})` déclenche le like.
- [ ] 7.3 Fiche profil : photo, prénom, paire linguistique, niveau, intérêts communs mis en avant + « +N » — **vérif** : un profil avec 3 communs sur 5 affiche 3 chips et « +2 ».
- [ ] 7.4 États vides et fin de quota explicites (pas d'erreur brute) — **vérif** : feed vide ⇒ message « Revenez demain » et lien vers les messages.
- [ ] 7.5 Overlay de match (deux photos, score, intérêts communs, CTA) — **vérif** : un swipe renvoyant `match` non nul ouvre l'overlay avec le score affiché.

## 8. Matching (REQ-MAT-03, MAT-04)

- [ ] 8.1 Création atomique du match + icebreakers dans la même transaction, paire canonique — **vérif** : REQ-MAT-03 : deux likes concurrents créent un seul match et renvoient le même `match_id`.
- [ ] 8.2 `GET /matches` (dernier message, non-lus, tri) et `GET /matches/{id}` (profil public, score, icebreakers) — **vérif** : un non-membre reçoit 404 `match.not_found` (REQ-MSG-01).
- [ ] 8.3 `DELETE /matches/{id}` : `unmatched`, lecture seule, écriture refusée, swipes conservés — **vérif** : REQ-MAT-04, les 3 assertions du scénario vertes.
- [ ] 8.4 Aucune fuite de like sortant : `GET /matches` et toute réponse d'API n'exposent jamais qui a liké — **vérif** : test qui inspecte le JSON complet d'un like non réciproque et échoue si `liked_you`/`admirers` apparaît.

## 9. Messagerie — API (REQ-MSG-01…06)

- [ ] 9.1 `POST /matches/{id}/messages` : validation 1–4000 après trim, appartenance, non-blocage, mise à jour `last_message_at`, `body_lang` par défaut — **vérif** : REQ-MSG-02, les 3 scénarios verts (valide, vide/trop long, match fermé).
- [ ] 9.2 Idempotence : `UNIQUE(match_id, sender_id, client_key)`, rejeu ⇒ 200 avec le message existant, aucun doublon — **vérif** : REQ-MSG-05 : deux POST avec la même clé ⇒ un seul message en base.
- [ ] 9.3 `GET /matches/{id}/messages?limit&before` keyset `(created_at, id)`, réponse avec `body` + `body_rendered` — **vérif** : 45 messages injectés ⇒ 3 pages de 30/15 sans doublon ni trou, même avec des insertions concurrentes.
- [ ] 9.4 `POST /matches/{id}/read` en lot + `GET /matches/{id}/unread-count` avec `ETag`/304 — **vérif** : REQ-MSG-03 : compteur à 0 après marquage ; seconde requête avec `If-None-Match` ⇒ 304 sans corps.
- [ ] 9.5 `PATCH /messages/{id}` (≤ 15 min, `edited_at`) et `DELETE /messages/{id}` (soft-delete `"[message supprimé]"`) — **vérif** : édition après 15 min ⇒ 403 ; suppression ⇒ corps remplacé, ligne conservée.
- [ ] 9.6 Aucun appel LLM dans le chemin messagerie (garde-fou exécutable) — **vérif** : REQ-MSG-06 : `scripts/no_llm_guard.py` passe et aucune dépendance LLM n'apparaît dans `pip list`.
- [ ] 9.7 Chargement des messages en une requête + rendu des corrections acceptées sans requête additionnelle — **vérif** : `django-debug`-like absent, mais assertion `len(queries) == 1` via un listener SQLAlchemy sur 45 messages.

## 10. Messagerie — interface

- [ ] 10.1 Boîte de réception : liste, extrait 80 caractères, horodatage relatif, badge de non-lus — **vérif** : test Vitest avec 2 matchs, un lu et un non lu : ordre et badges corrects.
- [ ] 10.2 Fil : bulles, séparateurs de date, indicateur « Vu », pagination au défilement vers le haut, `aria-live="polite"` sur l'arrivée d'un message — **vérif** : REQ-PLT-06 : un message reçu pendant l'ouverture déclenche l'annonce dans la région live ; descendre puis remonter charge la page précédente sans dupliquer.
- [ ] 10.3 Composition : compteur 4000, envoi optimiste, réconciliation par `client_key` — **vérif** : un envoi en échec réseau garde le texte, affiche « non envoyé », le rejeu ne crée pas de doublon.
- [ ] 10.4 Polling : 15 s fil ouvert / 60 s ailleurs, arrêt total onglet caché (Page Visibility), `If-None-Match` — **vérif** : test avec faux timers : 4 ticks en 60 s fil ouvert, 0 onglet caché.
- [ ] 10.5 États d'erreur visibles (REQ-PLT-04) : message refusé, fil fermé, 503 de traduction — **vérif** : REQ-PLT-04, les 2 scénarios verts en composant.

## 11. Icebreakers (REQ-ICE-01)

- [ ] 11.1 Catalogue `data/icebreakers.yaml` : 6 questions FR/EN pour chacun des 60 intérêts (360 entrées) — **vérif** : test qui échoue si un intérêt actif n'a pas exactement 6 questions dans les deux langues.
- [ ] 11.2 Sélection déterministe : une question par intérêt commun distinct, complétion par re-pioche si intersection < 3, `sha256(match_id + slug)` — **vérif** : REQ-ICE-01 : 3 communs ⇒ 3 intérêts distincts ; 1 commun ⇒ 3 questions sans répétition ; deux exécutions ⇒ même sortie.
- [ ] 11.3 Persistance à la création et immuabilité — **vérif** : REQ-ICE-03 : modifier le YAML puis relire le match renvoie les questions d'origine.
- [ ] 11.4 Bandeau UI repliable, questions cliquables insérant le texte dans la zone de saisie — **vérif** : test Vitest : clic sur la 2ᵉ question remplit le champ sans écraser un brouillon existant.

## 12. Corrections — API (REQ-COR-01…03)

- [ ] 12.1 `POST /messages/{id}/corrections` avec validation des offsets en points de code et vérification du fragment — **vérif** : REQ-COR-01 : plage hors bornes ⇒ 422 `invalid_range` ; fragment ne correspondant pas ⇒ 422 ; `original_text` renvoyé = fragment exact.
- [ ] 12.2 Interdiction d'auto-correction et de chevauchement — **vérif** : REQ-COR-01 : auteur ⇒ 422 `own_message` ; deux plages qui se chevauchent ⇒ 409 `conflict` avec l'id existant.
- [ ] 12.3 `accept` / `reject` réservés à l'auteur, décision définitive — **vérif** : REQ-COR-02 : le correcteur qui accepte ⇒ 403 ; l'auteur accepte ⇒ `accepted` + `resolved_at` ; `messages.body` inchangé (assertion SQL directe).
- [ ] 12.4 Rendu serveur : `body_rendered` applique les corrections `accepted` sur le corps d'origine — **vérif** : 2 corrections acceptées sur des plages disjointes produisent le texte attendu ; assertion sur emoji et kanji (UTF-8 multi-octets).
- [ ] 12.5 Détection d'obsolescence à l'édition du message — **vérif** : REQ-COR-03 : édition qui invalide les offsets ⇒ statut `stale` et correction absente de la liste « à accepter ».

## 13. Corrections — interface

- [ ] 13.1 Sélection de texte dans une bulle reçue → panneau de suggestion (fragment figé, remplacement, explication) — **vérif** : test : sélectionner 10 caractères envoie `start_offset=…, end_offset=…` cohérents en points de code.
- [ ] 13.2 Affichage des suggestions : souligné ambre (correcteur) / vert pointillé (auteur), boutons Accepter / Refuser côté auteur — **vérif** : un message avec 1 suggestion `pending` affiche les 2 boutons pour l'auteur, aucun pour le correcteur.
- [ ] 13.3 Rendu de la version corrigée avec bascule vers l'original — **vérif** : REQ-COR-02 : après acceptation, le texte corrigé s'affiche, le clic révèle l'original et l'explication.
- [ ] 13.4 Offsets robustes : conversion UTF-16 → points de code dans `lib/offsets.ts` + test dédié — **vérif** : un corps contenant `👨‍👩‍👧‍👦` et des kanji produit des offsets identiques côté front et côté API.

## 14. Outils linguistiques — API (REQ-LNG-01…04)

- [ ] 14.1 Interface `TranslationProvider` + `LibreTranslateProvider` (timeout 5 s) + cache `translations` (hash, langs, provider) — **vérif** : REQ-LNG-01 : première requête `cached:false`, seconde `cached:true` sans second appel réseau (mock compteur).
- [ ] 14.2 `DeepLProvider` optionnel + bascule automatique + disjoncteur 5 échecs/60 s — **vérif** : REQ-LNG-01 : primaire en timeout ⇒ réponse du secondaire ; les deux en échec ⇒ 503 `language.provider_unavailable`, jamais 500.
- [ ] 14.3 `POST /language/translate` (par `message_id` ou texte) + `GET /language/capabilities` ; refus des paires non supportées — **vérif** : REQ-LNG-01 : paire absente ⇒ 422 `language.unsupported` ; le texte traduit est le corps brut, sans corrections appliquées.
- [ ] 14.4 Aide à la lecture : `fugashi` + `unidic-lite` + `pykakasi`, chargement paresseux, offsets en points de code — **vérif** : REQ-LNG-02 : `"私は学生です"` ⇒ 4 à 6 tokens avec `reading` et `romaji` ; `"".join(surfaces) == texte`.
- [ ] 14.5 Cache `reading_aids` (texte + lang + version moteur) + fonctionnement sans réseau — **vérif** : REQ-LNG-03 : appel avec réseau coupé (proxy blackhole) ⇒ 200 ; seconde requête servie depuis le cache.
- [ ] 14.6 Invariant d'offsets vérifié et rejet explicite si le tokenizer dérive — **vérif** : REQ-LNG-04 : test sur texte mixte kanji/kana/latin/ponctuation ⇒ concaténation identique à l'entrée.

## 15. Outils linguistiques — interface

- [ ] 15.1 Bouton « Traduire » par message reçu : remplacement temporaire, mention du moteur, lien « Voir l'original » — **vérif** : test : la traduction ne s'affiche qu'après clic, le corps original est restauré au clic sur le lien.
- [ ] 15.2 Rendu `<ruby>` du furigana + toggle romaji — **vérif** : un message japonais affiche des balises `ruby`/`rt` ; le toggle ajoute les romaji sur chaque token.
- [ ] 15.3 Masquage conditionnel des actions selon `GET /language/capabilities` — **vérif** : un message `es` n'affiche pas « Aide à la lecture » ; le bouton n'est pas rendu du tout.
- [ ] 15.4 Bandeau d'échec non bloquant en cas de 503 — **vérif** : REQ-PLT-04 : le 503 affiche « Traduction indisponible, réessayer » et le message original reste visible.

## 16. Sécurité et modération (REQ-SAF-01…04)

- [ ] 16.1 `POST /users/{id}/block` / `DELETE` / `GET /me/blocks` avec effet immédiat (feed, fil, écriture) — **vérif** : REQ-SAF-01 : blocage pendant conversation ⇒ match `blocked`, écriture 403 `safety.blocked`, profil masqué au feed.
- [ ] 16.2 `POST /reports` avec `content_snapshot` figé + catégories contraintes — **vérif** : REQ-SAF-02 : l'instantané reste identique après édition du message signalé.
- [ ] 16.3 Anti-énumération de comptes : corps identique, délai plancher 250 ms, aucune variation d'en-tête — **vérif** : REQ-SAF-03 : 50 logins sur emails inconnus ⇒ 50 réponses `401` identiques, écart-type des durées < 20 ms.
- [ ] 16.4 Suppression de compte : anonymisation, purge des médias sous 24 h, messages « Compte supprimé » — **vérif** : REQ-SAF-04 : email haché non réversible, fichier média absent du volume, fil lisible.
- [ ] 16.5 Endpoints admin (`PATCH /admin/reports/{id}`, `POST /admin/users/{id}/suspend`) protégés par rôle — **vérif** : un utilisateur `user` ⇒ 403 ; un `admin` ⇒ 200 et le compte suspendu disparaît du feed.
- [ ] 16.6 En-têtes de sécurité (CSP, HSTS, `X-Content-Type-Options`, `Referrer-Policy`) + `https` forcé en prod — **vérif** : `curl -I` en mode prod montre les 4 en-têtes ; un appel HTTP est redirigé 301.

## 17. Intégration, performance et documentation

- [ ] 17.1 Parcours de bout en bout API : deux comptes, like mutuel, match, 3 icebreakers, message, correction acceptée, traduction, blocage — **vérif** : `pytest tests/test_e2e_journey.py` passe et ne fait aucun appel réseau externe.
- [ ] 17.2 Budgets de performance du §13.3 : feed p95 < 250 ms, envoi < 150 ms, matches < 200 ms, lecture 200 car. < 200 ms — **vérif** : `pytest tests/test_perf.py` avec 5 000 profils et 50 000 messages, seuils assertés (skip si `--no-perf`).
- [ ] 17.3 Matrice de couverture complète : 71 scénarios couverts, `coverage.md` rangé dans le dossier du change — **vérif** : `python scripts/coverage_matrix.py` sort en 0 et affiche 0 orphelin.
- [ ] 17.4 `README` d'API (une ligne par endpoint), procédure de démarrage local et `alembic upgrade head` — **vérif** : suivre le README depuis un clone vide permet d'atteindre `/healthz` = 200 sans étape implicite.
- [ ] 17.5 Vérifier `openspec validate --all --strict` et la cohérence spec ↔ tests ↔ code — **vérif** : commande en code 0 ; aucune exigence du change sans test correspondant.
- [ ] 17.6 Audit final P2 (aucune IA) et P6 (aucune mutation du corps d'origine) — **vérif** : `no_llm_guard` vert + assertion SQL que `messages.body` est identique avant/après acceptation d'une correction.

# Tasks — preferences-matching

## 1. Données

- [x] 1.1 Migration : `ALTER TABLE profiles ADD COLUMN preferences jsonb NOT NULL DEFAULT '{}'` — **vérif** : `alembic upgrade head` puis `downgrade -1` sans erreur, colonne présente. — **vérif** : ✅ migration `99f703d059b9` : `upgrade` → colonne présente, `downgrade -1` → retour à `2150a02ec928`, ré-`upgrade` OK.
- [ ] 1.2 Renseigner `profiles.timezone` à l'inscription, validé contre la base IANA — **vérif** : `Europe/Paris` accepté, `Mars/Olympus` ignoré sans erreur.

## 2. API

- [x] 2.1 `GET/PUT /me/preferences` (jsonb, schéma Pydantic strict) — **vérif** : test, clé inconnue rejetée, défauts renvoyés si vide. — **vérif** : ✅ `GET/PUT /me/preferences` avec `PreferencesIn` (`extra: forbid`), 84 tests verts, ruff/mypy à 0.
- [ ] 2.2 `PUT /me/matching-criteria` réutilisant les validateurs d'enrôlement — **vérif** : test, 2 intérêts ⇒ 422 avec le même code qu'au wizard.
- [ ] 2.3 `GET /profiles/match-preview` renvoyant le nombre de profils compatibles — **vérif** : test, critères impossibles ⇒ 0.
- [ ] 2.4 Exposer `timezone` dans `GET /matches/{id}` — **vérif** : test, champ présent, valeur IANA.

## 3. Interface

- [x] 3.1 `/settings/preferences` : densité, taille, furigana auto, mot à mot par défaut, animations — **vérif** : test Vitest, changement applique la classe et appelle l'API. — **vérif** : ✅ section « Affichage » dans `/settings` : densité, taille de texte, animations, furigana auto, mot à mot par défaut — chargement + enregistrement serveur.
- [ ] 3.2 Application avant le premier rendu (script inline + `localStorage`) — **vérif** : aucun flash de thème au rechargement (constat manuel consigné).
- [ ] 3.3 `/settings/matching` : langues, niveau, intérêts, quota, visibilité + avertissement `match-preview` — **vérif** : test Vitest, avertissement affiché quand l'aperçu renvoie 0.
- [ ] 3.4 Fil : heure locale du correspondant + salutation calée sur son heure — **vérif** : test Vitest, Tokyo à 2 h ⇒ pas de « Bonjour ».

## 4. Clôture

- [ ] 4.1 `tsc`, `eslint`, `vitest`, `build`, `pytest`, `openspec validate --strict` — **vérif** : six commandes en code 0.
- [ ] 5.1 Jouer les migrations automatiquement au démarrage du conteneur `api` (`COPY alembic`
  + `alembic upgrade head && uvicorn …`) — **vérif** : un déploiement sur une base en retard applique la migration seule, `/healthz` reste 200.
- [ ] 5.2 Test d'intégration « schéma à jour » : comparer `alembic current` à `heads` avant de servir du trafic — **vérif** : base volontairement en retard ⇒ démarrage refusé avec un message explicite, pas un 500 utilisateur.

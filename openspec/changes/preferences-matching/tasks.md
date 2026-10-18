# Tasks — preferences-matching

## 1. Données

- [ ] 1.1 Migration : `ALTER TABLE profiles ADD COLUMN preferences jsonb NOT NULL DEFAULT '{}'` — **vérif** : `alembic upgrade head` puis `downgrade -1` sans erreur, colonne présente.
- [ ] 1.2 Renseigner `profiles.timezone` à l'inscription, validé contre la base IANA — **vérif** : `Europe/Paris` accepté, `Mars/Olympus` ignoré sans erreur.

## 2. API

- [ ] 2.1 `GET/PUT /me/preferences` (jsonb, schéma Pydantic strict) — **vérif** : test, clé inconnue rejetée, défauts renvoyés si vide.
- [ ] 2.2 `PUT /me/matching-criteria` réutilisant les validateurs d'enrôlement — **vérif** : test, 2 intérêts ⇒ 422 avec le même code qu'au wizard.
- [ ] 2.3 `GET /profiles/match-preview` renvoyant le nombre de profils compatibles — **vérif** : test, critères impossibles ⇒ 0.
- [ ] 2.4 Exposer `timezone` dans `GET /matches/{id}` — **vérif** : test, champ présent, valeur IANA.

## 3. Interface

- [ ] 3.1 `/settings/preferences` : densité, taille, furigana auto, mot à mot par défaut, animations — **vérif** : test Vitest, changement applique la classe et appelle l'API.
- [ ] 3.2 Application avant le premier rendu (script inline + `localStorage`) — **vérif** : aucun flash de thème au rechargement (constat manuel consigné).
- [ ] 3.3 `/settings/matching` : langues, niveau, intérêts, quota, visibilité + avertissement `match-preview` — **vérif** : test Vitest, avertissement affiché quand l'aperçu renvoie 0.
- [ ] 3.4 Fil : heure locale du correspondant + salutation calée sur son heure — **vérif** : test Vitest, Tokyo à 2 h ⇒ pas de « Bonjour ».

## 4. Clôture

- [ ] 4.1 `tsc`, `eslint`, `vitest`, `build`, `pytest`, `openspec validate --strict` — **vérif** : six commandes en code 0.

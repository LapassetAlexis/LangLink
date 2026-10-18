# Design — preferences-matching

## Decisions

### D-1 — Préférences en `jsonb` sur `profiles`

Lues à chaque rendu, aucune contrainte relationnelle : `preferences jsonb NOT NULL DEFAULT '{}'`
suffit. Une table clé/valeur imposerait une jointure pour trois valeurs.
Migration : colonne additive, rollback trivial.

### D-2 — Thème et taille appliqués avant le premier rendu

Préférences critiques mises en cache dans `localStorage` et appliquées par un script inline
avant l'hydratation, puis confirmées par l'API. Sinon : flash de thème au chargement.
Alternative écartée : cookies côté serveur, inutilement complexe pour une SPA.

### D-3 — Critères : mêmes validateurs que l'enrôlement

Les endpoints d'édition réutilisent `services/onboarding.py` (3–12 intérêts, règles de
langues). Dupliquer les règles garantirait qu'elles divergent.

### D-4 — Avertissement « aucun profil compatible » calculé côté serveur

`GET /profiles/match-preview` renvoie le nombre de profils compatibles pour des critères
donnés **sans les enregistrer** : seule façon d'avertir avant validation sans deviner.

### D-5 — Fuseau horaire : `profiles.timezone` existait déjà

Colonne présente depuis la migration initiale, jamais exposée ni renseignée. Deux corrections :
la renseigner à l'inscription (`Intl.DateTimeFormat().resolvedOptions().timeZone`), l'exposer
dans `GET /matches/{id}`. Validation serveur contre `zoneinfo.available_timezones()` ; un
fuseau invalide est ignoré, jamais une erreur d'affichage.

## Risks

| Risque | Impact | Mitigation |
|---|---|---|
| Fuseau erroné côté client | Heure fausse | Repli silencieux, « heure inconnue » |
| Critères rendant le profil invisible | Utilisateur isolé | `match-preview` avant validation |
| Migration `preferences` | Réglages perdus si mal écrite | Colonne additive, défaut `{}` |

# Proposal — preferences-matching : préférences d'affichage, critères de matching, heure locale

## Why

Trois manques constatés à l'usage :

1. **Aucune préférence d'affichage** : l'utilisateur ne peut pas régler ce qui le concerne
   personnellement (furigana systématique ou non, mode mot à mot par défaut, densité,
   réduction des animations). Ces réglages existent en CSS mais ne sont pas pilotables.
2. **Les critères de matching ne sont pas éditables** : langues, niveau visé, intérêts et
   quota quotidien sont figés à l'enrôlement. Changer d'objectif impose aujourd'hui de
   repasser par le wizard, qui n'est pas prévu pour ça.
3. **L'heure du correspondant est inconnue** : envoyer « Bonsoir » à Tokyo à 2 h du matin est
   une maladresse que l'application devrait éviter. `profiles.timezone` existe en base depuis
   la migration initiale mais n'est **jamais** exposé ni utilisé.

## What Changes

- **Nouveau** : page `/settings/preferences` — thème de densité, furigana automatique, mode
  mot à mot par défaut, réduction des animations, taille de texte.
- **Nouveau** : page `/settings/matching` — langues et niveau, intérêts (3 à 12), quota
  quotidien de swipes, visibilité du profil.
- **Modifié** : `GET /matches/{id}` expose le `timezone` du correspondant ; le fil affiche son
  heure locale et adapte la salutation proposée à **son** heure, plus à la nôtre.

## Capabilities

### New Capabilities

| Capacité | Périmètre |
|---|---|
| `preferences` | Préférences d'affichage persistées par utilisateur |
| `matching-criteria` | Édition des critères de découverte après l'enrôlement |

### Modified Capabilities

| Capacité | Modification |
|---|---|
| `messaging` | Exigence ajoutée : heure locale du correspondant et salutation adaptée |

## Impact

- `profiles` : colonnes `timezone` (déjà présente) et `preferences` (jsonb, **migration**)
- `backend/app/api/v1/matching/router.py` — exposer `timezone`
- `backend/app/api/v1/onboarding/router.py` — endpoints de préférences
- `frontend/src/features/SettingsPage.tsx` — deux sous-pages

## Risque principal

Éditer ses critères peut rendre un profil invisible (par exemple apprendre une langue que
personne n'apprend). L'interface doit **prévenir** avant d'enregistrer, pas après.

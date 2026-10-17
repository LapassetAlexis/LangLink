# Proposal — niveaux-langue : un niveau lisible par un humain

## Why

Le niveau est stocké et affiché en codes CEFR (`A1`…`C2`). Alexis le relève à l'usage :
« A1 A1 et tout c'est pas parlant pour tout les pays ». C'est exact — le CECR est un
référentiel européen ; un apprenant japonais raisonne en **JLPT (N5→N1)**, un Américain en
`beginner / intermediate / advanced`, et personne ne sait spontanément ce que « B2 » veut
dire hors institution.

Le niveau sert pourtant à deux choses visibles : l'auto-positionnement à l'enrôlement, et
la **compatibilité de niveau** dans le score d'affinité (30 % du score). Un niveau mal
compris produit un mauvais appariement.

## What Changes

- **Nouveau** : affichage du niveau par un **libellé dans la langue de l'interface**
  (`Débutant`, `Intermédiaire`, `Confirmé`, `Avancé`, `Maîtrise`), le code CEFR restant
  disponible en second plan (infobulle).
- **Nouveau** : échelle de niveau **par langue cible** — pour le japonais, les libellés
  JLPT (N5→N1) sont proposés, avec correspondance documentée vers l'échelle interne.
- **Modifié** : l'écran d'enrôlement et les réglages affichent les libellés, pas les codes.
- **Modifié** : le calcul de compatibilité de niveau continue de s'appuyer sur un rang
  numérique 1–6 : **aucune migration de données**, la valeur stockée ne change pas.

## Hors périmètre

- Remplacer le stockage CEFR par une échelle maison : coût de migration, et perte d'un
  standard interopérable (Europass, dossiers scolaires).
- Ajouter un test de niveau certifié (JLPT officiel, DELF) : c'est un parcours de
  certification, pas une case à cocher.

## Impact

- `frontend/src/lib/levels.ts` (nouveau), `pages.tsx`, `SettingsPage.tsx`
- `backend/app/services/onboarding.py` — table de correspondance exposée par l'API
- Aucune migration : `profiles.target_level` conserve `A1`…`C2`

## Décision à valider

Le point « **Maternelle** » de la proposition est **écarté** : on ne choisit pas sa langue
maternelle comme *niveau d'apprentissage*. Si c'est votre langue maternelle, vous ne
l'apprenez pas — et le matching repose précisément sur la réciprocité
« j'apprends ta langue / tu apprends la mienne ». « Maîtrise » (C2) couvre le cas
« je parle presque comme un natif » sans contredire le modèle.

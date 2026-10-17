# Proposal — ui-refinements : cinq finitions issues de l'usage réel

## Why

Alexis a utilisé l'application avec un compte réel et un correspondant japonais. Cinq
manques sautent aux yeux, tous du côté de l'usage quotidien plutôt que du socle :

1. les **icebreakers** s'affichent en français pour un utilisateur français — donc dans une
   langue qu'il n'apprend pas, alors que l'intérêt est précisément de les lire en japonais ;
2. la **liste des conversations** ne dit ni quand le dernier message est arrivé, ni l'état du
   fil ;
3. il n'y a **aucun accès au profil ni aux réglages** une fois connecté ;
4. l'inscription ne demande **qu'une seule fois** le mot de passe (risque de faute de frappe
   irréversible) ;
5. la traduction est **tout-ou-rien** : impossible de demander le sens d'un mot précis.

## What Changes

- **Nouveau** : icebreakers affichés dans la langue du correspondant, avec bascule vers le
  français et cache de traduction.
- **Modifié** : boîte de réception — date relative du dernier message et statut du fil.
- **Nouveau** : menu de compte et écran `/settings` (profil, langues, intérêts, blocages,
  déconnexion, suppression de compte).
- **Modifié** : inscription — double saisie du mot de passe avec contrôle de concordance.
- **Nouveau (spécifié, non implémenté)** : aide lexicale au clic sur un mot — voir la
  réserve technique dans `design.md` (D-4) : un moteur de traduction ne fournit pas
  plusieurs sens, il faut un dictionnaire.

## Capabilities

### New Capabilities

| Capacité | Périmètre |
|---|---|
| `lexical-aid` | Aide au mot : segmentation, sens multiples, romanisation |

### Modified Capabilities

| Capacité | Modification |
|---|---|
| `icebreakers` | Exigence ajoutée : affichage dans la langue du correspondant + bascule |
| `messaging` | Exigence ajoutée : métadonnées de liste (date, statut) |
| `identity` | Exigence ajoutée : double saisie du mot de passe à l'inscription |
| `safety` | Exigence ajoutée : accès aux réglages de compte |

## Impact

- `frontend/src/features/pages.tsx` — inbox, fil, icebreakers, chat
- `frontend/src/app/App.tsx` — menu de compte, route `/settings`
- `frontend/src/lib/api.ts` — `translateText`, réglages
- `backend/app/api/v1/language/router.py` — rien à changer (le texte libre est déjà accepté)
- Aucune migration de base : les données existantes suffisent.

## Hors périmètre

- Notifications email ou push.
- Refonte complète du wizard (change `ui-refonte`, tâche 3.1).

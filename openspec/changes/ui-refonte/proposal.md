# Proposal — ui-refonte : identité visuelle et cohérence des écrans

## Why

Le MVP est fonctionnel (77 tests backend, 11 tests d'interface) mais son apparence est celle
d'un squelette de développement : palette bleue Tailwind par défaut, cartes plates, titres
en sans-serif, aucun état visuel soigné. Pour un produit dont la promesse est **l'échange
humain**, une interface générique contredit le positionnement et décourage l'inscription.

Ce changement introduit une identité visuelle assumée et un système de composants partagé,
afin que chaque écran à venir hérite de la même qualité sans réinventer son style.

## What Changes

- **Nouveau** : système de design centralisé — tokens de couleur, typographie (serif display
  + sans-serif texte), rayons, ombres, halos de fond, primitives `.surface`, `.btn-primary`,
  `.btn-ghost`, `.field`, `.chip`, `.chip-on`, `.bubble-them`.
- **Nouveau** : identité « éditorial chaleureux » — fond encre, accent ambre/sable, halos
  ambre/turquoise/rose, évocation d'une correspondance plutôt que d'un tableau de bord.
- **Modifié** : page d'accueil (hero, carte de profil flottante, 3 étapes, bandeau de
  chiffres), écrans d'authentification (split-screen avec citation), carte de découverte
  (anneau de score en `conic-gradient`), lignes de boîte de réception, bulles du fil.
- **Modifié** : accessibilité renforcée — focus visible ambre, respect de
  `prefers-reduced-motion`, contrastes AA sur texte principal.
- **Régularisation** : cette refonte a d'abord été implémentée directement sur `main`
  (commit `7d463f3`) hors du flux OpenSpec. Ce change la spécifie rétroactivement et
  transforme les écrans non traités en tâches suivies.

Aucun changement d'API, aucune rupture de contrat : uniquement de la présentation.

## Capabilities

### New Capabilities

| Capacité | Périmètre |
|---|---|
| `design-system` | Tokens, typographie, primitives de composants, accessibilité visuelle, états |

### Modified Capabilities

Aucune. Les specs métier (`identity`, `onboarding`, `discovery`, `messaging`…) sont
inchangées : seule la couche de présentation évolue.

## Impact

- `frontend/src/styles/index.css` — tokens et primitives
- `frontend/tailwind.config.js` — palette `brand` réalignée sur l'ambre
- `frontend/index.html` — polices, `theme-color`, titre
- `frontend/src/app/App.tsx` — accueil et authentification
- `frontend/src/features/pages.tsx` — découverte, inbox, fil
- Aucun impact backend, aucune migration, aucun changement d'API.

## Hors périmètre

- Refonte des écrans d'enrôlement et du panneau de correction (tâches suivies dans ce change).
- Photographies ou illustrations : la direction repose sur la typographie et la couleur.
- Mode clair : le thème sombre reste l'unique thème en V1.

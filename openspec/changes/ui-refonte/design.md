# Design — ui-refonte

## Context

L'application est fonctionnelle mais visuellement neutre : palette Tailwind par défaut
(bleu `brand-600`), cartes `border-slate-800` sans profondeur, titres en sans-serif, états
vides minimaux. Le produit promet un échange **humain** ; l'interface doit le dire avant
qu'on lise une ligne de texte.

Contraintes : SPA React + Tailwind 3 déjà en place, aucune dépendance UI lourde (pas de
bibliothèque de composants), thème sombre unique en V1, cible mobile-first 360 px.

## Goals / Non-Goals

**Goals**

- Une identité reconnaissable en une seconde : encre + ambre + serif d'affichage.
- Un socle de primitives réutilisables, pour que les écrans restants (wizard, correction,
  overlay de match) n'aient plus qu'à composer.
- Accessibilité non négociable : focus visible, `prefers-reduced-motion`, contraste AA.
- Zéro régression fonctionnelle : les 11 tests d'interface existants doivent continuer à
  passer sans adaptation de comportement.

**Non-Goals**

- Mode clair (thème unique assumé en V1).
- Illustrations ou photographies : la direction repose sur typographie + couleur + halos.
- Bibliothèque de composants externe (Radix, shadcn) : surdimensionné pour 6 primitives.
- Refonte du parcours fonctionnel : aucune route, aucun appel d'API ne change.

## Decisions

### D-1 — Tokens CSS plutôt que classes utilitaires éparpillées

Les couleurs vivent dans `:root` (`--ink-900`, `--amber-400`, `--sand-100`…) et sont
exposées à Tailwind par la palette `brand`. Raison : changer l'accent doit être une édition
d'une ligne, pas une chasse dans 20 fichiers. Conséquence assumée : les modificateurs
d'opacité Tailwind (`/80`) ne s'appliquent pas aux couleurs arbitraires `var(...)` — deux
builds ont échoué dessus, la règle est donc : pas d'opacité sur `bg-[color:var(--…)]`.

Alternative écartée : un fichier `theme.ts` consommé par `styled-components`. Introduirait
un runtime CSS-in-JS pour un gain nul sur 6 primitives.

### D-2 — Deux familles typographiques, chargées depuis Google Fonts

`Fraunces` (serif, optique variable) pour les titres, `Inter` pour le texte. Chargement par
`<link>` avec `preconnect`, et piles de repli déclarées pour le cas hors-ligne
(`Georgia`, `system-ui`). Alternative écartée : auto-héberger les fontes — 2 fichiers de
plus à gérer dans l'image nginx pour un gain de latence marginal sur un LAN.

### D-3 — Primitives en `@layer components`, pas en composants React

Six classes CSS (`.surface`, `.btn-primary`, `.btn-ghost`, `.field`, `.chip`, `.chip-on`,
`.bubble-them`) plutôt que six composants React. Raison : elles s'appliquent à des éléments
sémantiques variés (`<article>`, `<button>`, `<input>`) sans imposer une hiérarchie de
props, et restent lisibles dans le DOM. Limite connue : `@apply` d'une classe composant
dans une autre est refusé par Tailwind — les utilitaires de base sont donc dupliqués dans
`.btn-primary` et `.btn-ghost`.

### D-4 — Anneau de score en `conic-gradient`

Le score d'affinité (0–100) est l'information la plus utile de la carte de découverte. Un
anneau CSS pur (`conic-gradient`) le rend lisible d'un coup d'œil, sans SVG ni librairie de
graphiques. Accessible via `aria-label` explicite (« Affinité 63 sur 100 »).

### D-5 — Halos plutôt qu'images de fond

Trois `radial-gradient` en `position: fixed` sur `body::before`, en ambre/turquoise/rose.
Coût : 0 octet d'image, aucun impact sur le LCP. Alternative écartée : une image de fond
floutée (300 Ko, et un rendu différent selon l'écran).

### D-6 — Régularisation a posteriori assumée

La refonte a d'abord été implémentée sur `main` sans change OpenSpec. Ce document la
spécifie rétroactivement : les décisions ci-dessus décrivent le code existant (commit
`7d463f3`), et les écrans non traités deviennent des tâches de ce change. C'est un écart de
méthode reconnu, pas un précédent : tout changement futur d'apparence passe par un change.

## Risks / Trade-offs

| Risque | Impact | Mitigation |
|---|---|---|
| Police distante indisponible | Titres en Georgia, moins d'identité | Piles de repli déclarées, pas de décalage de mise en page bloquant |
| `conic-gradient` non supporté (vieux navigateurs) | Score illisible | Le chiffre reste affiché au centre, seule la jauge disparaît |
| Halos en `position: fixed` | Coût de composition sur mobile bas de gamme | `pointer-events: none`, pas d'animation, testé à 360 px |
| Duplication d'utilitaires dans `.btn-*` | Maintenance | Commentée dans le CSS, la règle est unique et documentée |
| Refonte partielle | Incohérence visuelle entre écrans traités et non traités | Les écrans restants sont des tâches explicites de ce change |

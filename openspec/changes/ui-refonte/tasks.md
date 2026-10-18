# Tasks — ui-refonte

> Chaque tâche porte son critère de vérification. Une case n'est cochée que si ce critère a
> été exécuté. Références : `specs/design-system/spec.md`, `design.md`.

## 1. Socle de design

- [x] 1.1 Déclarer les tokens CSS (`--ink-*`, `--sand-*`, `--amber-*`, `--teal-*`, `--rose-*`) dans `:root` — **vérif** : `grep -c '^  --' src/styles/index.css` ≥ 8, aucune valeur hexadécimale dans un `.tsx`.
- [x] 1.2 Réaligner la palette Tailwind `brand` sur l'ambre (`#f0b357` → `#a86c24`) et déclarer `fontFamily.display` — **vérif** : `npm run build` passe et `bg-brand-600` rend de l'ambre.
- [x] 1.3 Charger `Fraunces` + `Inter` avec `preconnect` et piles de repli — **vérif** : `index.html` contient les deux `preconnect` ; `.display` déclare `Georgia` en secours.
- [x] 1.4 Écrire les primitives `.surface`, `.btn-primary`, `.btn-ghost`, `.field`, `.chip`, `.chip-on`, `.bubble-them` dans `@layer components` — **vérif** : `npm run build` sans erreur PostCSS ; les 7 classes existent.
- [x] 1.5 Poser les halos de fond diffus et l'animation `rise` avec garde `prefers-reduced-motion` — **vérif** : `grep -q 'prefers-reduced-motion' src/styles/index.css`.

## 2. Écrans refondus

- [x] 2.1 Accueil : hero, carte de profil flottante inclinée, 3 étapes numérotées, bandeau de chiffres, pied de page — **vérif** : `npm run build` + `vitest` (test « proposition de valeur ») verts.
- [x] 2.2 Authentification : split-screen citation / formulaire, états `busy` et `alert` stylés — **vérif** : `tsc --noEmit` et `eslint` verts.
- [x] 2.3 Découverte : carte `.surface`, anneau de score `conic-gradient` avec `aria-label`, chips d'intérêts, boutons pilules — **vérif** : test « un like appelle swipe une seule fois » toujours vert.
- [x] 2.4 Boîte de réception : lignes en surface avec survol, badge de non-lus — **vérif** : test « badge de non-lus » vert.
- [x] 2.5 Fil : bulles `.bubble-them`, champ `.field`, bouton d'envoi pilule — **vérif** : tests « traduction » et « furigana » verts.

## 3. Écrans restants (à faire)

- [ ] 3.1 Wizard : reprendre la barre de progression (segments arrondis, étape courante contrastée, libellés 1-2-3) et les tuiles de catégories — **vérif** : test Vitest « compteur n/12 » vert + capture à 360 px sans débordement.
- [ ] 3.2 Wizard étape 3 : zone photo (glisser-déposer, aperçu circulaire) et compteur de bio — **vérif** : composant monté avec un fichier factice, aperçu rendu.
- [ ] 3.3 Panneau de correction : mettre en forme le fragment figé, le champ de remplacement et les boutons Accepter/Refuser avec les primitives — **vérif** : test « Accepter » vert, panneau visible dans le flux du message.
- [ ] 3.4 Overlay de match : deux avatars, score, intérêts communs, CTA — **vérif** : test Vitest sur un swipe renvoyant un match non nul.
- [ ] 3.5 États vides et chargements : composant `EmptyState` (titre, texte, action) et `Skeleton` réutilisables — **vérif** : 3 écrans (découverte, inbox, fil) utilisent le même composant.
- [x] 3.7 Remplacer les codes de langue par un drapeau + libellé partout (carte de découverte, boîte de réception, en-tête du fil, sélecteurs du wizard, carte d'accueil) — **vérif** : composant `LanguagePair` unique, 5 points d'affichage migrés, `aria-label` explicite, `tsc`/`eslint`/`vitest` verts.
- [x] 3.8 Remplacer les drapeaux emoji par des SVG vectoriels (`country-flag-icons`, 13 composants tree-shakés) — **vérif** : `npm run build` vert, +18 Ko de JS pour 13 drapeaux, `tsc`/`eslint`/`vitest` verts, rendu identique sous Windows.
- [ ] 3.6 Écran de réglages : profil, langues, intérêts, blocages, suppression de compte — **vérif** : route `/settings` accessible depuis le fil, formulaire prérempli.

## 4. Qualité et accessibilité

- [ ] 4.1 Vérifier le contraste AA (≥ 4.5:1) du texte courant et des libellés secondaires — **vérif** : mesure documentée dans ce dossier (`contrast.md`) pour 4 paires texte/fond.
- [ ] 4.2 Vérifier l'absence de défilement horizontal à 360 px sur les 5 écrans — **vérif** : capture ou test jsdom à 360 px, `scrollWidth <= clientWidth`.
- [ ] 4.3 Parcours clavier complet : tabulation visible sur accueil, auth, wizard, découverte, fil — **vérif** : test Vitest « focus » sur 2 écrans + revue manuelle consignée.
- [ ] 4.4 Documenter la direction visuelle dans `frontend/README.md` (palette, typo, primitives) — **vérif** : le fichier liste les 7 primitives et la règle « pas d'opacité sur `var()` ».

## 6. Coquille applicative et messagerie

- [x] 6.1 Coquille commune `AppShell` : en-tête collant, navigation (Découvrir / Messages / Mon compte), largeur bornée sur les formulaires — **vérif** : ✅ 3 vues authentifiées utilisent la même coquille, `tsc`/`lint`/`build` verts.
- [x] 6.2 Liste de conversations : avatar à initiale, aperçu, heure relative, badge de non-lus, état vide avec action, colonne latérale éditoriale en `lg` — **vérif** : ✅ plus de lien bleu par défaut, aucune zone morte > 50 % sur écran large.
- [x] 6.3 Tiroir d'assistance à la traduction dans le fil (`AssistDock`) : pastille repliée, saisie libre, traduction déterministe, mention du moteur, insertion dans le message — **vérif** : ✅ composant isolé, aucun modèle de langage, `tsc`/`lint`/`build` verts, 16 tests inchangés.

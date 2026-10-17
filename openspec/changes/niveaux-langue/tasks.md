# Tasks — niveaux-langue

## 1. Socle

- [ ] 1.1 Créer `frontend/src/lib/levels.ts` : échelle générique (6 rangs) + surcharges par langue cible (`ja` → N5…N1), avec `levelLabel(code, lang)` et `levelOptions(lang)` — **vérif** : test unitaire, `levelLabel('B1','ja')` ⇒ `N3`, `levelLabel('B1','fr')` ⇒ « Intermédiaire ».
- [ ] 1.2 Exposer la même correspondance côté API (`GET /language/levels` ou constante documentée) — **vérif** : réponse JSON listant les échelles par langue.

## 2. Affichage

- [ ] 2.1 Wizard : boutons de niveau avec libellé principal, code CEFR en infobulle, deux entrées « Débutant » (A1) et « Débutant avancé » (A2) — **vérif** : test Vitest, les 6 codes restent atteignables, aucun code affiché en texte principal.
- [ ] 2.2 Réglages : même rendu que le wizard, valeur courante correctement pré-sélectionnée — **vérif** : test Vitest avec un profil `B2` ⇒ « Confirmé » actif.
- [ ] 2.3 Cartes de découverte et en-tête du fil : afficher le libellé (« niveau Confirmé ») au lieu du code — **vérif** : capture ou test, plus aucun `A1`/`B2` brut à l'écran.

## 3. Vérifications

- [ ] 3.1 Le score de compatibilité est inchangé sur les paires existantes — **vérif** : test `affinity_score` rejoué, valeur 63 conservée.
- [ ] 3.2 `tsc`, `eslint`, `vitest`, `npm run build` + `pytest` verts — **vérif** : cinq commandes en code 0.

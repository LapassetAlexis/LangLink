# Tasks — ui-refinements

## 1. Identité : double saisie du mot de passe

- [ ] 1.1 Ajouter un champ « Confirmer le mot de passe » à l'inscription, avec contrôle de concordance côté client — **vérif** : test Vitest, saisies différentes ⇒ requête non envoyée et message affiché ; identiques ⇒ un seul appel.

## 2. Liste des conversations : date et statut

- [ ] 2.1 Afficher la date relative du dernier message (`il y a 5 min`, `hier`, date courte au-delà de 7 jours), horodatage absolu en `title` — **vérif** : test Vitest sur 3 dates (5 min, hier, il y a 2 mois).
- [ ] 2.2 Afficher le statut du fil (`active` / `unmatched` / `blocked`) et masquer le compteur de non-lus si le fil est fermé — **vérif** : test Vitest avec un fil `blocked` ⇒ badge absent, libellé « conversation fermée ».

## 3. Compte et réglages

- [ ] 3.1 Menu de compte dans l'en-tête des vues authentifiées (initiale, lien Réglages, Déconnexion) — **vérif** : test Vitest, clic sur Déconnexion ⇒ `setToken(null)` appelé et retour à `/`.
- [ ] 3.2 Route `/settings` avec 5 blocs : profil, langues, intérêts, blocages, suppression de compte — **vérif** : formulaire prérempli depuis `GET /me/profile`, enregistrement appelle l'endpoint correspondant.
- [ ] 3.3 Suppression de compte depuis les réglages, avec confirmation par mot de passe — **vérif** : test, mot de passe erroné ⇒ 422 affiché, compte intact.

## 4. Icebreakers dans la langue du correspondant

- [x] 4.1 Étendre `api` avec `translateText(text, source, target)` — **vérif** : typecheck + test unitaire du client (URL et corps de requête). — **vérif** : ✅ `translateText` ajouté au client, `tsc` vert.
- [x] 4.2 Afficher la question dans `other.native_language` **par défaut** (traduction automatique à l'ouverture du fil), avec bascule « voir en français » et cache en mémoire — **vérif** : ✅ effet de traduction des 3 questions au montage, `shown = traduit ?? original`, bascule vers l'original sans nouvel appel.
- [ ] 4.3 Repli non bloquant si la traduction échoue — **vérif** : test, provider en erreur ⇒ question d'origine + mention, aucune exception.

## 5. Aide au mot (mode « mot à mot »)

- [x] 5.1 Bouton « mot à mot » par message reçu : segmentation par espaces pour les écritures latines, par tokens pour le japonais — **vérif** : test, un message japonais produit des tokens alignés sur les offsets de l'API. — **vérif** : ✅ mode « mot à mot » par message : japonais segmenté via `readingAid` (aligné sur les offsets de l'API), latin par espaces, retour au texte normal au second clic — test Vitest.
- [x] 5.2 Panneau d'aide au clic : sens (via `/language/translate`), lecture + romaji pour le japonais, mention explicite « traduction automatique, sens unique » — **vérif** : test Vitest, clic sur un mot affiche le panneau avec la mention. — **vérif** : ✅ panneau au clic : sens multiples numérotés avec catégorie, lecture kana + romaji pour le japonais, mention « Source : Wiktionnaire francophone » ou absence de sens — test Vitest (appel `lexicon('marché','fr')` + définition affichée).
- [x] 5.3 Backend : `POST /language/lexicon` — récupérer le wikitext via `action=parse`, extraire les lignes `#`, nettoyer les liens `[[…]]`, renvoyer `{part_of_speech, definition}[]` + lecture/romaji si `ja` — **vérif** : test « marché » ⇒ ≥ 2 sens avec catégorie ; « 学生 » ⇒ sens + reading. — **vérif** : ✅ `POST /language/lexicon` livré : wikitext `action=parse`, lignes `#`, exemples `#*` exclus, déduplication, cache mémoire borné — 4 tests, vérifié en production (« marché » 6 sens, « 学生 » 2 sens + がくせい/gakusei).
- [x] 5.4 Trancher la source lexicale multi-sens (design D-4) — **vérif** : ✅ REST du Wiktionnaire hors service (`501`), `action=parse` + wikitext `#` retenu, vérifié sur « marché » et « 学生 ».

## 6. Clôture

- [x] 6.1 `tsc`, `eslint`, `vitest`, `npm run build` verts — **vérif** : quatre commandes en code 0. — **vérif** : ✅ `tsc`, `eslint`, `vitest` (11 tests) et `npm run build` en code 0.
- [x] 6.2 `openspec validate --all --strict` — **vérif** : 0 échec. — **vérif** : ✅ `openspec validate --all --strict` : 3 changes, 0 échec.
- [x] 6.3 Test anti-régression du déploiement : le moteur de traduction doit être déclaré dans `deploy/stack.yml` et l'URL de l'API doit pointer vers un service existant — **vérif** : ✅ `tests/test_deploy_contract.py` (3 tests), né du 503 de production où les tests mockaient le fournisseur.

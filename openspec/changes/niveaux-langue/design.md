# Design — niveaux-langue

## Context

`profiles.target_level` est un `text` contraint à `A1…C2`, utilisé par le score d'affinité
via un `CASE ... THEN 1..6` en SQL. Le frontend affiche ces codes dans le wizard, les
réglages et les cartes de découverte.

## Decisions

### D-1 — Le stockage ne change pas

On garde `A1…C2` en base. Raison : c'est une échelle ordonnée, interopérable, déjà
contrainte, et sur laquelle la compatibilité est calculée en SQL. Changer le stockage
imposerait une migration, une reprise de données, et la réécriture du `CASE` de scoring —
pour un gain purement cosmétique.

Alternative écartée : stocker `beginner…mastery`. Perte du standard, migration inutile.

### D-2 — Cinq libellés pour six codes

| Libellé | Codes couverts |
|---|---|
| Débutant | A1, A2 |
| Intermédiaire | B1 |
| Confirmé | B2 |
| Avancé | C1 |
| Maîtrise | C2 |

A1 et A2 sont fusionnés à l'affichage : la distinction « faux débutant / élémentaire » n'a
de sens que pour un examinateur. En interne, la différence reste prise en compte dans le
score (rangs 1 et 2).

Conséquence assumée : choisir « Débutant » enregistre `A1`. Si l'on veut préserver A2, il
faut deux entrées distinctes — d'où les libellés « Débutant » et « Débutant avancé »
proposés à l'implémentation (voir tâche 2.1).

### D-3 — Référentiel par langue cible

Un module `levels.ts` (frontend) et une table de correspondance (backend,
`services/onboarding.py`) exposent pour chaque langue cible un jeu d'options :

```ts
{ code: 'ja', labels: [['N5','A1'],['N4','A2'],['N3','B1'],['N2','B2'],['N1','C1']] }
```

La correspondance JLPT → CEFR est **approximative** et doit être présentée comme telle :
le JLPT mesure la compréhension, pas la production orale, là où le CECR évalue les deux.
On l'affiche comme une aide au positionnement, jamais comme une équivalence officielle.

### D-4 — « Maternelle » écarté

Proposé par Alexis, refusé : un niveau « maternelle » contredit la réciprocité du matching
(je n'apprends pas ma propre langue). `Maîtrise` (C2) couvre le besoin exprimé.

## Risks / Trade-offs

| Risque | Impact | Mitigation |
|---|---|---|
| Correspondance JLPT/CEFR approximative | Positionnement erroné | Mention « équivalence indicative » dans l'interface |
| Fusion A1/A2 | Perte de granularité perçue | Deux entrées d'affichage, un seul code possible chacune |
| Libellés non traduits (i18n futures) | Incohérence | Les libellés vivent dans `levels.ts`, pas dans les composants |

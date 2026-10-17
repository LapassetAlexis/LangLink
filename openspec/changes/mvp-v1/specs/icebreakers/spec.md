# Spec Delta — icebreakers

## Purpose

Selection deterministe de trois questions brise-glace issues du catalogue statique, rattachees aux interets communs et persistees a la creation du match.

## ADDED Requirements

### Requirement: [REQ-ICE-01] Trois questions issues des intérêts communs
Le système SHALL sélectionner exactement 3 questions du catalogue statique, chacune
rattachée à un intérêt commun distinct si possible, et les persister à la création du match.

#### Scenario: Intérêts communs suffisants
- **WHEN** A et B partagent `jeux-rpg`, `cuisine-patisserie` et `lecture-manga`
- **THEN** les 3 icebreakers couvrent ces 3 intérêts
- **AND** aucune question n'est dupliquée

#### Scenario: Un seul intérêt commun
- **WHEN** l'intersection ne contient qu'un intérêt
- **THEN** les 3 questions proviennent de cet intérêt, sans répétition
- **AND** la génération reste déterministe pour ce match (hash de `match_id`)

#### Scenario: Stabilité dans le temps
- **WHEN** l'utilisateur recharge le fil une semaine plus tard
- **THEN** les icebreakers affichés sont identiques (persistés, jamais régénérés)

# Spec Delta — discovery

## Purpose

Interface de decouverte : exposition des seuls profils linguistiquement reciproques, exclusions (swipes, blocages, suspendus), quota quotidien et annulation bornee du dernier swipe.

## ADDED Requirements

### Requirement: [REQ-DSC-01] Réciprocité stricte du feed
Le système SHALL n'exposer que les profils dont la paire linguistique est réciproque
avec celle du demandeur.

#### Scenario: Candidat non réciproque
- **WHEN** A est `fr→ja` et B est `ja→es`
- **THEN** B n'apparaît jamais dans le feed de A
- **AND** aucune entrée de cache ne contient B pour A

#### Scenario: Paires réciproques multiples
- **WHEN** A est `fr→ja` et B est `ja→fr`
- **THEN** B est éligible pour A et A est éligible pour B


### Requirement: [REQ-DSC-02] Exclusions du feed
Le système SHALL exclure du feed : soi-même, les profils déjà swipés, les profils
bloqués dans un sens ou l'autre, les comptes non découvrables ou suspendus.

#### Scenario: Profil déjà passé
- **WHEN** A a déjà `pass` sur B
- **THEN** B n'est plus proposé à A, même après redémarrage du client

#### Scenario: Blocage croisé
- **WHEN** B a bloqué A
- **THEN** A ne voit plus B dans son feed
- **AND** toute tentative de swipe de A vers B renvoie `403 safety.blocked`


### Requirement: [REQ-DSC-03] Quota quotidien de découverte
Le système SHALL limiter à 20 profils **nouveaux** par jour et par utilisateur, les profils
déjà servis mais non swipés n'étant pas recomptés.

#### Scenario: Quota atteint
- **WHEN** l'utilisateur a swipé 20 profils dans la journée
- **THEN** le feed renvoie `items: []` et `next_cursor: null`
- **AND** l'UI affiche un état « revenez demain » plutôt qu'une erreur


### Requirement: [REQ-DSC-04] Rewind borné
Le système SHALL permettre d'annuler le dernier swipe au plus une fois par heure.

#### Scenario: Second rewind
- **WHEN** l'utilisateur tente un second rewind dans l'heure
- **THEN** l'API renvoie `429 rate.limited` avec `Retry-After`

---

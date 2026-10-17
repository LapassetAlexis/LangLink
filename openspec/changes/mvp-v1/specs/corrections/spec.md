# Spec Delta — corrections

## Purpose

Correcteur collaboratif : suggestions localisees par offsets sur un message recu, acceptees ou refusees par l'auteur, sans jamais modifier le corps d'origine.

## ADDED Requirements

### Requirement: [REQ-COR-01] Suggestion localisée
Le système SHALL valider que la plage `[start_offset, end_offset)` est incluse dans le
corps du message et que `original_text` correspond exactement au fragment ciblé.

#### Scenario: Plage invalide
- **WHEN** `end_offset` dépasse la longueur du corps
- **THEN** l'API renvoie `422 correction.invalid_range`
- **AND** aucune correction n'est créée

#### Scenario: Auto-correction interdite
- **WHEN** l'auteur d'un message tente de le corriger lui-même
- **THEN** l'API renvoie `422 correction.own_message`

#### Scenario: Chevauchement de suggestions
- **WHEN** une suggestion `pending` chevauche déjà la plage demandée
- **THEN** l'API renvoie `409 correction.conflict` avec l'identifiant de la suggestion existante


### Requirement: [REQ-COR-02] Décision de l'auteur
Le système SHALL réserver l'acceptation et le refus à l'auteur du message, et rendre la
décision définitive.

#### Scenario: Acceptation
- **WHEN** l'auteur accepte une correction `pending`
- **THEN** `status = accepted`, `resolved_at` est renseigné
- **AND** le message affiché contient le fragment remplacé (calcul à la volée)
- **AND** `messages.body` reste inchangé en base

#### Scenario: Correction devenue obsolète
- **WHEN** l'auteur édite le message et que les offsets ne correspondent plus
- **THEN** la correction passe automatiquement à `stale`
- **AND** elle n'est plus proposée à l'acceptation

#### Scenario: Décision par un tiers
- **WHEN** le correcteur tente d'accepter sa propre suggestion
- **THEN** l'API renvoie `403` et le statut reste `pending`


### Requirement: [REQ-COR-03] Traçabilité de la correction
Le système SHALL conserver l'original, le remplacement, l'auteur de la suggestion et la
décision, et exposer les deux versions à l'affichage.

#### Scenario: Vue auteur après acceptation
- **WHEN** l'auteur accepte la suggestion `"je suis allé"` → `"je suis allée"`
- **THEN** le message affiche la version corrigée avec un marqueur visuel
- **AND** un clic sur le marqueur affiche le texte d'origine et l'explication

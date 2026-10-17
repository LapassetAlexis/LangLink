# Spec Delta — matching

## Purpose

Moteur de matching : score d'affinite explicable, creation atomique du match sur like mutuel, fermeture unilaterale du match.

## ADDED Requirements

### Requirement: [REQ-MAT-01] Score d'affinité explicable
Le système SHALL calculer un score entier 0–100 à partir des intérêts communs et de la
proximité de niveau, et l'exposer pour rendre le classement compréhensible.

Formule normative :
```
overlap    = |Ia ∩ Ib| / min(|Ia|, |Ib|)          # couverture du plus petit profil
jaccard    = |Ia ∩ Ib| / |Ia ∪ Ib|                # similarité globale
level_fit  = 1 - |niveau(A) - niveau(B)| / 5      # A1=1 … C2=6
score      = round(100 * (0.5*overlap + 0.3*jaccard + 0.2*level_fit))
```

#### Scenario: Trois intérêts communs sur cinq
- **WHEN** A a 5 intérêts, B en a 5, dont 3 communs, et tous deux sont B1
- **THEN** `overlap = 0.6`, `jaccard = 0.4286`, `level_fit = 1`
- **AND** le score renvoyé vaut `63`  (100 × (0.5×0.6 + 0.3×0.4286 + 0.2×1) = 62.86 → 63)

#### Scenario: Aucun intérêt commun
- **WHEN** l'intersection est vide
- **THEN** le score vaut au plus `20` (seul `level_fit` contribue)
- **AND** le candidat est relégué après tous ceux ayant au moins un intérêt commun


### Requirement: [REQ-MAT-02] Création du match sur like mutuel
Le système SHALL créer un match atomiquement lors du second like et générer dans la même
transaction les 3 icebreakers.

#### Scenario: Like réciproque
- **WHEN** A like B alors que B avait déjà liké A
- **THEN** la réponse `201` contient `match` avec `affinity_score`
- **AND** 3 icebreakers sont persistés et renvoyés
- **AND** le match apparaît dans `GET /matches` des deux utilisateurs

#### Scenario: Like non réciproque
- **WHEN** A like B et B n'a encore rien décidé
- **THEN** la réponse `201` a `match: null`
- **AND** B ne reçoit aucune notification de type « quelqu'un t'a liké »


### Requirement: [REQ-MAT-03] Dématch
Le système SHALL permettre à un membre de fermer définitivement un match.

#### Scenario: Dématch unilatéral
- **WHEN** A appelle `DELETE /matches/{id}`
- **THEN** `status = unmatched` et le fil devient accessible en lecture seule
- **AND** l'envoi de message renvoie `409 match.closed`
- **AND** les swipes restent en base : aucun nouveau match ne peut se former


### Requirement: [REQ-MAT-04] Déterminisme du classement
Le système SHALL produire un ordre stable pour un même utilisateur et une même journée,
afin d'éviter le scintillement du feed entre deux rafraîchissements.

#### Scenario: Deux appels successifs
- **WHEN** le client appelle deux fois `GET /discovery/feed` dans la même journée sans swipe
- **THEN** les deux réponses ont le même ordre

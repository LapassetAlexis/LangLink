# Spec Delta — matching-criteria

## ADDED Requirements

### Requirement: [REQ-MTC-01] Critères de matching éditables

Le système SHALL permettre de modifier langues, niveau, intérêts et visibilité après
l'enrôlement, avec les mêmes règles de validation qu'à la création.

#### Scenario: Changement de langue apprise
- **WHEN** l'utilisateur remplace le japonais par l'espagnol
- **THEN** le feed ne contient plus que des hispanophones apprenant sa langue
- **AND** les matchs existants restent accessibles

#### Scenario: Validation identique au wizard
- **WHEN** l'utilisateur ne garde que 2 intérêts
- **THEN** l'enregistrement est refusé avec le même motif qu'à l'enrôlement
- **AND** les critères précédents restent actifs

### Requirement: [REQ-MTC-02] Avertissement avant de se rendre invisible

Le système SHALL avertir lorsque les critères ne peuvent produire aucun résultat, **avant**
d'enregistrer.

#### Scenario: Aucun profil compatible
- **WHEN** les critères choisis ne correspondent à aucun profil découvrable
- **THEN** un avertissement explicite s'affiche avant validation
- **AND** l'utilisateur peut revenir en arrière sans perdre sa saisie

### Requirement: [REQ-MTC-03] Quota de découverte réglable

Le système SHALL permettre d'ajuster le nombre de swipes quotidiens dans une plage bornée.

#### Scenario: Réduction du quota
- **WHEN** l'utilisateur abaisse son quota de 20 à 10
- **THEN** le feed s'arrête à 10 profils le jour même
- **AND** la valeur ne peut pas dépasser le plafond serveur

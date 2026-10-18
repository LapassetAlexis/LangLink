# Spec Delta — messaging

## ADDED Requirements

### Requirement: [REQ-MSG-08] Heure locale du correspondant

Le système SHALL afficher l'heure locale du correspondant dans le fil et adapter la
salutation proposée à cette heure, non à celle du lecteur.

#### Scenario: Décalage horaire
- **WHEN** il est 19 h à Paris et 2 h du matin à Tokyo
- **THEN** le fil indique l'heure de Tokyo
- **AND** aucune salutation du matin n'est proposée à 2 h du matin

#### Scenario: Fuseau inconnu
- **WHEN** le fuseau du correspondant est absent ou invalide
- **THEN** aucune heure locale n'est affichée
- **AND** la salutation retombe sur l'heure du lecteur, sans erreur

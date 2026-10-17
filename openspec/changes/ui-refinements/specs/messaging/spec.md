# Spec Delta — messaging

## ADDED Requirements

### Requirement: [REQ-MSG-07] Métadonnées de la liste des conversations

Le système SHALL afficher, pour chaque conversation, la date du dernier message sous forme
relative et le statut du fil.

#### Scenario: Message récent
- **WHEN** le dernier message date de moins de 24 heures
- **THEN** la date est affichée en relatif (« il y a 5 min », « hier »)
- **AND** l'horodatage absolu reste accessible en infobulle

#### Scenario: Statut du fil
- **WHEN** un fil est fermé (dématch ou blocage)
- **THEN** la liste indique ce statut
- **AND** le compteur de non-lus n'est plus affiché

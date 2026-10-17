# Spec Delta — identity

## ADDED Requirements

### Requirement: [REQ-IDN-04] Double saisie du mot de passe à l'inscription

Le système SHALL demander la confirmation du mot de passe lors de l'inscription et refuser
la création si les deux saisies diffèrent.

#### Scenario: Saisies différentes
- **WHEN** les deux champs diffèrent
- **THEN** l'inscription n'est pas envoyée au serveur
- **AND** un message explicite s'affiche sous les champs

#### Scenario: Saisies identiques
- **WHEN** les deux champs concordent et respectent la longueur minimale
- **THEN** la requête d'inscription est envoyée une seule fois

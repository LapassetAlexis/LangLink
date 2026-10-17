# Spec Delta — safety

## ADDED Requirements

### Requirement: [REQ-SAF-07] Accès permanent au compte et aux réglages

Le système SHALL rendre le profil et les réglages accessibles depuis tout écran authentifié,
en un clic.

#### Scenario: Depuis la découverte
- **WHEN** l'utilisateur est sur l'écran de découverte
- **THEN** un accès au compte est visible
- **AND** il mène à `/settings`

#### Scenario: Déconnexion
- **WHEN** l'utilisateur choisit « Se déconnecter »
- **THEN** le jeton local est effacé et il revient à l'accueil
- **AND** aucune donnée de session ne reste en mémoire

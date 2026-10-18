# Spec Delta — preferences

## ADDED Requirements

### Requirement: [REQ-PRF-01] Préférences d'affichage persistées

Le système SHALL conserver les préférences d'affichage de chaque utilisateur et les appliquer
dès le chargement, sans clignotement.

#### Scenario: Furigana systématique
- **WHEN** l'utilisateur active « afficher le furigana automatiquement »
- **THEN** les messages japonais sont annotés sans action
- **AND** le réglage survit à la déconnexion

#### Scenario: Préférence appliquée avant le premier rendu
- **WHEN** l'application se charge avec des préférences enregistrées
- **THEN** le thème et la taille de texte sont appliqués dès le premier affichage
- **AND** aucun changement visible ne survient après l'appel réseau

### Requirement: [REQ-PRF-02] Respect des préférences système

Le système SHALL respecter `prefers-reduced-motion` et permettre de le surcharger.

#### Scenario: Animations réduites
- **WHEN** l'utilisateur choisit « réduire les animations »
- **THEN** les transitions et apparitions sont désactivées
- **AND** le contenu reste intégralement accessible

#### Scenario: Surcharge explicite
- **WHEN** le système exprime « réduire » mais que l'utilisateur choisit « animations normales »
- **THEN** le choix de l'utilisateur prévaut
- **AND** il peut revenir au réglage système

### Requirement: [REQ-PRF-03] Densité et taille de texte

Le système SHALL proposer au moins trois densités et deux tailles de texte, appliquées
globalement.

#### Scenario: Texte agrandi
- **WHEN** l'utilisateur choisit la taille « grande »
- **THEN** la taille de base augmente sur tous les écrans
- **AND** aucun texte ne déborde de son conteneur

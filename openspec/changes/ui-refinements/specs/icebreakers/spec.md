# Spec Delta — icebreakers

## ADDED Requirements

### Requirement: [REQ-ICE-04] Icebreaker dans la langue du correspondant

Le système SHALL afficher chaque question brise-glace dans la langue maternelle du
correspondant, et SHALL offrir une bascule vers la langue maternelle du lecteur.

#### Scenario: Lecteur français, correspondant japonais
- **WHEN** un lecteur français ouvre un fil avec un correspondant japonais
- **THEN** la question s'affiche en japonais
- **AND** une bascule « voir en français » révèle la version française

#### Scenario: Traduction indisponible
- **WHEN** le moteur de traduction ne répond pas
- **THEN** la question reste affichée dans sa langue d'origine
- **AND** un message non bloquant indique que la bascule est indisponible

#### Scenario: Bascule mémorisée
- **WHEN** le lecteur bascule une question en français
- **THEN** le choix s'applique à la session sans nouvel appel réseau

### Requirement: [REQ-ICE-05] Salutation proposée au premier message du jour

Le système SHALL proposer une salutation dans la langue du correspondant lorsque aucun
message n'a encore été échangé ce jour-là, sans l'envoyer automatiquement.

#### Scenario: Aucun message aujourd'hui
- **WHEN** le lecteur ouvre un fil où le dernier message date d'hier ou est absent
- **THEN** une salutation adaptée à l'heure (matin/soir) est proposée dans la langue du
  correspondant
- **AND** un bouton permet de l'insérer dans la zone de saisie
- **AND** rien n'est envoyé sans action du lecteur

#### Scenario: Conversation déjà entamée aujourd'hui
- **WHEN** au moins un message a été échangé dans la journée
- **THEN** aucune salutation n'est proposée

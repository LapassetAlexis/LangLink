# Spec Delta — safety

## Purpose

Securite et moderation : blocage bilateral immediat, signalement conservant un instantane du contenu, revue administrateur, suppression de compte anonymisante.

## ADDED Requirements

### Requirement: [REQ-SAF-01] Effet immédiat du blocage
Le système SHALL appliquer le blocage sans délai au feed, au fil et à l'envoi.

#### Scenario: Blocage pendant une conversation
- **WHEN** A bloque B alors qu'ils ont un match actif
- **THEN** le match passe à `blocked`
- **AND** B ne peut plus écrire (`403 safety.blocked`)
- **AND** B ne voit plus le profil de A dans son feed


### Requirement: [REQ-SAF-02] Signalement conservant la preuve
Le système SHALL enregistrer un instantané du contenu signalé au moment du signalement.

#### Scenario: Signalement d'un message
- **WHEN** B signale un message de A avec la catégorie `harassment`
- **THEN** un `report` est créé avec `content_snapshot` = corps du message à cet instant
- **AND** le message reste visible pour les membres du fil

---


### Requirement: [REQ-SAF-03] Protection contre l'énumération de comptes
Le système SHALL renvoyer une réponse et un délai comparables pour un email inconnu et un
mot de passe erroné.

#### Scenario: Login avec email inconnu
- **WHEN** un attaquant teste 50 emails
- **THEN** toutes les réponses sont `401 auth.invalid_credentials`
- **AND** aucun en-tête ni code ne distingue un compte existant


### Requirement: [REQ-SAF-04] Suppression de compte effective
Le système SHALL anonymiser le compte et purger les médias, tout en conservant les
messages nécessaires à l'intégrité des conversations restantes.

#### Scenario: Suppression demandée
- **WHEN** l'utilisateur confirme la suppression avec son mot de passe
- **THEN** `status = deleted`, email remplacé par un hash non réversible
- **AND** les photos sont supprimées du stockage sous 24 h
- **AND** les messages affichent « Compte supprimé »

---

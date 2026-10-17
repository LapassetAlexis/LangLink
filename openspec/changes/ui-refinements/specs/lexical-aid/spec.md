# Spec Delta — lexical-aid

## Purpose

Permettre à l'apprenant de demander le sens d'un mot isolé dans un message reçu, sans
traduire toute la phrase, avec prise en charge des écritures non latines.

## ADDED Requirements

### Requirement: [REQ-LEX-01] Aide au mot isolé

Le système SHALL permettre de sélectionner un mot d'un message reçu et d'obtenir son ou ses
sens dans la langue maternelle du lecteur.

#### Scenario: Mot latin
- **WHEN** le lecteur active le mode « mot à mot » et clique sur « marché »
- **THEN** une aide s'affiche avec au moins un sens en français
- **AND** le message d'origine reste inchangé

#### Scenario: Mot japonais
- **WHEN** le lecteur clique sur « 学生 » dans un message japonais
- **THEN** l'aide affiche la lecture kana et le romaji, en plus du sens
- **AND** les offsets renvoyés restent exprimés en points de code

### Requirement: [REQ-LEX-02] Plusieurs sens, pas une seule traduction

Le système SHALL présenter plusieurs sens possibles lorsqu'ils existent, avec leur catégorie
grammaticale, et SHALL ne jamais présenter une traduction unique comme si elle était la
seule lecture.

#### Scenario: Mot polysémique
- **WHEN** le mot consulté admet plusieurs sens
- **THEN** au moins deux sens sont listés
- **AND** chaque sens est accompagné de sa nature grammaticale

#### Scenario: Source lexicale indisponible
- **WHEN** le dictionnaire ne répond pas
- **THEN** l'interface propose le sens unique du moteur de traduction en le signalant
  comme tel (« traduction automatique, sens unique »)
- **AND** aucune erreur bloquante n'est affichée

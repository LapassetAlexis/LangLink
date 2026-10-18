# Spec Delta — platform

## MODIFIED Requirements

### Requirement: [REQ-PLT-02] Aucune IA comme interlocuteur

Tout message échangé dans une conversation SHALL être écrit par un humain. Aucun système
SHALL générer, compléter ou envoyer un message à la place d'un utilisateur, ni se présenter
comme un correspondant.

#### Scenario: Message reçu
- **WHEN** un utilisateur lit un message dans un fil
- **THEN** ce message a été rédigé et envoyé par son correspondant humain
- **AND** aucune réponse automatique n'est produite en son nom

#### Scenario: Aide à la rédaction
- **WHEN** une aide (traduction, dictionnaire, correction) est sollicitée
- **THEN** elle s'affiche comme une **aide**, jamais comme un message du fil
- **AND** son origine est indiquée (dictionnaire, moteur de traduction, annotation locale)
- **AND** l'utilisateur reste l'auteur de ce qu'il envoie

#### Scenario: Tentative d'automatisation du dialogue
- **WHEN** du code tente de produire un message de conversation sans action humaine
- **THEN** le garde-fou de compilation le signale
- **AND** l'intégration est refusée en revue

## ADDED Requirements

### Requirement: [REQ-PLT-08] Transparence de l'origine des aides

Le système SHALL indiquer, pour chaque texte non écrit par un humain, sa provenance.

#### Scenario: Aide affichée
- **WHEN** une traduction ou une définition est présentée
- **THEN** la source est mentionnée à proximité du texte
- **AND** une aide issue d'un moteur automatique est signalée comme telle

#### Scenario: Aide ambiguë
- **WHEN** la provenance d'un texte ne peut pas être établie
- **THEN** il n'est pas affiché dans le fil de conversation

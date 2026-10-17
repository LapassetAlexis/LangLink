# Spec Delta — messaging

## Purpose

Messagerie asynchrone 1-a-1 : envoi idempotent, pagination, statut de lecture, edition et suppression douce, fonctionnement sans connexion persistante.

## ADDED Requirements

### Requirement: [REQ-MSG-01] Accès restreint au fil
Le système SHALL refuser tout accès à un fil par un non-membre.

#### Scenario: Intrusion
- **WHEN** C appelle `GET /matches/{id}/messages` d'un match A–B
- **THEN** l'API renvoie `404 match.not_found` (pas `403`, pour ne pas révéler l'existence)


### Requirement: [REQ-MSG-02] Envoi de message
Le système SHALL valider la longueur (1–4000 après trim), l'appartenance au match actif et
le non-blocage, puis mettre à jour `matches.last_message_at`.

#### Scenario: Message valide
- **WHEN** A envoie `"Bonjour !"` dans un match actif
- **THEN** le message est créé avec `body_lang` = langue visée de A
- **AND** `last_message_at` du match est mis à jour
- **AND** B voit `unread_count` incrémenté au prochain polling

#### Scenario: Message vide ou trop long
- **WHEN** le corps ne contient que des espaces, ou dépasse 4000 caractères
- **THEN** l'API renvoie `422` et n'écrit rien

#### Scenario: Match fermé
- **WHEN** A tente d'écrire après un dématch ou un blocage
- **THEN** l'API renvoie `409 match.closed`


### Requirement: [REQ-MSG-03] Statut de lecture
Le système SHALL enregistrer la lecture par message et exposer un compteur de non-lus.

#### Scenario: Marquage en lot
- **WHEN** B ouvre le fil et appelle `POST /read` avec `last_message_id`
- **THEN** toutes les lignes non lues jusqu'à cet identifiant sont marquées
- **AND** le compteur de B retombe à 0

#### Scenario: L'auteur ne compte pas
- **WHEN** A envoie un message
- **THEN** aucun `message_reads` n'est créé pour A
- **AND** ce message n'entre jamais dans le compteur de non-lus de A


### Requirement: [REQ-MSG-04] Marquage de lecture naturel
Le système SHALL marquer un message comme lu quand le fil est ouvert et que le message est
visible depuis au moins 1 seconde.

#### Scenario: Fil ouvert
- **WHEN** B ouvre un fil contenant 3 messages non lus
- **THEN** `POST /read` est appelé une seule fois avec le dernier identifiant
- **AND** l'expéditeur voit « Vu » au rafraîchissement suivant


### Requirement: [REQ-MSG-05] Asynchronisme assumé
Le système SHALL fonctionner sans connexion persistante et sans dépendance à un serveur
temps réel.

#### Scenario: Perte de connexion pendant la rédaction
- **WHEN** le réseau tombe au moment de l'envoi
- **THEN** le message reste en file locale et l'UI affiche l'état « non envoyé »
- **AND** un retry manuel ou automatique réutilise la même `Idempotency-Key`
- **AND** aucun doublon n'est créé


### Requirement: [REQ-MSG-06] Pas de contenu généré
Le système SHALL ne jamais insérer de texte produit par un modèle génératif dans un fil de
discussion.

#### Scenario: Audit du produit
- **WHEN** on inspecte les dépendances et le code du chemin messagerie
- **THEN** aucun client LLM n'est appelé
- **AND** les seuls textes pré-écrits sont les icebreakers du catalogue et les libellés UI

---

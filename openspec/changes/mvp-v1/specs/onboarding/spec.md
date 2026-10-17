# Spec Delta — onboarding

## Purpose

Enrolement progressif en trois etapes : declaration de la paire linguistique et du niveau CECRL, selection de centres d'interet dans un catalogue, puis profil optionnel avec photo.

## ADDED Requirements

### Requirement: [REQ-ONB-01] Onboarding actionnable en moins de 3 minutes
Le système SHALL permettre de terminer l'onboarding obligatoire (étapes 1 et 2) en
moins de 3 minutes et en moins de 8 interactions pointantes.

#### Scenario: Inscription jusqu'au discovery
- **WHEN** un visiteur s'inscrit, choisit `fr` → `ja` (A2) et 3 intérêts
- **THEN** il est redirigé vers le discovery sans étape supplémentaire
- **AND** son profil est découvrable immédiatement

#### Scenario: Reprise après interruption
- **WHEN** un utilisateur ferme le navigateur à l'étape 2
- **AND** se reconnecte plus tard
- **THEN** le wizard reprend à l'étape 2 avec les sélections déjà enregistrées

---


### Requirement: [REQ-ONB-02] Validation de l'étape 1
Le système SHALL refuser une paire linguistique où la langue native égale la langue visée,
et exiger un niveau CECRL valide.

#### Scenario: Langues identiques
- **WHEN** l'utilisateur envoie `{native_language:"fr", target_language:"fr"}`
- **THEN** l'API renvoie `422` avec `errors[{field:"target_language", code:"same_as_native"}]`

#### Scenario: Langue non supportée
- **WHEN** `target_language` n'appartient pas au référentiel des langues actives
- **THEN** l'API renvoie `422 language.unsupported`


### Requirement: [REQ-ONB-03] Seuil d'intérêts
Le système SHALL exiger au moins 3 centres d'intérêt et en accepter au plus 12.

#### Scenario: Deux intérêts seulement
- **WHEN** l'utilisateur soumet 2 intérêts
- **THEN** l'API renvoie `422` avec `errors[{field:"interest_ids", code:"min_3"}]`
- **AND** l'étape reste non validée

#### Scenario: Intérêt inconnu ou inactif
- **WHEN** la liste contient un identifiant absent du référentiel actif
- **THEN** l'API renvoie `422` et n'enregistre aucune sélection (transaction atomique)


### Requirement: [REQ-ONB-04] Finalisation de l'onboarding
Le système SHALL rendre le profil découvrable uniquement si les étapes 1 et 2 sont
complètes et que le profil n'est ni suspendu ni bloqué.

#### Scenario: Finalisation incomplète
- **WHEN** `POST /onboarding/complete` est appelé sans intérêts
- **THEN** l'API renvoie `409 onboarding.incomplete` avec la liste des prérequis manquants
- **AND** `discoverable` reste `false`


### Requirement: [REQ-ONB-05] Barre de progression fiable
Le système SHALL afficher une progression à 3 segments reflétant l'étape courante, et
permettre le retour arrière sans perte de données.

#### Scenario: Retour à l'étape précédente
- **WHEN** l'utilisateur revient de l'étape 3 à l'étape 2
- **THEN** ses intérêts restent cochés
- **AND** la barre affiche 2/3


### Requirement: [REQ-ONB-06] Étape 3 sautable
Le système SHALL proposer une action « Plus tard » explicite à l'étape 3.

#### Scenario: Saut de l'étape 3
- **WHEN** l'utilisateur clique « Plus tard »
- **THEN** `onboarding_done_at` est renseigné et le discovery s'ouvre
- **AND** une invitation non bloquante à compléter le profil apparaît sur le feed


### Requirement: [REQ-ONB-07] Robustesse de la photo
Le système SHALL accepter JPEG/PNG/WebP jusqu'à 5 Mo, recompresser en 512×512 WebP et
supprimer les métadonnées EXIF.

#### Scenario: Fichier trop volumineux
- **WHEN** l'utilisateur envoie une image de 8 Mo
- **THEN** l'API renvoie `413` avec un message explicite
- **AND** l'UI conserve les autres champs du formulaire

#### Scenario: Format non supporté
- **WHEN** le fichier est un GIF ou un PDF
- **THEN** l'API renvoie `415` sans écrire de fichier

---


### Requirement: [REQ-ONB-08] Intérêts stables et traduisibles
Le système SHALL servir le catalogue depuis la base, avec libellés FR/EN et emoji, sans
référence en dur dans le code client.

#### Scenario: Chargement du catalogue
- **WHEN** le client appelle `GET /interests`
- **THEN** la réponse est groupée par catégorie, triée par `sort_order`
- **AND** chaque entrée contient `id, slug, label, emoji`

#### Scenario: Retrait d'un intérêt
- **WHEN** un intérêt est passé `active = false`
- **THEN** il disparaît de la grille d'onboarding
- **AND** les profils qui l'avaient conservé ne sont pas modifiés
- **AND** les icebreakers déjà générés restent lisibles

---
